"""
ConnectorFactory — central registry for connector implementations.

Adding a new connector:
  1. Implement BaseConnector in a new file (e.g. oracle_connector.py)
  2. Call ConnectorFactory.register("oracle", OracleConnector)
  3. Done. All endpoints automatically support the new type.
"""
import logging
from typing import Dict, List, Type

from app.connectors.base import BaseConnector, UnsupportedConnectorError

logger = logging.getLogger(__name__)


class ConnectorFactory:
    """
    Registry-based factory for creating connector instances.

    Why a factory?
    - Single source of truth for which connector types are available
    - Eliminates scattered if/elif chains (they were in registry.py, connections.py, connection_service.py)
    - New connectors register once; all API routes pick them up automatically
    """

    _registry: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, source_type: str, connector_class: Type[BaseConnector]) -> None:
        """Register a connector implementation for a given source type."""
        source_type = source_type.lower()
        cls._registry[source_type] = connector_class
        logger.info(f"Registered connector: {source_type} -> {connector_class.__name__}")

    @classmethod
    def create_connector(cls, source_type: str) -> BaseConnector:
        """
        Instantiate a connector for the given source type.

        Raises UnsupportedConnectorError if no connector is registered.
        """
        source_type = source_type.lower()
        connector_class = cls._registry.get(source_type)
        if not connector_class:
            raise UnsupportedConnectorError(source_type)
        return connector_class()

    @classmethod
    def supported_types(cls) -> List[str]:
        """Return list of all registered connector type names."""
        return sorted(cls._registry.keys())

    @classmethod
    def is_supported(cls, source_type: str) -> bool:
        """Check if a connector type is registered."""
        return source_type.lower() in cls._registry

    @classmethod
    def build_credentials(cls, source_type: str, **kwargs) -> dict:
        """
        Build the credentials dict each connector expects from flat API fields.

        This centralises credential shape knowledge so the API layer stays generic.
        """
        source_type = source_type.lower()

        if source_type in ("postgresql", "mysql"):
            default_port = 5432 if source_type == "postgresql" else 3306
            return {
                "host": kwargs.get("host") or "localhost",
                "port": int(kwargs.get("port") or default_port),
                "database": kwargs.get("database"),
                "user": kwargs.get("username"),
                "password": kwargs.get("password"),
            }
        elif source_type == "snowflake":
            return {
                "account": kwargs.get("account"),
                "database": kwargs.get("database"),
                "warehouse": kwargs.get("warehouse"),
                "role": kwargs.get("role"),
                "user": kwargs.get("username"),
                "password": kwargs.get("password"),
            }
        elif source_type == "mongodb":
            return {
                "host": kwargs.get("host") or "localhost",
                "port": int(kwargs.get("port") or 27017),
                "database": kwargs.get("database"),
                "user": kwargs.get("username"),
                "password": kwargs.get("password"),
                "connection_string": kwargs.get("connection_string"),
            }
        else:
            # Generic fallback — pass through whatever was provided
            return {k: v for k, v in kwargs.items() if v is not None}
