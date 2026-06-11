import json
import re
import logging
from sqlalchemy import text, inspect

logger = logging.getLogger(__name__)


class SQLGenerationService:

    def __init__(self, ai_service):
        self.ai_service = ai_service

    # ------------------------------------------------
    # Extract JSON from LLM response
    # ------------------------------------------------
    def _extract_json(self, response: str) -> dict:
        """
        Robust JSON extraction from LLM response.
        Handles markdown fences, extra text, and common issues.
        """
        if not response:
            return None

        clean = response.strip()

        # Remove markdown code fences (```json or ```)
        clean = re.sub(r"```(?:json)?\s*", "", clean)
        clean = clean.replace("```", "").strip()

        # Try direct JSON parse
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in response
        json_match = re.search(r'\{[\s\S]*\}', clean)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try to extract SQL manually if JSON fails
        sql_match = re.search(r'(SELECT\s+[\s\S]+?;)', clean, re.IGNORECASE)
        if sql_match:
            return {
                "sql": sql_match.group(1).strip(),
                "explanation": "SQL extracted from response"
            }

        return None

    # ------------------------------------------------
    # Generate SQL using LLM
    # ------------------------------------------------
    def generate_sql(self, question: str, schema_context: str, dialect: str = "postgresql"):

        system_prompt = f"""
You are a senior database architect.

CRITICAL RULES:
1. Generate SQL for {dialect} dialect.
   For snowflake: use double-quote identifiers and ILIKE for case-insensitive.
   For mysql: use backtick quoting and LIMIT syntax.
   For postgresql: use standard ANSI SQL with pgcrypto extensions available.
2. You MUST use SCHEMA-QUALIFIED table names (e.g., schema_name.table_name)
3. You MUST ONLY use columns listed in the schema below — check which table has each column!
4. You MUST NOT invent or assume column names that are not listed below.
   STRICTLY FORBIDDEN: Do NOT invent columns like 'quantity', 'amount', 'total', etc. if they are not listed.
5. When a column exists in one table but the question implies another, you MUST use a JOIN
6. Carefully read the JOIN PATTERNS and IMPORTANT NOTES sections — they tell you exactly how tables connect
7. Before writing SQL, mentally verify EVERY column you use actually appears in the schema listing for that table

=== DATABASE SCHEMA (USE ONLY THESE TABLES AND COLUMNS) ===

{schema_context}

Return ONLY valid SELECT SQL with schema-qualified table names.

IMPORTANT: Return ONLY a valid JSON object:
{{"sql": "SELECT ... FROM schema.table_name ...", "explanation": "..."}}
"""

        user_prompt = f"""
User Question:
{question}

REMEMBER:
- ONLY use columns that exist in the schema above — do NOT invent columns
- Use JOINs when you need columns from multiple tables
- Check the IMPORTANT NOTES section for revenue/monetary column hints and join keys
- If date columns are stored as text, cast them with ::timestamp
- Double-check every column name against the schema before using it
Respond with JSON only:
"""

        response = self.ai_service.generate(system_prompt, user_prompt, json_mode=True)

        if not response:
            return {"error": "Empty response from LLM"}

        # Check for AI error
        if response.startswith("AI Error:"):
            logger.error(f"AI Service Error: {response}")
            return {"error": response}

        logger.info(f"LLM Raw Response: {response[:500]}")  # Log first 500 chars

        parsed = self._extract_json(response)

        if not parsed:
            logger.error(f"Failed to parse JSON from: {response}")
            return {
                "error": "Failed to parse SQL response",
                "raw_response": response
            }

        if "sql" not in parsed or "explanation" not in parsed:
            logger.error(f"Invalid structure: {parsed}")
            return {
                "error": "Invalid SQL response structure",
                "raw_response": response
            }

        return parsed

    # ------------------------------------------------
    # Basic SQL Safety Validation
    # ------------------------------------------------
    def validate_sql(self, sql: str) -> tuple[bool, str]:

        if not sql:
            return False, "Empty SQL"

        sql_clean = sql.strip().lower()

        import re
        forbidden = [r"\binsert\b", r"\bupdate\b", r"\bdelete\b", r"\bdrop\b", r"\balter\b", r"\btruncate\b", r"\bcreate\b", r"\bgrant\b", r"\brevoke\b", r"\breplace\b"]

        for pattern in forbidden:
            if re.search(pattern, sql_clean):
                clean_pattern = pattern.replace(r'\b', '')
                return False, f"Destructive SQL command blocked. Found forbidden pattern: {clean_pattern}"

        if not (sql_clean.startswith("select") or sql_clean.startswith("with")):
            return False, "Query must start with SELECT or WITH"

        return True, ""

    # ------------------------------------------------
    # Dynamic Column Validation (Prevents Hallucination)
    # ------------------------------------------------
    def validate_sql_columns(self, engine, sql: str):
        """
        Validate that referenced tables exist in the database.
        Let PostgreSQL handle column validation for better error messages.
        """

        if not sql:
            return False, "Empty SQL"

        inspector = inspect(engine)
        sql_lower = sql.lower()

        # ----------------------------
        # Remove all contents inside parentheses to avoid false positives
        # (e.g., EXTRACT(MONTH FROM column) or nested functions)
        # ----------------------------
        sql_cleaned = sql_lower
        while '(' in sql_cleaned:
            new_sql = re.sub(r'\([^()]*\)', '', sql_cleaned)
            if new_sql == sql_cleaned:
                break
            sql_cleaned = new_sql
        
        # ----------------------------
        # Extract tables from FROM / JOIN (handles schema.table format)
        # Only match FROM/JOIN followed by schema.table or table pattern
        # Exclude common column patterns
        # ----------------------------
        table_pattern = r'(?:from|join)\s+([a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*)'
        matches = re.findall(table_pattern, sql_cleaned)
        
        # Also try to find non-schema-qualified tables (less common but valid)
        if not matches:
            table_pattern_simple = r'(?:from|join)\s+([a-zA-Z][a-zA-Z0-9_]*)'
            matches = re.findall(table_pattern_simple, sql_cleaned)
            # Filter out common SQL keywords that might be caught
            sql_keywords = {'select', 'where', 'group', 'order', 'having', 'limit', 
                           'offset', 'union', 'intersect', 'except', 'as', 'on', 
                           'and', 'or', 'not', 'in', 'exists', 'between', 'like',
                           'null', 'true', 'false', 'case', 'when', 'then', 'else', 'end'}
            matches = [m for m in matches if m not in sql_keywords]

        if not matches:
            logger.warning("No tables detected in SQL, skipping validation")
            return True, None

        used_tables = matches
        logger.info(f"Detected tables in SQL: {used_tables}")

        # ----------------------------
        # Validate tables exist
        # ----------------------------
        for table in used_tables:
            if "." in table:
                schema, table_name = table.split(".", 1)
            else:
                schema = None
                table_name = table

            try:
                # Just check if table exists
                inspector.get_columns(table_name, schema=schema)
                logger.info(f"Table {table} validated")
            except Exception as e:
                logger.error(f"Table lookup failed for '{table}': {e}")
                return False, f"Table '{table}' does not exist. Use schema-qualified names like 'olist.orders'."

        # Let PostgreSQL validate columns - it gives better error messages
        return True, None

    # ------------------------------------------------
    # Auto Add LIMIT Protection
    # ------------------------------------------------
    def enforce_limit(self, sql: str, default_limit: int = 50):

        sql_lower = sql.lower()

        # Skip limit for COUNT queries
        if "count(" in sql_lower:
            return sql

        if "limit" not in sql_lower:
            sql = sql.rstrip(";")
            sql += f" LIMIT {default_limit};"

        return sql

    # ------------------------------------------------
    # Safe Execution
    # ------------------------------------------------
    def execute_safe_query(self, engine_or_connector, sql: str, user=None, session=None):

        # Step 0: Enforce Guardrails
        if user and session:
            from app.domain.models import ColumnPermission
            role = getattr(user, 'role', 'analyst') or 'analyst'
            restricted = session.query(ColumnPermission).filter_by(role=role, allow=False).all()
            sql_lower = sql.lower()
            for r in restricted:
                if r.column_name.lower() in sql_lower:
                    return {"error": f"Guardrail blocked query: You do not have permission to access restricted column '{r.column_name}'."}

        # Step 1: Basic validation
        is_safe, err_msg = self.validate_sql(sql)
        if not is_safe:
            return {"error": f"Unsafe or invalid SQL detected: {err_msg}"}

        # Step 2: Enforce LIMIT
        sql = self.enforce_limit(sql)

        try:
            from app.connectors.base import BaseConnector
            if isinstance(engine_or_connector, BaseConnector):
                result = engine_or_connector.execute_query(sql)
                if result.error:
                    return {"error": result.error}
                return {
                    "columns": result.columns,
                    "rows": result.rows
                }
            else:
                # Fallback to SQLAlchemy Engine (for test DB or old functionality)
                with engine_or_connector.connect() as conn:
                    result = conn.execute(text(sql))
                    rows = result.fetchall()
                    columns = result.keys()

                return {
                    "columns": list(columns),
                    "rows": [list(row) for row in rows]
                }

        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------
    # Confidence Scoring
    # ------------------------------------------------
    def compute_confidence(self, sql: str, session, question: str) -> dict:
        """
        Compute a confidence score for generated SQL based on:
        1. Schema coverage — do referenced tables/columns exist?
        2. FK-backed joins — are JOINs supported by foreign keys?
        3. Question ambiguity — is the question clear?
        Returns: { score: 0-100, uncertain_columns, uncertain_joins, warning }
        """
        from app.domain.models import Table, ColumnModel, Relationship

        score = 100
        uncertain_columns = []
        uncertain_joins = []
        warning = None

        if not sql:
            return {"score": 0, "uncertain_columns": [], "uncertain_joins": [], "warning": "No SQL generated"}

        sql_lower = sql.lower()

        # --- 1. Check table/column coverage ---
        # Strip parentheses content to avoid matching SQL functions (e.g. EXTRACT(MONTH FROM ...))
        sql_cleaned = sql_lower
        while '(' in sql_cleaned:
            new_sql = re.sub(r'\([^()]*\)', '', sql_cleaned)
            if new_sql == sql_cleaned:
                break
            sql_cleaned = new_sql

        # Extract table references
        table_pattern = r'(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)'
        table_matches = re.findall(table_pattern, sql_cleaned)

        # Extract column references (simplified)
        col_pattern = r'(?:select|where|on|group\s+by|order\s+by|having)\s+.*?(?:from|join|where|group|order|having|limit|$)'
        
        all_tables = session.query(Table).all()
        known_table_names = set()
        known_columns = {}
        for t in all_tables:
            schema_name = t.schema.name if t.schema else ""
            full_name = f"{schema_name}.{t.name}".lower()
            known_table_names.add(full_name)
            known_table_names.add(t.name.lower())
            for col in t.columns:
                known_columns.setdefault(full_name, set()).add(col.name.lower())
                known_columns.setdefault(t.name.lower(), set()).add(col.name.lower())

        for tbl in table_matches:
            if tbl.lower() not in known_table_names:
                score -= 15
                warning = f"Table '{tbl}' may not exist in the schema"

        # --- 2. Check FK-backed joins ---
        join_pattern = r'join\s+(\S+)\s+\w+\s+on\s+(\S+)\s*=\s*(\S+)'
        join_matches = re.findall(join_pattern, sql_lower)
        
        all_rels = session.query(Relationship).all()
        fk_pairs = set()
        for rel in all_rels:
            fk_pairs.add((rel.source_table.lower(), rel.source_column.lower(),
                         rel.target_table.lower(), rel.target_column.lower()))
            fk_pairs.add((rel.target_table.lower(), rel.target_column.lower(),
                         rel.source_table.lower(), rel.source_column.lower()))

        for joined_table, left_col, right_col in join_matches:
            # Extract just column names (strip aliases like o.order_id)
            left_parts = left_col.split(".")
            right_parts = right_col.split(".")
            l_col = left_parts[-1]
            r_col = right_parts[-1]
            
            # Check if any FK relationship covers this join
            has_fk = False
            for st, sc, tt, tc in fk_pairs:
                if (sc == l_col and tc == r_col) or (sc == r_col and tc == l_col):
                    has_fk = True
                    break
            if not has_fk:
                score -= 10
                uncertain_joins.append(f"{left_col} = {right_col}")

        # --- 3. Question ambiguity ---
        ambiguous_words = ["maybe", "perhaps", "something like", "sort of", "kind of", "probably", "might"]
        q_lower = question.lower()
        for word in ambiguous_words:
            if word in q_lower:
                score -= 5
                if not warning:
                    warning = "The question contains ambiguous language"
                break

        # Clamp score
        score = max(0, min(100, score))

        return {
            "score": score,
            "uncertain_columns": uncertain_columns,
            "uncertain_joins": uncertain_joins,
            "warning": warning,
        }


