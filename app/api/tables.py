"""
Tables API — list, detail, columns, sample data for a connection's tables.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.dependencies import get_db, get_current_user
from app.api.schemas import (
    TableListResponse, TableSummary, TableDetail, ColumnInfo,
    RelationshipInfo, SampleDataResponse,
)
from app.domain.models import (
    User, DatabaseConnection, Schema, Table, ColumnModel, Relationship,
)
from app.services.connection_service import ConnectionService

router = APIRouter(prefix="/v1/connections", tags=["tables"])


@router.get("/{connection_id}/tables", response_model=TableListResponse)
def list_tables(
    connection_id: int,
    search: str = Query("", description="Search table names"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn_obj = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn_obj:
        raise HTTPException(status_code=404, detail="Connection not found")

    schema_ids = [s.id for s in conn_obj.schemas]
    if not schema_ids:
        return TableListResponse(tables=[], total=0)

    query = db.query(Table).filter(Table.schema_id.in_(schema_ids))
    if search:
        query = query.filter(Table.name.ilike(f"%{search}%"))

    total = query.count()
    tables = query.order_by(Table.name).offset((page - 1) * per_page).limit(per_page).all()

    summaries = []
    for t in tables:
        schema_name = t.schema.name if t.schema else ""
        summaries.append(TableSummary(
            name=t.name,
            schema_name=schema_name,
            column_count=len(t.columns),
            row_count=t.row_count,
            relationship_count=len(t.relationships),
        ))

    return TableListResponse(tables=summaries, total=total)


@router.get("/{connection_id}/tables/{table_name}", response_model=TableDetail)
def get_table_detail(
    connection_id: int,
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn_obj = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn_obj:
        raise HTTPException(status_code=404, detail="Connection not found")

    schema_ids = [s.id for s in conn_obj.schemas]
    table = (
        db.query(Table)
        .filter(Table.schema_id.in_(schema_ids), Table.name == table_name)
        .first()
    )
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    columns = [
        ColumnInfo(
            name=c.name,
            data_type=c.data_type,
            is_nullable=c.is_nullable,
            is_primary_key=c.is_primary_key or False,
            is_foreign_key=c.is_foreign_key or False,
            ai_description=c.ai_description,
        )
        for c in table.columns
    ]

    relationships = [
        RelationshipInfo(
            source_table=r.source_table,
            source_column=r.source_column,
            target_table=r.target_table,
            target_column=r.target_column,
        )
        for r in table.relationships
    ]

    return TableDetail(
        name=table.name,
        schema_name=table.schema.name if table.schema else "",
        row_count=table.row_count,
        columns=columns,
        relationships=relationships,
    )


@router.get("/{connection_id}/tables/{table_name}/sample", response_model=SampleDataResponse)
def get_sample_data(
    connection_id: int,
    table_name: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query(None),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch sample rows from the external database."""
    conn_obj = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn_obj:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Find schema name for this table
    schema_ids = [s.id for s in conn_obj.schemas]
    table = (
        db.query(Table)
        .filter(Table.schema_id.in_(schema_ids), Table.name == table_name)
        .first()
    )
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    schema_name = table.schema.name if table.schema else "public"

    try:
        svc = ConnectionService(db)
        engine = svc.get_engine(connection_id, current_user.id)

        order_clause = ""
        if sort_by:
            order_clause = f'ORDER BY "{sort_by}" {sort_order}'

        query = f'SELECT * FROM "{schema_name}"."{table_name}" {order_clause} LIMIT :limit OFFSET :offset'

        with engine.connect() as ext_conn:
            result = ext_conn.execute(text(query), {"limit": limit, "offset": offset})
            columns = list(result.keys())
            rows = []
            for row in result:
                rows.append([str(v) if v is not None else None for v in row])

        return SampleDataResponse(
            columns=columns,
            rows=rows,
            total_rows=table.row_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sample data: {str(e)}")
