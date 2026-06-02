import os
import json
from base64 import b64encode
from cryptography.fernet import Fernet
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.domain.models import SourceConnection
from app.connectors.base import BaseConnector
from app.connectors.postgresql_connector import PostgreSQLConnector
from app.connectors.mysql_connector import MySQLConnector
from app.connectors.snowflake_connector import SnowflakeConnector

# Key management: Retrieve SECRET_KEY from environment or generate a valid Fernet key.
# A Fernet key must be 32 url-safe base64-encoded bytes.
_SECRET_KEY = os.getenv("SECRET_KEY", "b42ec328404ee88ebfecc9ed2ee161d7")
if len(_SECRET_KEY) < 32:
    _SECRET_KEY = _SECRET_KEY.ljust(32, '0')
_FERNET_KEY = b64encode(_SECRET_KEY[:32].encode('utf-8'))

cipher_suite = Fernet(_FERNET_KEY)


def encrypt_credentials(creds_dict: dict) -> str:
    creds_json = json.dumps(creds_dict)
    return cipher_suite.encrypt(creds_json.encode('utf-8')).decode('utf-8')


def decrypt_credentials(encrypted_text: str) -> dict:
    decrypted_json = cipher_suite.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
    return json.loads(decrypted_json)


class ConnectorRegistry:
    def __init__(self):
        # Cache of active connector instances: { "connection_id_str": BaseConnector_instance }
        self._registry: Dict[str, BaseConnector] = {}

    def get_connector(self, db: Session, connection_id: str) -> BaseConnector:
        """Fetch a connector instance by connection ID. Instantiates it if not cached."""
        if connection_id in self._registry:
            return self._registry[connection_id]

        conn_record = db.query(SourceConnection).filter_by(id=connection_id, is_active=True).first()
        if not conn_record:
            raise ValueError(f"Active SourceConnection with id '{connection_id}' not found.")

        creds = decrypt_credentials(conn_record.encrypted_credentials)
        
        connector: BaseConnector
        if conn_record.db_type == "postgresql":
            connector = PostgreSQLConnector()
        elif conn_record.db_type == "mysql":
            connector = MySQLConnector()
        elif conn_record.db_type == "snowflake":
            connector = SnowflakeConnector()
        else:
            raise ValueError(f"Unsupported db_type: {conn_record.db_type}")

        connector.connect(creds)
        self._registry[connection_id] = connector
        return connector

    def clear_cache(self, connection_id: str = None) -> None:
        """Clear specific connector or all connectors from memory cache."""
        if connection_id:
            self._registry.pop(connection_id, None)
        else:
            self._registry.clear()

    def list_connections(self, db: Session, user_id: int = None) -> List[dict]:
        """Return list of connection summaries without credentials."""
        query = db.query(SourceConnection).filter_by(is_active=True)
        if user_id is not None:
            query = query.filter_by(created_by=user_id)
            
        return [
            {
                "id": c.id,
                "name": c.name,
                "db_type": c.db_type,
                "status": "connected" if c.last_tested_at else "untested",
                "last_tested_at": c.last_tested_at.isoformat() if c.last_tested_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in query.all()
        ]

# Global registry instance
registry = ConnectorRegistry()
