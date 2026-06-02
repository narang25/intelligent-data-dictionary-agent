"""
Connections API — create, test, list, delete, sync connections + metadata extraction.

All endpoints now use DatabaseConnection model + ConnectionService,
which is what every downstream API (tables, dashboard, quality, etc.) expects.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User
from app.services.connection_service import ConnectionService
from app.connectors.factory import ConnectorFactory
from app.connectors.base import (
    ConnectorError,
    ConnectionTimeoutError,
    InvalidCredentialsError,
    DatabaseUnavailableError,
    UnsupportedConnectorError,
)

router = APIRouter(prefix="/v1", tags=["connections"])


# =========================
# Request / Response DTOs
# =========================
class ConnectionCreate(BaseModel):
    name: str = Field(..., example="Production DB")
    db_type: str = Field(..., example="postgresql")
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    # Snowflake-specific
    account: Optional[str] = None
    warehouse: Optional[str] = None
    role: Optional[str] = None
    # MongoDB-specific
    connection_string: Optional[str] = None


class ConnectionSummary(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database: str
    status: str
    created_at: Optional[str] = None
    last_synced: Optional[str] = None


class SchemaResponse(BaseModel):
    schemas: List[str]


class EntitySummary(BaseModel):
    name: str
    schema_name: str
    entity_type: str  # "table" or "collection"
    row_count: Optional[int] = None
    column_count: int = 0


class ColumnDetail(BaseModel):
    name: str
    data_type: str
    nullable: Optional[bool] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: Optional[str] = None


# =========================
# Helper — map errors to HTTP codes
# =========================
def _handle_connector_error(e: Exception) -> HTTPException:
    """Convert connector exceptions to appropriate HTTP errors."""
    if isinstance(e, UnsupportedConnectorError):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, InvalidCredentialsError):
        return HTTPException(status_code=401, detail=str(e))
    if isinstance(e, ConnectionTimeoutError):
        return HTTPException(status_code=408, detail=str(e))
    if isinstance(e, DatabaseUnavailableError):
        return HTTPException(status_code=503, detail=str(e))
    if isinstance(e, ConnectorError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# =========================
# POST /connections/test
# =========================
@router.post("/connections/test")
def test_connection_before_save(
    payload: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test connection credentials without saving. Returns status + DB version."""
    if not ConnectorFactory.is_supported(payload.db_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported database type: '{payload.db_type}'. "
                   f"Supported: {', '.join(ConnectorFactory.supported_types())}"
        )

    svc = ConnectionService(db)
    result = svc.test_connection_params(
        host=payload.host,
        port=payload.port,
        database=payload.database or "",
        username=payload.username,
        password=payload.password,
        db_type=payload.db_type,
        account=payload.account,
        warehouse=payload.warehouse,
        role=payload.role,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("detail", "Connection failed"))

    return result  # { "status": "ok", "version": "PostgreSQL 16.3..." }


