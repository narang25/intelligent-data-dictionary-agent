"""
Dashboard API — overview metrics for a database connection.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_db, get_current_user
from app.api.schemas import OverviewResponse
from app.domain.models import (
    User, DatabaseConnection, Schema, Table, ColumnModel, Relationship,
)

router = APIRouter(prefix="/v1/connections", tags=["dashboard"])


@router.get("/{connection_id}/overview", response_model=OverviewResponse)
def get_overview(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """High-level database metrics: table count, column count, total rows, relationships."""
    conn = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    schema_ids = [s.id for s in conn.schemas]
    if not schema_ids:
        return OverviewResponse(
            total_tables=0, total_columns=0, total_rows=0,
            total_relationships=0, schemas=[],
        )

    total_tables = db.query(func.count(Table.id)).filter(Table.schema_id.in_(schema_ids)).scalar() or 0

    total_columns = (
        db.query(func.count(ColumnModel.id))
        .join(Table, ColumnModel.table_id == Table.id)
        .filter(Table.schema_id.in_(schema_ids))
        .scalar() or 0
    )

    total_rows = (
        db.query(func.coalesce(func.sum(Table.row_count), 0))
        .filter(Table.schema_id.in_(schema_ids))
        .scalar() or 0
    )

    total_relationships = (
        db.query(func.count(Relationship.id))
        .join(Table, Relationship.table_id == Table.id)
        .filter(Table.schema_id.in_(schema_ids))
        .scalar() or 0
    )

    schema_names = [s.name for s in conn.schemas]

    return OverviewResponse(
        total_tables=total_tables,
        total_columns=total_columns,
        total_rows=int(total_rows),
        total_relationships=total_relationships,
        schemas=schema_names,
    )
