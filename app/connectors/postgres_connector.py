from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()


class PostgresConnector:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def get_schemas(self):
        query = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema','pg_toast');
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return [row[0] for row in result]

    def get_tables(self, schema_name):
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema_name
        AND table_type = 'BASE TABLE';
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"schema_name": schema_name})
            return [row[0] for row in result]

    def get_columns(self, schema_name, table_name):
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = :schema_name
        AND table_name = :table_name;
        """
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"schema_name": schema_name, "table_name": table_name},
            )
            return result.fetchall()
    
    def get_foreign_keys(self, schema_name):
        query = """
        SELECT
        tc.table_name AS source_table,
        kcu.column_name AS source_column,
        ccu.table_name AS target_table,
        ccu.column_name AS target_column
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = :schema_name;
    """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"schema_name": schema_name}
            )
            return result.fetchall()
