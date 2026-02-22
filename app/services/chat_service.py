from app.services.embedding_service import EmbeddingService
from app.services.vector_search_service import VectorSearchService
from app.domain.models import Documentation, ChatSession, ChatMessage, ColumnModel


class ChatService:

    def __init__(self, engine, session, ai_service):
        self.engine = engine
        self.embedding_service = EmbeddingService(session)
        self.vector_search = VectorSearchService(engine)
        self.session = session
        self.ai_service = ai_service

    # ==================================================
    # INTENT DETECTION
    # ==================================================
    def _detect_intent(self, question: str) -> str:
        """
        Detect whether the question should be handled by SQL or RAG mode.
        Returns: 'sql' or 'rag'
        """
        q_lower = question.lower()

        # RAG keywords - documentation, explanation, description questions
        rag_keywords = [
            "documentation", "document", "describe", "description", "explain",
            "what is", "what are", "tell me about", "meaning of", "purpose of",
            "why", "how does", "understand", "definition", "overview",
            "summary", "business", "data quality", "usage", "recommended",
            "help me understand", "can you explain", "what does"
        ]

        # Check for RAG intent first (documentation/explanation requests)
        for keyword in rag_keywords:
            if keyword in q_lower:
                # But if they also ask for specific data, use SQL
                sql_action_words = ["calculate", "compute", "sum", "count", "average", 
                                   "how many", "how much", "total", "revenue"]
                if any(action in q_lower for action in sql_action_words):
                    return "sql"
                return "rag"

        # SQL keywords - data retrieval, calculations, aggregations
        sql_keywords = [
            "generate sql", "write sql", "run query", "execute",
            "show me", "list all", "find all", "get all",
            "count", "average", "avg", "sum", "total", 
            "how many", "how much", "calculate", "compute",
            "revenue", "sales", "trend", "monthly", "yearly", "daily",
            "top", "bottom", "highest", "lowest", "maximum", "minimum",
            "group by", "per", "by state", "by category", "by month", "by year",
            "between", "greater than", "less than", "more than",
            "delivery time", "payment value", "order status",
            "select", "from olist", "query"
        ]

        # Check for SQL intent
        for keyword in sql_keywords:
            if keyword in q_lower:
                return "sql"

        # Default to RAG for general questions
        return "rag"

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

        # Detect intent
        intent = self._detect_intent(question)

        if intent == "sql":
            return self._handle_sql_mode(question, session_id)

        return self._rag_reasoning(question, session_id)

    # ==================================================
    # LIST SCHEMA TABLES HELPER
    # ==================================================
    def _list_schema_tables(self, question: str, session_id: int, schema_name: str):
        from sqlalchemy import text

        # Query all tables in the schema
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {"schema": schema_name})
            tables = [row[0] for row in result.fetchall()]

        # Build documentation context for each table
        context_text = f"**Tables in the {schema_name} schema:**\n\n"

        for table_name in tables:
            # Search for documentation by table name in description
            full_table_name = f"{schema_name}.{table_name}"
            doc = (
                self.session.query(Documentation)
                .filter(Documentation.entity_type == "table")
                .filter(Documentation.description.ilike(f"%{full_table_name}%"))
                .first()
            )

            context_text += f"### {full_table_name}\n"
            if doc:
                context_text += f"{doc.description}\n\n"
            else:
                context_text += "(No documentation available)\n\n"

        history = self._get_recent_history(session_id)

        system_prompt = """
You are an enterprise data architect AI assistant.

List all tables in the requested schema with their documentation.
Format the response clearly with table names and their summaries.
Extract and present the key information: summary, business_purpose, and columns if available.
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
            return {
                "session_id": session_id,
                "mode": "sql",
                "answer": sql_response["error"]
            }

        sql_query = sql_response.get("sql")
        explanation = sql_response.get("explanation")

        execution = sql_service.execute_safe_query(self.engine, sql_query)

        if "error" in execution:
            return {
                "session_id": session_id,
                "mode": "sql",
                "answer": execution["error"]
            }

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

        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=summary
        )
        self.session.add(assistant_message)
        self.session.commit()

        # ✅ FULL SQL RESPONSE
        return {
            "session_id": session_id,
            "mode": "sql",
            "answer": summary,
            "sql": sql_query,
            "explanation": explanation,
            "result": execution
        }

    # ==================================================
    # RAG MODE
    # ==================================================
    def _rag_reasoning(self, question: str, session_id: int):
        from sqlalchemy import text

        q_lower = question.lower()

        # Special handling for "list tables in schema" queries
        if any(keyword in q_lower for keyword in ["tables in olist", "olist tables", "olist schema", "tables of olist", "tell me tables"]):
            return self._list_schema_tables(question, session_id, "olist")

        query_vector = self.embedding_service.generate_embedding(question)
        results = self.vector_search.search(query_vector)

        context_text = ""
        seen = set()

        for entity_type, entity_id, distance in results:

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
