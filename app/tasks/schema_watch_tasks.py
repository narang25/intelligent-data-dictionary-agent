"""
Celery tasks for schema watch & sync (Feature 1).
Compares current DB schema against stored metadata, re-runs doc generation on changes.
"""
import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.domain.models import DatabaseConnection, Table, ColumnModel

logger = logging.getLogger(__name__)


@celery_app.task(name="schema_watch.check_all_connections")
def check_all_connections():
    """Celery Beat task: iterate each active connection, compare schema, flag changes."""
    db = SessionLocal()
    try:
        connections = db.query(DatabaseConnection).all()
        for conn in connections:
            try:
                _check_connection_schema(db, conn)
            except Exception as e:
                logger.error(f"Schema check failed for connection {conn.id}: {e}")
    finally:
        db.close()


def _check_connection_schema(db, conn):
    """Compare live schema against stored tables/columns. Flag drift."""
    from app.services.connection_service import ConnectionService

    svc = ConnectionService(db)
    engine = svc.get_engine(conn)

    # Get current live tables
    from sqlalchemy import inspect
    insp = inspect(engine)
    live_tables = set(insp.get_table_names())

    # Get stored tables
    stored = db.query(Table).filter_by(schema_id=conn.id).all()
    stored_names = {t.name for t in stored}

    new_tables = live_tables - stored_names
    dropped_tables = stored_names - live_tables

    changes = []

    if new_tables:
        changes.append(f"New tables: {', '.join(new_tables)}")
        logger.info(f"Connection {conn.id}: new tables detected: {new_tables}")

    if dropped_tables:
        changes.append(f"Dropped tables: {', '.join(dropped_tables)}")
        logger.info(f"Connection {conn.id}: dropped tables: {dropped_tables}")

    # Check for column changes in existing tables
    for table in stored:
        if table.name not in live_tables:
            continue
        live_columns = {c["name"] for c in insp.get_columns(table.name)}
        stored_columns = {c.name for c in table.columns}

        new_cols = live_columns - stored_columns
        dropped_cols = stored_columns - live_columns

        if new_cols:
            changes.append(f"{table.name}: new columns {new_cols}")
        if dropped_cols:
            changes.append(f"{table.name}: dropped columns {dropped_cols}")

    if changes:
        logger.info(f"Connection {conn.id}: schema drift detected. Re-syncing...")
        try:
            svc.sync_schema(conn)
            logger.info(f"Connection {conn.id}: schema re-synced successfully")
        except Exception as e:
            logger.error(f"Connection {conn.id}: re-sync failed: {e}")
