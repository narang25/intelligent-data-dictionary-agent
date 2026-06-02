"""
MongoDB Connector — extracts metadata from MongoDB databases.

MongoDB maps to the unified model as:
  - Schema  → database name
  - Entity  → collection (entityType = "collection")
  - Columns → inferred from document sampling (no fixed schema in Mongo)
"""
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from app.connectors.base import BaseConnector, ConnectorError
from app.connectors.types import ColumnMeta, QueryResult


class MongoDBConnector(BaseConnector):
    def __init__(self):
        self.client = None
        self.credentials = None
        self._database_name: Optional[str] = None

    def connect(self, credentials: dict) -> None:
        self.credentials = credentials
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure

            # Support both connection string and individual fields
            connection_string = credentials.get("connection_string")
            if connection_string:
                self.client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
            else:
                host = credentials.get("host", "localhost")
                port = int(credentials.get("port", 27017))
                user = credentials.get("user")
                password = credentials.get("password")

                if user and password:
                    uri = f"mongodb://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}"
                else:
                    uri = f"mongodb://{host}:{port}"

                self.client = MongoClient(uri, serverSelectionTimeoutMS=10000)

            self._database_name = credentials.get("database")

            # Verify connectivity immediately
            self.client.admin.command("ping")

        except Exception as e:
            raise ConnectorError(f"Connection failed: {str(e)}", self.dialect)

    def _get_db(self):
        """Return the pymongo Database object."""
        if not self.client:
            self.connect(self.credentials)
        if not self._database_name:
            raise ConnectorError("No database name specified", self.dialect)
        return self.client[self._database_name]

    def get_schemas(self) -> List[str]:
        """In MongoDB, we treat the database name as the schema."""
        if self._database_name:
            return [self._database_name]
        try:
            # List all non-system databases
            return [
                name for name in self.client.list_database_names()
                if name not in ("admin", "local", "config")
            ]
        except Exception as e:
            raise ConnectorError(f"Failed to list databases: {str(e)}", self.dialect)

    def get_tables(self, schema: str) -> List[str]:
        """Return collection names (tables in MongoDB)."""
        try:
            db = self.client[schema]
            return [
                name for name in db.list_collection_names()
                if not name.startswith("system.")
            ]
        except Exception as e:
            raise ConnectorError(f"Failed to list collections: {str(e)}", self.dialect)

    def get_columns(self, schema: str, table: str) -> List[ColumnMeta]:
        """
        Infer columns by sampling documents from the collection.

        MongoDB has no fixed schema, so we sample up to 100 documents
        and union their keys. The data_type is inferred from the first
        non-null occurrence of each field.
        """
        try:
            db = self.client[schema]
            collection = db[table]

            # Sample documents to infer schema
            sample_docs = list(collection.find().limit(100))
            if not sample_docs:
                return []

            # Collect all unique keys and infer types
            field_types: Dict[str, str] = {}
            for doc in sample_docs:
                for key, value in doc.items():
                    if key == "_id":
                        continue
                    if key not in field_types and value is not None:
                        field_types[key] = type(value).__name__

            result = []
            # Add _id first
            result.append(ColumnMeta(
                name="_id",
                data_type="ObjectId",
                is_nullable=False,
                is_primary_key=True,
                is_foreign_key=False,
            ))

            for field_name, field_type in sorted(field_types.items()):
                result.append(ColumnMeta(
                    name=field_name,
                    data_type=self._map_python_type(field_type),
                    is_nullable=True,  # MongoDB fields are always optional
                    is_primary_key=False,
                    is_foreign_key=False,
                ))

            return result

        except Exception as e:
            raise ConnectorError(f"Failed to infer columns: {str(e)}", self.dialect)

    def get_sample_rows(self, schema: str, table: str, limit: int = 5) -> List[dict]:
        try:
            db = self.client[schema]
            collection = db[table]
            rows = []
            for doc in collection.find().limit(limit):
                # Convert ObjectId to string for JSON serialisation
                doc["_id"] = str(doc["_id"])
                rows.append(doc)
            return rows
        except Exception as e:
            raise ConnectorError(f"Failed to fetch sample rows: {str(e)}", self.dialect)

    def execute_query(self, sql: str) -> QueryResult:
        """MongoDB does not support SQL queries."""
        return QueryResult(
            columns=[], rows=[],
            error="SQL queries are not supported for MongoDB. Use the MongoDB shell or aggregation API instead."
        )

    def get_row_count(self, schema: str, table: str) -> int:
        try:
            db = self.client[schema]
            return db[table].estimated_document_count()
        except Exception as e:
            raise ConnectorError(f"Failed to get document count: {str(e)}", self.dialect)

    def get_null_counts(self, schema: str, table: str) -> Dict[str, int]:
        """
        Count documents where each field is null or missing.
        Uses aggregation pipeline for efficiency.
        """
        try:
            columns = self.get_columns(schema, table)
            if not columns:
                return {}

            db = self.client[schema]
            collection = db[table]
            total = collection.estimated_document_count()

            null_counts = {}
            for col in columns:
                if col.name == "_id":
                    null_counts[col.name] = 0
                    continue
                # Count documents where the field is null OR doesn't exist
                count = collection.count_documents({
                    "$or": [
                        {col.name: None},
                        {col.name: {"$exists": False}},
                    ]
                })
                null_counts[col.name] = count

            return null_counts
        except Exception as e:
            raise ConnectorError(f"Failed to get null counts: {str(e)}", self.dialect)

    def get_distinct_counts(self, schema: str, table: str) -> Dict[str, int]:
        """Count distinct values per field using aggregation."""
        try:
            columns = self.get_columns(schema, table)
            if not columns:
                return {}

            db = self.client[schema]
            collection = db[table]

            distinct_counts = {}
            for col in columns:
                try:
                    distinct_vals = collection.distinct(col.name)
                    distinct_counts[col.name] = len(distinct_vals)
                except Exception:
                    distinct_counts[col.name] = -1  # Signal that it couldn't be computed

            return distinct_counts
        except Exception as e:
            raise ConnectorError(f"Failed to get distinct counts: {str(e)}", self.dialect)

    def test_connection(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    @property
    def dialect(self) -> str:
        return "mongodb"

    @staticmethod
    def _map_python_type(py_type: str) -> str:
        """Map Python type names to friendly data type labels."""
        mapping = {
            "str": "string",
            "int": "int32",
            "float": "double",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "datetime": "date",
            "bytes": "binary",
            "ObjectId": "objectId",
            "Decimal128": "decimal",
        }
        return mapping.get(py_type, py_type)
