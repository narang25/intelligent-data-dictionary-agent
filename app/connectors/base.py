import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.connectors.types import ColumnMeta, QueryResult


class ConnectorError(Exception):
    """Exception raised for errors during connector operations."""
    def __init__(self, message: str, source_db_type: str):
        self.message = message
        self.source_db_type = source_db_type
        super().__init__(f"{source_db_type} Connector Error: {message}")


class ReadOnlyViolationError(ConnectorError):
    """Exception raised when a non-SELECT query is attempted."""
    def __init__(self, message: str, source_db_type: str):
        super().__init__(message, source_db_type)


class ConnectionTimeoutError(ConnectorError):
    """Exception raised when a connection attempt times out."""
    def __init__(self, message: str, source_db_type: str):
        super().__init__(message, source_db_type)


class InvalidCredentialsError(ConnectorError):
    """Exception raised when credentials are invalid."""
    def __init__(self, message: str, source_db_type: str):
        super().__init__(message, source_db_type)


class DatabaseUnavailableError(ConnectorError):
    """Exception raised when the target database is unreachable."""
    def __init__(self, message: str, source_db_type: str):
        super().__init__(message, source_db_type)


class UnsupportedConnectorError(ConnectorError):
    """Exception raised when a requested connector type is not registered."""
    def __init__(self, source_db_type: str):
        super().__init__(
            f"Unsupported connector type: '{source_db_type}'. "
            f"No connector implementation is registered for this source.",
            source_db_type,
        )


class BaseConnector(ABC):
    
    @abstractmethod
    def connect(self, credentials: dict) -> None:
        """Establish connection to the source database."""
        pass

    @abstractmethod
    def get_schemas(self) -> List[str]:
        """Return list of all schema/dataset names."""
        pass

    @abstractmethod
    def get_tables(self, schema: str) -> List[str]:
        """Return list of table names in a schema."""
        pass

    @abstractmethod
    def get_columns(self, schema: str, table: str) -> List[ColumnMeta]:
        """Return column metadata: name, type, nullable, description."""
        pass

    @abstractmethod
    def get_sample_rows(self, schema: str, table: str, limit: int = 5) -> List[dict]:
        """Return sample rows for profiling and documentation context."""
        pass

    @abstractmethod
    def execute_query(self, sql: str) -> QueryResult:
        """Execute a validated SELECT query and return results."""
        pass

    @abstractmethod
    def get_row_count(self, schema: str, table: str) -> int:
        """Return approximate row count for a table."""
        pass

    @abstractmethod
    def get_null_counts(self, schema: str, table: str) -> Dict[str, int]:
        """Return null count per column."""
        pass

    @abstractmethod
    def get_distinct_counts(self, schema: str, table: str) -> Dict[str, int]:
        """Return distinct value count per column."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify credentials and connectivity."""
        pass

    @property
    @abstractmethod
    def dialect(self) -> str:
        """Return SQL dialect: postgresql | mysql | snowflake"""
        pass
        
    def _enforce_read_only(self, sql: str) -> None:
        """Ensure the query is standard SELECT and does not modify data."""
        sql_clean = sql.strip().lower()
        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"]
        for word in forbidden:
            # Match whole words to avoid catching valid column names like "drop_zone"
            if re.search(rf'\b{word}\b', sql_clean):
                raise ReadOnlyViolationError(f"Forbidden keyword '{word}' detected. Only SELECT queries are allowed.", self.dialect)
