import os
from dotenv import load_dotenv
from app.connectors.postgres_connector import PostgresConnector

load_dotenv()

connector = PostgresConnector(os.getenv("DATABASE_URL"))

schemas = connector.get_schemas()
print("Schemas:", schemas)

for schema in schemas:
    tables = connector.get_tables(schema)
    print(f"\nSchema: {schema}")
    print("Tables:", tables)

    for table in tables:
        columns = connector.get_columns(schema, table)
        print(f"  Table: {table}")
        for col in columns:
            print("   ", col)
