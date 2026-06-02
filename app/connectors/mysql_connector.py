import pymysql
from typing import Dict, List

from app.connectors.base import BaseConnector, ConnectorError
from app.connectors.types import ColumnMeta, QueryResult


class MySQLConnector(BaseConnector):
    def __init__(self):
        self.conn = None
        self.credentials = None

    def connect(self, credentials: dict) -> None:
        self.credentials = credentials
        try:
            self.conn = pymysql.connect(
                host=credentials.get("host", "localhost"),
                port=credentials.get("port", 3306),
                user=credentials.get("user"),
                password=credentials.get("password"),
                database=credentials.get("database"),
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            raise ConnectorError(f"Connection failed: {str(e)}", self.dialect)

    def _get_cursor(self):
        if not self.conn or not self.conn.open:
            self.connect(self.credentials)
        # Ping the server and reconnect if needed
        self.conn.ping(reconnect=True)
        return self.conn.cursor()

    def get_schemas(self) -> List[str]:
        # In MySQL, database = schema. Since we connected to a specific database,
        # we consider that database name as the only schema.
        if self.credentials and self.credentials.get("database"):
            return [self.credentials.get("database")]
        return []

    def get_tables(self, schema: str) -> List[str]:
        try:
            with self._get_cursor() as cur:
                cur.execute("""
                    SELECT TABLE_NAME 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                """, (schema,))
                return [row["TABLE_NAME"] for row in cur.fetchall()]
        except Exception as e:
            raise ConnectorError(f"Failed to fetch tables: {str(e)}", self.dialect)

    def get_columns(self, schema: str, table: str) -> List[ColumnMeta]:
        try:
            with self._get_cursor() as cur:
                # Need column definition and keys
                cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (schema, table))
                columns = cur.fetchall()

            result = []
            for col in columns:
                # Handle boolean tinyint mapping
                data_type = col["DATA_TYPE"]
                is_pk = col["COLUMN_KEY"] == "PRI"
                is_fk = col["COLUMN_KEY"] == "MUL"  # MUL is often foreign key or index in MySQL
                
                result.append(ColumnMeta(
                    name=col["COLUMN_NAME"],
                    data_type=data_type,
                    is_nullable=(col["IS_NULLABLE"] == "YES"),
                    is_primary_key=is_pk,
                    is_foreign_key=is_fk,
                    description=col.get("COLUMN_COMMENT")
                ))
            return result
        except Exception as e:
            raise ConnectorError(f"Failed to fetch columns: {str(e)}", self.dialect)

    def get_sample_rows(self, schema: str, table: str, limit: int = 5) -> List[dict]:
        try:
            with self._get_cursor() as cur:
                cur.execute(f"SELECT * FROM `{schema}`.`{table}` LIMIT {limit}")
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
                cur.execute(f"SELECT COUNT(*) as cnt FROM `{schema}`.`{table}`")
                return cur.fetchone()["cnt"]
        except Exception as e:
            raise ConnectorError(f"Failed to get row count: {str(e)}", self.dialect)

    def get_null_counts(self, schema: str, table: str) -> Dict[str, int]:
        columns = self.get_columns(schema, table)
        if not columns:
            return {}
            
        selects = []
        for col in columns:
            # MySQL trick: SUM(col IS NULL) counts nulls
            selects.append(f"SUM(`{col.name}` IS NULL) as `{col.name}`")
            
        sql = f"SELECT {', '.join(selects)} FROM `{schema}`.`{table}`"
        
        try:
            with self._get_cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                # Handle possible None results from empty tables
                return {k: int(v) if v is not None else 0 for k, v in row.items()}
        except Exception as e:
            raise ConnectorError(f"Failed to get null counts: {str(e)}", self.dialect)

    def get_distinct_counts(self, schema: str, table: str) -> Dict[str, int]:
        columns = self.get_columns(schema, table)
        if not columns:
            return {}
            
        selects = []
        for col in columns:
            selects.append(f"COUNT(DISTINCT `{col.name}`) as `{col.name}`")
            
        sql = f"SELECT {', '.join(selects)} FROM `{schema}`.`{table}`"
        
        try:
            with self._get_cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                return {k: int(v) if v is not None else 0 for k, v in row.items()}
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
        return "mysql"
