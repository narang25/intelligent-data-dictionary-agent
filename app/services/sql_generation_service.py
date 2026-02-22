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
    def generate_sql(self, schema_context: str, question: str):

        system_prompt = """
You are a senior PostgreSQL database architect.

CRITICAL RULES:
1. You MUST use SCHEMA-QUALIFIED table names (e.g., olist.orders, olist.customers)
2. You MUST ONLY use columns from the CORRECT table - check which table has each column!
3. You MUST NOT invent or assume column names
4. When "olist" is mentioned, it refers to the SCHEMA name, not a table

=== EXACT OLIST SCHEMA (USE ONLY THESE COLUMNS) ===

olist.customers:
  - customer_id (text), customer_unique_id (text), customer_zip_code_prefix (bigint), 
    customer_city (text), customer_state (text)

olist.orders:
  - order_id (text), customer_id (text), order_status (text), 
    order_purchase_timestamp (text), order_approved_at (text),
    order_delivered_carrier_date (text), order_delivered_customer_date (text), 
    order_estimated_delivery_date (text)
  NOTE: Date columns are in THIS table, not in payments!

olist.order_items:
  - order_id (text), order_item_id (bigint), product_id (text), seller_id (text), 
    shipping_limit_date (text), price (double), freight_value (double)

olist.payments:
  - order_id (text), payment_sequential (bigint), payment_type (text), 
    payment_installments (bigint), payment_value (double)
  NOTE: NO date columns here! Must JOIN with orders to get dates!

olist.products:
  - product_id (text), product_category_name (text), product_name_lenght (double), 
    product_description_lenght (double), product_photos_qty (double), 
    product_weight_g (double), product_length_cm (double), 
    product_height_cm (double), product_width_cm (double)

olist.sellers:
  - seller_id (text), seller_zip_code_prefix (bigint), seller_city (text), seller_state (text)

olist.reviews:
  - review_id (text), order_id (text), review_score (int), 
    review_comment_title (text), review_comment_message (text)

=== CRITICAL JOIN PATTERNS ===

For MONTHLY/YEARLY REVENUE (must JOIN orders and payments):
  SELECT 
    EXTRACT(YEAR FROM o.order_purchase_timestamp::timestamp) AS year,
    EXTRACT(MONTH FROM o.order_purchase_timestamp::timestamp) AS month,
    SUM(p.payment_value) AS revenue
  FROM olist.orders o
  JOIN olist.payments p ON o.order_id = p.order_id
  GROUP BY year, month
  ORDER BY year, month

=== IMPORTANT NOTES ===
- Date columns (order_purchase_timestamp, etc.) are ONLY in olist.orders
- Payment amounts (payment_value) are ONLY in olist.payments  
- For time-based revenue analysis: JOIN orders and payments ON order_id
- DATE COLUMNS ARE TEXT: Cast like order_purchase_timestamp::timestamp
- State in customers: customer_state | State in sellers: seller_state
- Category: product_category_name

Return ONLY valid SELECT SQL with schema-qualified table names.

IMPORTANT: Return ONLY a valid JSON object:
{"sql": "SELECT ... FROM olist.table_name ...", "explanation": "..."}
"""

        user_prompt = f"""
Additional Schema Context:
{schema_context}

User Question:
{question}

REMEMBER: 
- Date columns are in olist.orders, payment_value is in olist.payments
- For time-based revenue, JOIN orders and payments
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
        # Remove EXTRACT(...FROM...) to avoid false positives
        # EXTRACT(EPOCH FROM column) should not match as a table
        # ----------------------------
        sql_cleaned = re.sub(r'extract\s*\([^)]*\)', '', sql_lower)
        
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
    def execute_safe_query(self, engine, sql: str):

        # Step 1: Basic validation
        if not self.validate_sql(sql):
            return {"error": "Unsafe or invalid SQL detected."}

        # Step 2: Column validation
        valid, error = self.validate_sql_columns(engine, sql)
        if not valid:
            return {"error": error}

        # Step 3: Enforce LIMIT
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
            return {"error": str(e)}


# ------------------------------------------------
# Build Schema Context Helper
# ------------------------------------------------
def build_schema_context(session):

    from app.domain.models import Table, Relationship, Documentation

    context = ""

    tables = session.query(Table).all()

    for table in tables:

        context += f"\nTable: {table.schema.name}.{table.name}\n"
        context += "Columns:\n"

        for column in table.columns:

            doc = (
                session.query(Documentation)
                .filter_by(entity_type="column", entity_id=column.id)
                .first()
            )

            description = ""
            if doc and doc.description:
                description = f" -> {doc.description}"

            context += f"- {column.name} ({column.data_type}){description}\n"

        context += "\n"

    context += "\nRelationships:\n"

    relationships = session.query(Relationship).all()

    for rel in relationships:
        context += (
            f"{rel.source_table}.{rel.source_column} "
            f"→ {rel.target_table}.{rel.target_column}\n"
        )

    return context