# =========================
# POST /connections
# =========================
@router.post("/connections")
def create_connection(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new database connection. Tests connectivity first, then persists."""
    if not ConnectorFactory.is_supported(payload.db_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported database type: '{payload.db_type}'. "
                   f"Supported: {', '.join(ConnectorFactory.supported_types())}"
        )

    try:
        svc = ConnectionService(db)
        conn = svc.create_connection(
            user_id=current_user.id,
            name=payload.name,
            host=payload.host,
            port=payload.port,
            database=payload.database or "",
            username=payload.username,
            password=payload.password,
            db_type=payload.db_type,
            account=payload.account,
            warehouse=payload.warehouse,
            role=payload.role,
        )
        return {
            "id": conn.id,
            "status": "created",
            "name": conn.name,
            "db_type": conn.db_type,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_connector_error(e)


# =========================
# GET /connections
# =========================
@router.get("/connections")
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active connections for the current user."""
    svc = ConnectionService(db)
    connections = svc.list_connections(current_user.id)

    result = []
    for c in connections:
        result.append(ConnectionSummary(
            id=c.id,
            name=c.name,
            db_type=c.db_type,
            host=c.host or "",
            port=c.port or 0,
            database=c.database or "",
            status="active" if c.is_active else "inactive",
            created_at=c.created_at.isoformat() if c.created_at else None,
            last_synced=c.last_synced.isoformat() if c.last_synced else None,
        ))

    return {"connections": result}


# =========================
# DELETE /connections/:id
# =========================
@router.delete("/connections/{connection_id}")
def delete_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConnectionService(db)
    deleted = svc.delete_connection(connection_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"status": "deleted"}


# =========================
# POST /connections/:id/test
# =========================
@router.post("/connections/{connection_id}/test")
def test_saved_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-test an existing saved connection."""
    svc = ConnectionService(db)
    conn = svc.get_connection(connection_id, current_user.id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        engine = svc.get_engine(connection_id, current_user.id)
        from sqlalchemy import text
        with engine.connect() as c:
            c.execute(text("SELECT 1"))

        from datetime import datetime
        conn.last_synced = datetime.utcnow()
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")


# =========================
# POST /connections/:id/sync
# =========================
@router.post("/connections/{connection_id}/sync")
def sync_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Synchronous schema sync — extracts all schemas, tables, columns, relationships
    from the external database and stores them in the internal metadata tables.
    """
    svc = ConnectionService(db)
    conn = svc.get_connection(connection_id, current_user.id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        stats = svc.sync_schema(connection_id, current_user.id)
        return {"status": "synced", **stats}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# =========================
# GET /connections/:id/status
# =========================
@router.get("/connections/{connection_id}/status")
def get_connection_status(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ConnectionService(db)
    conn = svc.get_connection(connection_id, current_user.id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {
        "id": conn.id,
        "name": conn.name,
        "db_type": conn.db_type,
        "host": conn.host,
        "port": conn.port,
        "database": conn.database,
        "status": "active" if conn.is_active else "inactive",
        "last_synced": conn.last_synced.isoformat() if conn.last_synced else None,
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
    }


# =========================
# GET /connections/:id/schemas
# =========================
@router.get("/connections/{connection_id}/schemas")
def get_schemas(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return list of schemas/databases for this connection (live query)."""
    from app.services.metadata_extraction_service import MetadataExtractionService

    svc = MetadataExtractionService(db)
    try:
        schemas = svc.get_schemas(connection_id, current_user.id)
        return {"schemas": schemas}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise _handle_connector_error(e)


# =========================
# GET /connections/:id/entities
# =========================
@router.get("/connections/{connection_id}/entities")
def get_entities(
    connection_id: int,
    schema: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return list of tables/collections for this connection (live query)."""
    from app.services.metadata_extraction_service import MetadataExtractionService

    svc = MetadataExtractionService(db)
    try:
        entities = svc.get_entities(connection_id, current_user.id, schema=schema)
        return {"entities": entities}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise _handle_connector_error(e)


# =========================
# GET /connections/:id/entities/:entityName/columns
# =========================
@router.get("/connections/{connection_id}/entities/{entity_name}/columns")
def get_entity_columns(
    connection_id: int,
    entity_name: str,
    schema: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return column metadata for a specific table/collection (live query)."""
    from app.services.metadata_extraction_service import MetadataExtractionService

    svc = MetadataExtractionService(db)
    try:
        columns = svc.get_columns(connection_id, current_user.id, entity_name, schema=schema)
        return {"entity_name": entity_name, "columns": columns}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise _handle_connector_error(e)


# =========================
# GET /connections/supported-types
# =========================
@router.get("/connections/supported-types")
def get_supported_types(
    current_user: User = Depends(get_current_user),
):
    """Return list of all supported connector types."""
    return {"supported_types": ConnectorFactory.supported_types()}
