from sqlalchemy.orm import Session
from app.connectors.postgres_connector import PostgresConnector
from app.domain.models import Schema, Table, ColumnModel, Relationship


class SchemaIngestionService:

    def __init__(self, db_url: str, session: Session):
        self.connector = PostgresConnector(db_url)
        self.session = session

    def ingest(self):
        schemas = self.connector.get_schemas()

        for schema_name in schemas:

            # Check if schema already exists
            existing_schema = (
                self.session.query(Schema)
                .filter_by(name=schema_name)
                .first()
            )

            if existing_schema:
                schema_obj = existing_schema
            else:
                schema_obj = Schema(name=schema_name)
                self.session.add(schema_obj)
                self.session.flush()

            tables = self.connector.get_tables(schema_name)

            for table_name in tables:

                existing_table = (
                    self.session.query(Table)
                    .filter_by(name=table_name, schema_id=schema_obj.id)
                    .first()
                )

                if existing_table:
                    table_obj = existing_table
                else:
                    table_obj = Table(
                        name=table_name,
                        schema_id=schema_obj.id
                    )
                    self.session.add(table_obj)
                    self.session.flush()

                columns = self.connector.get_columns(schema_name, table_name)

                for col_name, data_type, is_nullable in columns:

                    existing_column = (
                        self.session.query(ColumnModel)
                        .filter_by(name=col_name, table_id=table_obj.id)
                        .first()
                    )

                    if not existing_column:
                        column_obj = ColumnModel(
                            name=col_name,
                            data_type=data_type,
                            is_nullable=(is_nullable == "YES"),
                            table_id=table_obj.id
                        )
                        self.session.add(column_obj)

            # 🔹 Foreign Keys should be handled per schema (not per table loop)
            foreign_keys = self.connector.get_foreign_keys(schema_name)

            for source_table, source_column, target_table, target_column in foreign_keys:

                existing_relationship = (
                    self.session.query(Relationship)
                    .filter_by(
                        source_table=source_table,
                        source_column=source_column,
                        target_table=target_table,
                        target_column=target_column
                    )
                    .first()
                )

                if not existing_relationship:
                    relationship = Relationship(
                        source_table=source_table,
                        source_column=source_column,
                        target_table=target_table,
                        target_column=target_column
                    )

                    self.session.add(relationship)

        # Commit once at the end (much better practice)
        self.session.commit()

        print("Schema ingestion completed successfully!")
