"""
Service for managing external database connections.
Handles validation, encryption, engine caching, and schema extraction orchestration.
Supports: PostgreSQL, MySQL, Snowflake, BigQuery, MongoDB.
"""
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.domain.models import DatabaseConnection, Schema, Table, ColumnModel, Relationship
from app.utils.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

# In-memory engine cache: { connection_id: engine }
_engine_cache: Dict[int, Any] = {}

# Supported database types
SUPPORTED_DB_TYPES = ["postgresql", "mysql", "snowflake", "mongodb"]


class ConnectionService:

    def __init__(self, session: Session):
        self.session = session

    # --------------------------------------------------
    # Connection CRUD
    # --------------------------------------------------
    def create_connection(
        self,
        user_id: int,
        name: str,
        host: str = None,
        port: int = None,
        database: str = "",
        username: str = None,
        password: str = None,
        db_type: str = "postgresql",
        account: str = None,
        warehouse: str = None,
        role: str = None,
    ) -> DatabaseConnection:
        """Validate, encrypt credentials, and persist a new connection."""
        if db_type not in SUPPORTED_DB_TYPES:
            raise ValueError(f"Unsupported database type: {db_type}. Supported: {', '.join(SUPPORTED_DB_TYPES)}")

        # Build URL and test connection
        if db_type == "mongodb":
            # MongoDB uses native driver, not SQLAlchemy
            result = self._test_mongodb_params(host, port, database, username, password)
            if result.get("status") != "ok":
                raise ValueError(result.get("detail", "MongoDB connection test failed"))
        else:
            db_url = self._build_url(db_type, host, port, database, username, password,
                                      account=account, warehouse=warehouse, role=role)
            self._test_connection(db_url, db_type)

        conn = DatabaseConnection(
            user_id=user_id,
            name=name,
            db_type=db_type,
            host=host or "",
            port=port or 0,
            database=database,
            username=username or "",
            encrypted_password=encrypt_value(password) if password else None,
            account=account,
            warehouse=warehouse,
            role=role,
        )
        self.session.add(conn)
        self.session.commit()
        self.session.refresh(conn)
        return conn

    def list_connections(self, user_id: int) -> List[DatabaseConnection]:
        return (
            self.session.query(DatabaseConnection)
            .filter_by(user_id=user_id, is_active=True)
            .order_by(DatabaseConnection.created_at.desc())
            .all()
        )

    def get_connection(self, connection_id: int, user_id: int) -> Optional[DatabaseConnection]:
        return (
            self.session.query(DatabaseConnection)
            .filter_by(id=connection_id, user_id=user_id, is_active=True)
            .first()
        )

    def delete_connection(self, connection_id: int, user_id: int) -> bool:
        conn = self.get_connection(connection_id, user_id)
        if not conn:
            return False
        conn.is_active = False
        self.session.commit()
        _engine_cache.pop(connection_id, None)
        return True

    def test_connection_params(
        self, host: str = None, port: int = None, database: str = "",
        username: str = None, password: str = None, db_type: str = "postgresql",
        account: str = None, warehouse: str = None, role: str = None,
    ) -> Dict[str, Any]:
        """Test connection without saving. Returns status + version info."""
        if db_type not in SUPPORTED_DB_TYPES:
            return {"status": "error", "detail": f"Unsupported database type: {db_type}"}

        # MongoDB doesn't use SQLAlchemy — use native connector
        if db_type == "mongodb":
            return self._test_mongodb_params(host, port, database, username, password)

        db_url = self._build_url(db_type, host, port, database, username, password,
                                  account=account, warehouse=warehouse, role=role)
        try:
            engine = self._create_engine(db_url, db_type)
            with engine.connect() as c:
                version = c.execute(text(self._version_query(db_type))).scalar()
            engine.dispose()
            return {"status": "ok", "version": version}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # --------------------------------------------------
    # Engine management
    # --------------------------------------------------
    def get_engine(self, connection_id: int, user_id: int):
        """Return a cached SQLAlchemy engine for the given connection."""
        if connection_id in _engine_cache:
            return _engine_cache[connection_id]

        conn = self.get_connection(connection_id, user_id)
        if not conn:
            raise ValueError("Connection not found")

        password = decrypt_value(conn.encrypted_password) if conn.encrypted_password else None
        db_url = self._build_url(conn.db_type, conn.host, conn.port, conn.database,
                                  conn.username, password,
                                  account=conn.account, warehouse=conn.warehouse,
                                  role=conn.role)
        engine = self._create_engine(db_url, conn.db_type,
                                      pooled=True)
        _engine_cache[connection_id] = engine
        return engine

    # --------------------------------------------------
    # Schema sync — dispatches to per-DB extractors
    # --------------------------------------------------
    def sync_schema(self, connection_id: int, user_id: int) -> Dict[str, Any]:
        """Extract schema from the external DB and store in internal metadata."""
        conn = self.get_connection(connection_id, user_id)
        if not conn:
            raise ValueError("Connection not found")

        if conn.db_type == "mongodb":
            stats = self._sync_mongodb(conn)
        else:
            engine = self.get_engine(connection_id, user_id)
            if conn.db_type == "postgresql":
                stats = self._sync_postgresql(engine, conn)
            elif conn.db_type == "mysql":
                stats = self._sync_mysql(engine, conn)
            elif conn.db_type == "snowflake":
                stats = self._sync_snowflake(engine, conn)
            else:
                raise ValueError(f"Unsupported database type for sync: {conn.db_type}")

        conn.last_synced = datetime.utcnow()
        self.session.commit()
        logger.info(f"Schema sync complete for connection {connection_id}: {stats}")
        return stats

    # ==================================================
    # Per-DB schema sync implementations
    # ==================================================

    def _sync_postgresql(self, engine, conn) -> Dict[str, Any]:
        stats = {"schemas": 0, "tables": 0, "columns": 0, "relationships": 0}
        with engine.connect() as ext_conn:
            schema_rows = ext_conn.execute(text("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            """)).fetchall()

            for (schema_name,) in schema_rows:
                schema_obj = self._upsert_schema(schema_name, conn.id)
                stats["schemas"] += 1

                table_rows = ext_conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = :schema AND table_type = 'BASE TABLE'
                """), {"schema": schema_name}).fetchall()

                for (table_name,) in table_rows:
                    row_count = self._safe_count(ext_conn, f'"{schema_name}"."{table_name}"')
                    table_obj = self._upsert_table(table_name, schema_obj.id, row_count)
                    stats["tables"] += 1

                    col_rows = ext_conn.execute(text("""
                        SELECT c.column_name, c.data_type, c.is_nullable,
                            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk,
                            CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_fk
                        FROM information_schema.columns c
                        LEFT JOIN (
                            SELECT kcu.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                            WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = :schema AND tc.table_name = :table
                        ) pk ON c.column_name = pk.column_name
                        LEFT JOIN (
                            SELECT kcu.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = :schema AND tc.table_name = :table
                        ) fk ON c.column_name = fk.column_name
                        WHERE c.table_schema = :schema AND c.table_name = :table
                    """), {"schema": schema_name, "table": table_name}).fetchall()

                    for col_name, data_type, is_nullable, is_pk, is_fk in col_rows:
                        self._upsert_column(col_name, data_type, is_nullable == "YES", bool(is_pk), bool(is_fk), table_obj.id)
                        stats["columns"] += 1

                fk_rows = ext_conn.execute(text("""
                    SELECT tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = :schema
                """), {"schema": schema_name}).fetchall()

                for src_table, src_col, tgt_table, tgt_col in fk_rows:
                    self._upsert_relationship(src_table, src_col, tgt_table, tgt_col, schema_obj.id)
                    stats["relationships"] += 1
        return stats

    def _sync_mysql(self, engine, conn) -> Dict[str, Any]:
        stats = {"schemas": 0, "tables": 0, "columns": 0, "relationships": 0}
        with engine.connect() as ext_conn:
            # In MySQL, the database IS the schema
            schema_name = conn.database
            schema_obj = self._upsert_schema(schema_name, conn.id)
            stats["schemas"] += 1

            table_rows = ext_conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = :schema AND table_type = 'BASE TABLE'
            """), {"schema": schema_name}).fetchall()

            for (table_name,) in table_rows:
                row_count = self._safe_count(ext_conn, f"`{table_name}`")
                table_obj = self._upsert_table(table_name, schema_obj.id, row_count)
                stats["tables"] += 1

                col_rows = ext_conn.execute(text("""
                    SELECT c.COLUMN_NAME, c.DATA_TYPE, c.IS_NULLABLE, c.COLUMN_KEY
                    FROM information_schema.columns c
                    WHERE c.TABLE_SCHEMA = :schema AND c.TABLE_NAME = :table
                    ORDER BY c.ORDINAL_POSITION
                """), {"schema": schema_name, "table": table_name}).fetchall()

                for col_name, data_type, is_nullable, col_key in col_rows:
                    self._upsert_column(
                        col_name, data_type, is_nullable == "YES",
                        col_key == "PRI", col_key == "MUL",
                        table_obj.id
                    )
                    stats["columns"] += 1

            # Foreign keys
            fk_rows = ext_conn.execute(text("""
                SELECT kcu.TABLE_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME, kcu.REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE kcu
                WHERE kcu.TABLE_SCHEMA = :schema AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """), {"schema": schema_name}).fetchall()

            for src_table, src_col, tgt_table, tgt_col in fk_rows:
                self._upsert_relationship(src_table, src_col, tgt_table, tgt_col, schema_obj.id)
                stats["relationships"] += 1
        return stats

    def _sync_snowflake(self, engine, conn) -> Dict[str, Any]:
        stats = {"schemas": 0, "tables": 0, "columns": 0, "relationships": 0}
        with engine.connect() as ext_conn:
            schema_rows = ext_conn.execute(text("""
                SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA')
            """)).fetchall()

            for (schema_name,) in schema_rows:
                schema_obj = self._upsert_schema(schema_name, conn.id)
                stats["schemas"] += 1

                table_rows = ext_conn.execute(text("""
                    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = :schema AND TABLE_TYPE = 'BASE TABLE'
                """), {"schema": schema_name}).fetchall()

                for (table_name,) in table_rows:
                    row_count = self._safe_count(ext_conn, f'"{schema_name}"."{table_name}"')
                    table_obj = self._upsert_table(table_name, schema_obj.id, row_count)
                    stats["tables"] += 1

                    col_rows = ext_conn.execute(text("""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
                        ORDER BY ORDINAL_POSITION
                    """), {"schema": schema_name, "table": table_name}).fetchall()

                    for col_name, data_type, is_nullable in col_rows:
                        self._upsert_column(col_name, data_type, is_nullable == "YES", False, False, table_obj.id)
                        stats["columns"] += 1

                # Snowflake FK constraints
                try:
                    fk_rows = ext_conn.execute(text("""
                        SELECT fk_table_name, fk_column_name, pk_table_name, pk_column_name
                        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                        JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc ON tc.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                        WHERE tc.TABLE_SCHEMA = :schema AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
                    """), {"schema": schema_name}).fetchall()
                    for src_table, src_col, tgt_table, tgt_col in fk_rows:
                        self._upsert_relationship(src_table, src_col, tgt_table, tgt_col, schema_obj.id)
                        stats["relationships"] += 1
                except Exception:
                    logger.info("Could not extract FK for Snowflake schema %s", schema_name)
        return stats

    def _sync_mongodb(self, conn) -> Dict[str, Any]:
        """Extract schema from MongoDB and store in internal metadata."""
        stats = {"schemas": 0, "tables": 0, "columns": 0, "relationships": 0}

        from app.connectors.factory import ConnectorFactory
        connector = ConnectorFactory.create_connector("mongodb")

        password = decrypt_value(conn.encrypted_password) if conn.encrypted_password else None
        credentials = {
            "host": conn.host,
            "port": conn.port,
            "database": conn.database,
            "user": conn.username,
            "password": password,
        }
        connector.connect(credentials)

        # MongoDB: database = schema
        schema_name = conn.database
        schema_obj = self._upsert_schema(schema_name, conn.id)
        stats["schemas"] += 1

        collections = connector.get_tables(schema_name)
        for coll_name in collections:
            row_count = connector.get_row_count(schema_name, coll_name)
            table_obj = self._upsert_table(coll_name, schema_obj.id, row_count)
            stats["tables"] += 1

            columns = connector.get_columns(schema_name, coll_name)
            for col in columns:
                self._upsert_column(
                    col.name, col.data_type, col.is_nullable,
                    col.is_primary_key, col.is_foreign_key, table_obj.id
                )
                stats["columns"] += 1

        return stats

    # ==================================================
    # Shared helpers for schema sync
    # ==================================================

    def _upsert_schema(self, schema_name: str, connection_id: int) -> Schema:
        schema_obj = self.session.query(Schema).filter_by(name=schema_name, connection_id=connection_id).first()
        if not schema_obj:
            schema_obj = Schema(name=schema_name, connection_id=connection_id)
            self.session.add(schema_obj)
            self.session.flush()
        return schema_obj

    def _upsert_table(self, table_name: str, schema_id: int, row_count=None) -> Table:
        table_obj = self.session.query(Table).filter_by(name=table_name, schema_id=schema_id).first()
        if not table_obj:
            table_obj = Table(name=table_name, schema_id=schema_id, row_count=row_count)
            self.session.add(table_obj)
            self.session.flush()
        else:
            table_obj.row_count = row_count
        return table_obj

    def _upsert_column(self, name, data_type, is_nullable, is_pk, is_fk, table_id):
        existing = self.session.query(ColumnModel).filter_by(name=name, table_id=table_id).first()
        if not existing:
            col = ColumnModel(
                name=name, data_type=data_type, is_nullable=is_nullable,
                is_primary_key=is_pk, is_foreign_key=is_fk, table_id=table_id,
            )
            self.session.add(col)
        else:
            existing.data_type = data_type
            existing.is_nullable = is_nullable
            existing.is_primary_key = is_pk
            existing.is_foreign_key = is_fk

    def _upsert_relationship(self, src_table, src_col, tgt_table, tgt_col, schema_id):
        existing = self.session.query(Relationship).filter_by(
            source_table=src_table, source_column=src_col,
            target_table=tgt_table, target_column=tgt_col).first()
        if not existing:
            src_table_obj = self.session.query(Table).filter_by(name=src_table, schema_id=schema_id).first()
            if src_table_obj:
                self.session.add(Relationship(
                    source_table=src_table, source_column=src_col,
                    target_table=tgt_table, target_column=tgt_col,
                    table_id=src_table_obj.id))

    def _safe_count(self, ext_conn, qualified_name: str):
        try:
            return ext_conn.execute(text(f"SELECT COUNT(*) FROM {qualified_name}")).scalar()
        except Exception:
            return None

    # --------------------------------------------------
    # URL / Engine helpers
    # --------------------------------------------------
    @staticmethod
    def _build_url(db_type: str, host=None, port=None, database="", username=None, password=None,
                   account=None, warehouse=None, role=None) -> str:
        from urllib.parse import quote_plus
        
        user_enc = quote_plus(username) if username else ""
        pass_enc = quote_plus(password) if password else ""
        
        # Format credentials block: "user:pass@" or "user@" or ""
        creds = ""
        if user_enc and pass_enc:
            creds = f"{user_enc}:{pass_enc}@"
        elif user_enc:
            creds = f"{user_enc}@"
            
        if db_type == "postgresql":
            return f"postgresql://{creds}{host}:{port}/{database}"
        elif db_type == "mysql":
            return f"mysql+pymysql://{creds}{host}:{port}/{database}"
        elif db_type == "snowflake":
            url = f"snowflake://{creds}{account}/{database}"
            params = []
            if warehouse:
                params.append(f"warehouse={warehouse}")
            if role:
                params.append(f"role={role}")
            if params:
                url += "?" + "&".join(params)
            return url
        elif db_type == "mongodb":
            # MongoDB doesn't use SQLAlchemy — return a placeholder
            if username and password:
                from urllib.parse import quote_plus
                return f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/{database}"
            return f"mongodb://{host}:{port}/{database}"
        raise ValueError(f"Unsupported database type: {db_type}")

    @staticmethod
    def _version_query(db_type: str) -> str:
        """Return a simple version query for each DB type."""
        if db_type == "postgresql":
            return "SELECT version()"
        elif db_type == "mysql":
            return "SELECT version()"
        elif db_type == "snowflake":
            return "SELECT CURRENT_VERSION()"
        elif db_type == "mongodb":
            return ""  # MongoDB doesn't use SQL — handled separately
        return "SELECT 1"

    @staticmethod
    def _create_engine(db_url: str, db_type: str, pooled: bool = False):
        """Create a SQLAlchemy engine with DB-specific connect args."""
        kwargs = {}

        if db_type == "postgresql":
            if pooled:
                kwargs["pool_size"] = 5
                kwargs["max_overflow"] = 3
                kwargs["pool_pre_ping"] = True
                kwargs["connect_args"] = {"options": "-c statement_timeout=30000"}
            else:
                kwargs["pool_pre_ping"] = True

        elif db_type == "mysql":
            if pooled:
                kwargs["pool_size"] = 5
                kwargs["max_overflow"] = 3
            kwargs["pool_pre_ping"] = True

        elif db_type == "snowflake":
            if pooled:
                kwargs["pool_size"] = 3
                kwargs["max_overflow"] = 2
            kwargs["pool_pre_ping"] = True


        return create_engine(db_url, **kwargs)

    @staticmethod
    def _test_connection(db_url: str, db_type: str = "postgresql"):
        """Quick connectivity check. Raises on failure."""
        if db_type == "mongodb":
            # MongoDB doesn't use SQLAlchemy — skip the engine test.
            # Connectivity is tested via the connector's test_connection() in _test_mongodb_params.
            return

        engine = ConnectionService._create_engine(db_url, db_type)
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
        finally:
            engine.dispose()

    @staticmethod
    def _test_mongodb_params(host, port, database, username, password) -> Dict[str, Any]:
        """Test MongoDB connection using native pymongo driver."""
        try:
            from app.connectors.factory import ConnectorFactory

            connector = ConnectorFactory.create_connector("mongodb")
            credentials = {
                "host": host or "localhost",
                "port": int(port or 27017),
                "database": database,
                "user": username,
                "password": password,
            }
            connector.connect(credentials)

            if connector.test_connection():
                # Get MongoDB version
                build_info = connector.client.admin.command("buildInfo")
                version = f"MongoDB {build_info.get('version', 'unknown')}"
                return {"status": "ok", "version": version}
            else:
                return {"status": "error", "detail": "MongoDB connection test failed"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
