import re
import json
from sqlalchemy import text


class SQLGenerationService:

    def __init__(self, ai_service):
        self.ai_service = ai_service

    # ----------------------------
    # Generate SQL using LLM
    # ----------------------------
    def generate_sql(self, schema_context: str, question: str):

        system_prompt = """
You are a senior PostgreSQL database architect.

Generate ONLY a valid SELECT SQL query.
Do NOT generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.

Return response in this strict JSON format:

{
  "sql": "...",
  "explanation": "..."
}
"""

        user_prompt = f"""
Database Schema:
{schema_context}

User Question:
{question}
"""

        response = self.ai_service.generate(system_prompt, user_prompt)

        clean_response = response.strip()

        # Remove markdown fences
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            clean_response = clean_response.replace("json", "").strip()

        try:
            parsed = json.loads(clean_response)
        except Exception:
            return {
                "error": "Failed to parse SQL response",
                "raw_response": response
            }

        return parsed

    # ----------------------------
    # Validate SQL Safety
    # ----------------------------
    def validate_sql(self, sql: str):

        sql = sql.strip().lower()

        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]

        for word in forbidden:
            if word in sql:
                return False

        if not sql.startswith("select"):
            return False

        return True

    # ----------------------------
    # Safe Execution
    # ----------------------------
    def execute_safe_query(self, engine, sql: str):

        if not self.validate_sql(sql):
            return {
                "error": "Unsafe or invalid SQL detected."
            }

        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                columns = result.keys()

            return {
                "columns": list(columns),
                "rows": [list(row) for row in rows]
            }

        except Exception as e:
            return {
                "error": str(e)
            }


# ----------------------------
# Build Schema Context Helper
# ----------------------------
def build_schema_context(session):

    from app.domain.models import Table, Relationship

    context = ""

    tables = session.query(Table).all()

    for table in tables:
        context += f"\nTable: {table.name}\nColumns:\n"

        for column in table.columns:
            context += f"- {column.name} ({column.data_type})\n"

    context += "\nRelationships:\n"

    relationships = session.query(Relationship).all()

    for rel in relationships:
        context += (
            f"{rel.source_table}.{rel.source_column} "
            f"→ {rel.target_table}.{rel.target_column}\n"
        )

    return context
