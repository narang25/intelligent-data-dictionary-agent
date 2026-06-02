import snowflake.connector
from typing import Dict, List

from app.connectors.base import BaseConnector, ConnectorError
from app.connectors.types import ColumnMeta, QueryResult


class SnowflakeConnector(BaseConnector):
    def __init__(self):
        self.conn = None
        self.credentials = None

    def connect(self, credentials: dict) -> None:
        self.credentials = credentials
        try:
            self.conn = snowflake.connector.connect(
                user=credentials.get("user"),
                password=credentials.get("password"),
                account=credentials.get("account"),
                warehouse=credentials.get("warehouse"),
                database=credentials.get("database"),
                schema=credentials.get("schema"),
                role=credentials.get("role")
            )
        except Exception as e:
            raise ConnectorError(f"Connection failed: {str(e)}", self.dialect)

    def _get_cursor(self):
        if not self.conn or self.conn.is_closed():
            self.connect(self.credentials)
        return self.conn.cursor(snowflake.connector.DictCursor)

    def get_schemas(self) -> List[str]:
        try:
            with self._get_cursor() as cur:
                cur.execute("SHOW SCHEMAS")
                return [row["name"] for row in cur.fetchall() if row["name"] not in ("INFORMATION_SCHEMA", "PUBLIC")]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch schemas: {str(e)}", self.dialect)

    def get_tables(self, schema: str) -> List[str]:
        try:
            with self._get_cursor() as cur:
                cur.execute(f"SHOW TABLES IN SCHEMA \"{schema}\"")
                return [row["name"] for row in cur.fetchall()]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch tables: {str(e)}", self.dialect)

    def get_columns(self, schema: str, table: str) -> List[ColumnMeta]:
        try:
            with self._get_cursor() as cur:
                cur.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COMMENT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = cur.fetchall()
                
                # Fetch PK constraints
                cur.execute(f"SHOW PRIMARY KEYS IN TABLE \"{schema}\".\"{table}\"")
                pk_cols = {row["column_name"] for row in cur.fetchall()}

            result = []
            for col in columns:
                result.append(ColumnMeta(
                    name=col["COLUMN_NAME"],
                    data_type=col["DATA_TYPE"],
                    is_nullable=(col["IS_NULLABLE"] == "YES"),
                    is_primary_key=(col["COLUMN_NAME"] in pk_cols),
                    is_foreign_key=False, # Complex to fetch in Snowflake without specific privileges
                    description=col.get("COMMENT")
                ))
            return result
        except Exception as e:
            raise ConnectorError(f"Failed to fetch columns: {str(e)}", self.dialect)

    def get_sample_rows(self, schema: str, table: str, limit: int = 5) -> List[dict]:
        try:
            with self._get_cursor() as cur:
                cur.execute(f"SELECT * FROM \"{schema}\".\"{table}\" LIMIT {limit}")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch sample rows: {str(e)}", self.dialect)

    def execute_query(self, sql: str) -> QueryResult:
        self._enforce_read_only(sql)
        try:
            with self._get_cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = []
                    for row in cur.fetchall():
                        rows.append([str(val) if val is not None else None for val in row.values()])
                    return QueryResult(columns=columns, rows=rows)
                return QueryResult(columns=[], rows=[])
        except Exception as e:
            return QueryResult(columns=[], rows=[], error=str(e))

    def get_row_count(self, schema: str, table: str) -> int:
        try:
            with self._get_cursor() as cur:
                cur.execute(f"SELECT COUNT(*) as cnt FROM \"{schema}\".\"{table}\"")
                return cur.fetchone()["CNT"]
        except Exception as e:
            raise ConnectorError(f"Failed to get row count: {str(e)}", self.dialect)

    def get_null_counts(self, schema: str, table: str) -> Dict[str, int]:
        columns = self.get_columns(schema, table)
        if not columns:
            return {}
            
        selects = []
        for col in columns:
            selects.append(f"COUNT_IF(\"{col.name}\" IS NULL) as \"{col.name}\"")
            
        sql = f"SELECT {', '.join(selects)} FROM \"{schema}\".\"{table}\""
        
        try:
            with self._get_cursor() as cur:
                cur.execute(sql)
                return dict(cur.fetchone())
        except Exception as e:
            raise ConnectorError(f"Failed to get null counts: {str(e)}", self.dialect)

    def get_distinct_counts(self, schema: str, table: str) -> Dict[str, int]:
        columns = self.get_columns(schema, table)
        if not columns:
            return {}
            
        selects = []
        for col in columns:
            selects.append(f"APPROX_COUNT_DISTINCT(\"{col.name}\") as \"{col.name}\"")
            
        sql = f"SELECT {', '.join(selects)} FROM \"{schema}\".\"{table}\""
        
        try:
            with self._get_cursor() as cur:
                cur.execute(sql)
                return dict(cur.fetchone())
        except Exception as e:
            raise ConnectorError(f"Failed to get distinct counts: {str(e)}", self.dialect)

    def test_connection(self) -> bool:
        try:
            with self._get_cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except:
            return False

    @property
    def dialect(self) -> str:
        return "snowflake"
