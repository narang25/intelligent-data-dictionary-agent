"""
Connectors package — registers all built-in connectors with the factory.

Connectors that require optional drivers (Snowflake, MongoDB)
are registered with lazy imports so the app starts even if those drivers
are not installed. The import error only surfaces when you actually try
to create a connector of that type.

Adding a new connector:
  1. Implement BaseConnector in a new file
  2. Add a register() call below
  3. Done — all API endpoints automatically support it
"""
import logging
from app.connectors.factory import ConnectorFactory

logger = logging.getLogger(__name__)


def _safe_register(source_type: str, module_path: str, class_name: str):
    """
    Try to import and register a connector. If the driver isn't installed,
    log a warning but don't crash the app.
    """
    try:
        import importlib
        module = importlib.import_module(module_path)
        connector_class = getattr(module, class_name)
        ConnectorFactory.register(source_type, connector_class)
    except ImportError as e:
        logger.warning(
            f"Could not register '{source_type}' connector: {e}. "
            f"Install the required driver to enable this connector."
        )
    except Exception as e:
        logger.error(f"Failed to register '{source_type}' connector: {e}")


# -------------------------------------------------------
# Register built-in connectors
# -------------------------------------------------------

# PostgreSQL — always available (psycopg2-binary in requirements)
_safe_register("postgresql", "app.connectors.postgresql_connector", "PostgreSQLConnector")

# MySQL
_safe_register("mysql", "app.connectors.mysql_connector", "MySQLConnector")

# Snowflake (optional driver)
_safe_register("snowflake", "app.connectors.snowflake_connector", "SnowflakeConnector")

# MongoDB
_safe_register("mongodb", "app.connectors.mongodb_connector", "MongoDBConnector")