# ------------------------------------------------
# Build Schema Context Helper
# ------------------------------------------------
def build_schema_context(session, connection_id=None):
    """
    Dynamically build a rich schema context for the LLM prompt.
    Produces output equivalent to the old hardcoded Olist schema:
      - Compact table + column listings with data types
      - Auto-detected date-as-text warnings
      - JOIN patterns derived from foreign key relationships
      - Important notes about column locations
    """

    from app.domain.models import Table, Relationship, Documentation, Annotation, Schema

    # ----- 1. Collect tables (filtered by connection if provided) -----
    table_query = session.query(Table)
    if connection_id:
        table_query = table_query.join(Schema).filter(Schema.connection_id == connection_id)

    tables = table_query.all()

    # Filter out internal/system schemas — only include user data schemas
    SKIP_SCHEMAS = {"public", "pg_catalog", "information_schema"}
    tables = [t for t in tables if (t.schema.name if t.schema else "public") not in SKIP_SCHEMAS]

    if not tables:
        return "No tables found for this connection.\n"

    # Build a lookup: table_id -> schema_name.table_name
    table_ids = set()
    table_full_names = {}  # table_id -> "schema.table"
    date_text_columns = []  # columns that look like dates but are stored as text
    column_locations = {}   # column_name -> list of "schema.table" where it exists

    context = ""

    for table in tables:
        schema_name = table.schema.name if table.schema else "public"
        full_name = f"{schema_name}.{table.name}"
        table_ids.add(table.id)
        table_full_names[table.id] = full_name

        context += f"\n{full_name}:\n"

        col_parts = []
        for column in table.columns:
            # Build compact column entry
            col_entry = f"{column.name} ({column.data_type})"

            # Attach documentation if available
            doc = (
                session.query(Documentation)
                .filter_by(entity_type="column", entity_id=column.id)
                .first()
            )
            if doc and doc.description:
                col_entry += f" -> {doc.description}"

            # Attach team annotations if available
            annotations = session.query(Annotation).filter_by(
                table_name=table.name, column_name=column.name
            ).all()
            if annotations:
                notes = " | ".join([a.content for a in annotations])
                col_entry += f" [Team Notes: {notes}]"

            col_parts.append(f"  - {col_entry}")

            # Track date columns stored as text (for auto-casting hints)
            date_keywords = ["date", "timestamp", "time", "_at"]
            col_name_lower = column.name.lower()
            col_type_lower = (column.data_type or "").lower()
            if any(kw in col_name_lower for kw in date_keywords) and col_type_lower in ("text", "character varying", "varchar"):
                date_text_columns.append(f"{full_name}.{column.name}")

            # Track which tables have which columns
            column_locations.setdefault(column.name.lower(), []).append(full_name)

        context += "\n".join(col_parts) + "\n"

    # ----- 2. JOIN patterns from foreign key relationships -----
    # Only include relationships where at least one side belongs to our tables
    rel_query = session.query(Relationship)
    if table_ids:
        rel_query = rel_query.filter(Relationship.table_id.in_(table_ids))

    relationships = rel_query.all()

    if relationships:
        context += "\n=== JOIN PATTERNS (use these to connect tables) ===\n"
        seen_joins = set()
        for rel in relationships:
            join_key = (rel.source_table, rel.source_column, rel.target_table, rel.target_column)
            if join_key not in seen_joins:
                seen_joins.add(join_key)
                context += f"{rel.source_table}.{rel.source_column} → {rel.target_table}.{rel.target_column}\n"

    # ----- 3. Auto-generated important notes -----
    context += "\n=== IMPORTANT NOTES ===\n"

    if date_text_columns:
        col_names = ", ".join(date_text_columns)
        context += f"- DATE COLUMNS STORED AS TEXT (cast with ::timestamp): {col_names}\n"

    # Auto-detect monetary/value columns for revenue hints
    money_keywords = ["value", "price", "amount", "cost", "revenue", "salary", "payment", "fee", "freight"]
    monetary_columns = []
    for table in tables:
        schema_name = table.schema.name if table.schema else "public"
        for column in table.columns:
            col_type = (column.data_type or "").lower()
            if col_type in ("double precision", "numeric", "decimal", "real", "float", "money") and \
               any(kw in column.name.lower() for kw in money_keywords):
                monetary_columns.append(f"{schema_name}.{table.name}.{column.name}")
    if monetary_columns:
        context += f"- MONETARY/VALUE COLUMNS (use for revenue, sales, totals): {', '.join(monetary_columns)}\n"

    # Find columns that appear in multiple tables (helps the AI know where to find things)
    shared_columns = {col: tables_list for col, tables_list in column_locations.items() if len(tables_list) > 1}
    for col, tables_list in shared_columns.items():
        context += f"- Column '{col}' exists in: {', '.join(tables_list)} — use JOIN to connect them\n"

    return context