import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List

from app.connectors.base import BaseConnector, ConnectorError
from app.connectors.types import ColumnMeta, QueryResult


class PostgreSQLConnector(BaseConnector):
    def __init__(self):
        self.conn = None
        self.credentials = None

    def connect(self, credentials: dict) -> None:
        self.credentials = credentials
        try:
            self.conn = psycopg2.connect(
                host=credentials.get("host", "localhost"),
                port=credentials.get("port", 5432),
                dbname=credentials.get("database"),
                user=credentials.get("user"),
                password=credentials.get("password")
            )
        except Exception as e:
            raise ConnectorError(f"Connection failed: {str(e)}", self.dialect)

    def _get_cursor(self):
        if not self.conn or self.conn.closed:
            self.connect(self.credentials)
        return self.conn.cursor(cursor_factory=RealDictCursor)

    def get_schemas(self) -> List[str]:
        try:
            with self._get_cursor() as cur:
                cur.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                """)
                return [row["schema_name"] for row in cur.fetchall()]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch schemas: {str(e)}", self.dialect)

    def get_tables(self, schema: str) -> List[str]:
        try:
            with self._get_cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                """, (schema,))
                return [row["table_name"] for row in cur.fetchall()]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch tables: {str(e)}", self.dialect)

    def get_columns(self, schema: str, table: str) -> List[ColumnMeta]:
        try:
            with self._get_cursor() as cur:
                # 1. Fetch column definitions
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table))
                columns = cur.fetchall()

                # 2. Fetch primary keys
                cur.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tco
                    JOIN information_schema.key_column_usage kcu 
                      ON kcu.constraint_name = tco.constraint_name
                      AND kcu.constraint_schema = tco.constraint_schema
                    WHERE tco.constraint_type = 'PRIMARY KEY'
                      AND kcu.table_schema = %s AND kcu.table_name = %s
                """, (schema, table))
                pk_cols = {row["column_name"] for row in cur.fetchall()}

                # 3. Fetch foreign keys
                cur.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tco
                    JOIN information_schema.key_column_usage kcu 
                      ON tco.constraint_name = kcu.constraint_name 
                      AND tco.constraint_schema = kcu.constraint_schema
                    WHERE tco.constraint_type = 'FOREIGN KEY'
                      AND kcu.table_schema = %s AND kcu.table_name = %s
                """, (schema, table))
                fk_cols = {row["column_name"] for row in cur.fetchall()}

            result = []
            for col in columns:
                result.append(ColumnMeta(
                    name=col["column_name"],
                    data_type=col["data_type"],
                    is_nullable=(col["is_nullable"] == "YES"),
                    is_primary_key=(col["column_name"] in pk_cols),
                    is_foreign_key=(col["column_name"] in fk_cols),
                ))
            return result
        except Exception as e:
            raise ConnectorError(f"Failed to fetch columns: {str(e)}", self.dialect)

    def get_sample_rows(self, schema: str, table: str, limit: int = 5) -> List[dict]:
        try:
            with self._get_cursor() as cur:
                # Safe to inject schema/table names without parameterization using psycopg2's SQL composition if necessary, 
                # but simple string formatting with quoting is fine if controlled.
                # In IDD, these names come from information_schema so they are safe.
                cur.execute(f"SELECT * FROM \"{schema}\".\"{table}\" LIMIT {limit}")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch sample rows: {str(e)}", self.dialect)

    def execute_query(self, sql: str) -> QueryResult:
        self._enforce_read_only(sql)
        try:
            with self._get_cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY;")
                cur.execute(sql)
                # Some queries like SET statement might not return rows
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    # Format complex types to string so JSON serialization doesn't fail
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
                return cur.fetchone()["cnt"]
        except Exception as e:
            raise ConnectorError(f"Failed to get row count: {str(e)}", self.dialect)

    def get_null_counts(self, schema: str, table: str) -> Dict[str, int]:
        columns = self.get_columns(schema, table)
        if not columns:
            return {}
            
        selects = []
        for col in columns:
            selects.append(f"COUNT(*) FILTER (WHERE \"{col.name}\" IS NULL) as \"{col.name}\"")
            
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
            selects.append(f"COUNT(DISTINCT \"{col.name}\") as \"{col.name}\"")
            
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
        return "postgresql"
