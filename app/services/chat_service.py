from app.services.embedding_service import EmbeddingService
from app.services.vector_search_service import VectorSearchService
from app.domain.models import Documentation, ChatSession, ChatMessage


import json


class ChatService:

    def __init__(self, engine, session, ai_service):
        self.engine = engine
        self.embedding_service = EmbeddingService(session)
        self.vector_search = VectorSearchService(engine)
        self.session = session
        self.ai_service = ai_service

    # ==================================================
    # MAIN ENTRY
    # ==================================================
    def ask(self, question: str, session_id: int = None):

        # Create session if not provided
        if not session_id:
            new_session = ChatSession()
            self.session.add(new_session)
            self.session.commit()
            session_id = new_session.id

        # Store user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=question
        )
        self.session.add(user_message)
        self.session.commit()

        sql_keywords = ["generate sql", "write sql", "show", "list", "find", "count"]

        if any(keyword in question.lower() for keyword in sql_keywords):
            return self._handle_sql_mode(question, session_id)

        return self._rag_reasoning(question, session_id)

    # ==================================================
    # MEMORY HELPER
    # ==================================================
    def _get_recent_history(self, session_id, limit=5):

        messages = (
            self.session.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

        messages = list(reversed(messages))

        history_text = ""

        for msg in messages:
            history_text += f"{msg.role.upper()}: {msg.content}\n"

        return history_text

    # ==================================================
    # SQL MODE
    # ==================================================
    def _handle_sql_mode(self, question: str, session_id: int):

        from app.services.sql_generation_service import (
            SQLGenerationService,
            build_schema_context
        )

        sql_service = SQLGenerationService(self.ai_service)

        schema_context = build_schema_context(self.session)

        sql_response = sql_service.generate_sql(schema_context, question)

        if "error" in sql_response:
            return sql_response

        sql_query = sql_response["sql"]
        explanation = sql_response["explanation"]

        execution = sql_service.execute_safe_query(self.engine, sql_query)

        if "error" in execution:
            return execution

        history = self._get_recent_history(session_id)

        system_prompt = """
You are an enterprise database AI assistant.

Summarize the SQL query result clearly and concisely.
Explain what the data represents.
"""

        user_prompt = f"""
Conversation History:
{history}

SQL Query:
{sql_query}

Explanation:
{explanation}

Query Result:
Columns: {execution['columns']}
Rows: {execution['rows']}
"""

        summary = self.ai_service.generate(system_prompt, user_prompt)

        # Store assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=summary
        )
        self.session.add(assistant_message)
        self.session.commit()

        return {
            "session_id": session_id,
            "mode": "sql",
            "sql": sql_query,
            "explanation": explanation,
            "result": execution,
            "summary": summary
        }

    # ==================================================
    # RAG MODE
    # ==================================================
    def _rag_reasoning(self, question: str, session_id: int):

        query_vector = self.embedding_service.generate_embedding(question)
        results = self.vector_search.search(query_vector)

        context_text = ""
        seen = set()

        from app.domain.models import ColumnModel

        for entity_type, entity_id, distance in results:

            # Optional relaxed threshold
            if distance > 1.2:
                continue

            if (entity_type, entity_id) in seen:
                continue

            seen.add((entity_type, entity_id))

            doc = (
                self.session.query(Documentation)
                .filter_by(entity_type=entity_type, entity_id=entity_id)
                .first()
            )

            if not doc:
                continue

            context_text += f"""
--- ENTITY ---
Type: {entity_type}
ID: {entity_id}
Similarity Distance: {distance}

Documentation:
{doc.description}
"""

            if entity_type == "table":

                columns = (
                    self.session.query(ColumnModel)
                    .filter_by(table_id=entity_id)
                    .all()
                )

                context_text += "\n--- PROFILING ---\n"

                for column in columns:
                    profile = column.profile

                    if profile:
                        context_text += (
                            f"\nColumn: {column.name}\n"
                            f"- Null %: {profile.null_percentage}\n"
                            f"- Distinct Count: {profile.distinct_count}\n"
                            f"- Min: {profile.min_value}\n"
                            f"- Max: {profile.max_value}\n"
                            f"- Mean: {profile.mean}\n"
                        )

                        if profile.null_percentage == 100:
                            context_text += (
                                f"⚠ Column {column.name} is 100% NULL.\n"
                            )

        history = self._get_recent_history(session_id)

        system_prompt = """
You are an enterprise data architect AI assistant.

Use documentation, profiling metrics, and conversation history
to answer questions.

If profiling shows anomalies (e.g., 100% null columns),
explicitly highlight them as data quality issues.

Be precise, analytical, and professional.
"""

        user_prompt = f"""
Conversation History:
{history}

Context:
{context_text}

Question:
{question}
"""

        response = self.ai_service.generate(system_prompt, user_prompt)

        # Store assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response
        )
        self.session.add(assistant_message)
        self.session.commit()

        return {
            "session_id": session_id,
            "mode": "rag",
            "answer": response
        }
