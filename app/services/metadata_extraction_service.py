"""
MetadataExtractionService — live metadata introspection via connectors.

Unlike ConnectionService.sync_schema() which stores extracted metadata in our DB,
this service queries the external database on-demand and returns results directly.
Used by the /schemas, /entities, /entities/:name/columns API endpoints.
"""
import logging
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.domain.models import DatabaseConnection
from app.connectors.factory import ConnectorFactory
from app.connectors.base import BaseConnector
from app.utils.encryption import decrypt_value

logger = logging.getLogger(__name__)


class MetadataExtractionService:
    """
    Why does this exist separately from ConnectionService?

    - ConnectionService handles CRUD, engine caching, and batch schema sync (store to DB)
    - MetadataExtractionService handles live introspection (query external DB, return immediately)

    This separation follows the Single Responsibility Principle and keeps each service focused.
    """

    def __init__(self, session: Session):
        self.session = session

    def _get_connector(self, connection_id: int, user_id: int) -> BaseConnector:
        """Load a connection from the DB and return a connected connector instance."""
        conn = (
            self.session.query(DatabaseConnection)
            .filter_by(id=connection_id, user_id=user_id, is_active=True)
            .first()
        )
        if not conn:
            raise ValueError(f"Connection {connection_id} not found or not accessible")

        connector = ConnectorFactory.create_connector(conn.db_type)

        # Build credentials
        password = decrypt_value(conn.encrypted_password) if conn.encrypted_password else None
        credentials = ConnectorFactory.build_credentials(
            conn.db_type,
            host=conn.host,
            port=conn.port,
            database=conn.database,
            username=conn.username,
            password=password,
            account=conn.account,
            warehouse=conn.warehouse,
            role=conn.role,
            credentials_json=conn.credentials_json,
        )

        connector.connect(credentials)
        return connector

    def get_schemas(self, connection_id: int, user_id: int) -> List[str]:
        """Return list of schemas/databases from the live external connection."""
        connector = self._get_connector(connection_id, user_id)
        return connector.get_schemas()

    def get_entities(
        self, connection_id: int, user_id: int, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Return list of tables/collections from the live external connection.

        If schema is not provided, iterates over all schemas.
        Returns unified entity format: { name, schema_name, entity_type, row_count, column_count }
        """
        connector = self._get_connector(connection_id, user_id)

        # Get the database type to determine entity_type label
        conn = (
            self.session.query(DatabaseConnection)
            .filter_by(id=connection_id, user_id=user_id, is_active=True)
            .first()
        )
        entity_type = "collection" if conn and conn.db_type == "mongodb" else "table"

        schemas_to_scan = [schema] if schema else connector.get_schemas()
        entities = []

        for schema_name in schemas_to_scan:
            try:
                tables = connector.get_tables(schema_name)
                for table_name in tables:
                    try:
                        row_count = connector.get_row_count(schema_name, table_name)
                    except Exception:
                        row_count = None

                    try:
                        columns = connector.get_columns(schema_name, table_name)
                        column_count = len(columns)
                    except Exception:
                        column_count = 0

                    entities.append({
                        "name": table_name,
                        "schema_name": schema_name,
                        "entity_type": entity_type,
                        "row_count": row_count,
                        "column_count": column_count,
                    })
            except Exception as e:
                logger.warning(f"Failed to scan schema '{schema_name}': {e}")

        return entities

    def get_columns(
        self, connection_id: int, user_id: int, entity_name: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Return column metadata for a specific table/collection from the live external connection.

        If schema is not provided, uses the first available schema.
        Returns unified column format: { name, data_type, nullable, is_primary_key, is_foreign_key, description }
        """
        connector = self._get_connector(connection_id, user_id)

        if not schema:
            schemas = connector.get_schemas()
            if not schemas:
                raise ValueError("No schemas found in this connection")
            schema = schemas[0]

        raw_columns = connector.get_columns(schema, entity_name)

        return [
            {
                "name": col.name,
                "data_type": col.data_type,
                "nullable": col.is_nullable,
                "is_primary_key": col.is_primary_key,
                "is_foreign_key": col.is_foreign_key,
                "description": col.description,
            }
            for col in raw_columns
        ]
