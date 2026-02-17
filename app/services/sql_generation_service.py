import json
import re
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

Always include a LIMIT clause unless explicitly counting.

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

        if not response:
            return {
                "error": "Empty response from LLM"
            }

        clean_response = response.strip()

        # Remove markdown code fences if present
        if clean_response.startswith("```"):
            clean_response = re.sub(r"```.*?\n", "", clean_response)
            clean_response = clean_response.replace("```", "").strip()

        try:
            parsed = json.loads(clean_response)
        except Exception:
            return {
                "error": "Failed to parse SQL response",
                "raw_response": response
            }

        if "sql" not in parsed or "explanation" not in parsed:
            return {
                "error": "Invalid SQL response structure",
                "raw_response": response
            }

        return parsed

    # ----------------------------
    # Validate SQL Safety
    # ----------------------------
    def validate_sql(self, sql: str):

        if not sql:
            return False

        sql_clean = sql.strip().lower()

        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]

        for word in forbidden:
            if word in sql_clean:
                return False

        if not sql_clean.startswith("select"):
            return False

        return True

    # ----------------------------
    # Auto Add LIMIT Protection
    # ----------------------------
    def enforce_limit(self, sql: str, default_limit: int = 50):

        sql_lower = sql.lower()

        # Do not enforce limit for COUNT queries
        if "count(" in sql_lower:
            return sql

        if "limit" not in sql_lower:
            sql = sql.rstrip(";")
            sql += f" LIMIT {default_limit};"

        return sql

    # ----------------------------
    # Safe Execution
    # ----------------------------
    def execute_safe_query(self, engine, sql: str):

        if not self.validate_sql(sql):
            return {
                "error": "Unsafe or invalid SQL detected."
            }

        # 🔐 Enforce LIMIT automatically
        sql = self.enforce_limit(sql)

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
