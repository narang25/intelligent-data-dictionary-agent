"""API for data lineage tracking."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User, ColumnLineage

router = APIRouter(prefix="/v1", tags=["lineage"])


class LineageEntry(BaseModel):
    id: int
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    transformation_expression: Optional[str] = None


class LineageCreate(BaseModel):
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    transformation_expression: Optional[str] = None


@router.get("/lineage/{table}/{column}", response_model=List[LineageEntry])
def get_lineage(
    table: str,
    column: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get lineage graph for a column — both upstream and downstream."""
    upstream = db.query(ColumnLineage).filter_by(target_table=table, target_column=column).all()
    downstream = db.query(ColumnLineage).filter_by(source_table=table, source_column=column).all()
    all_lineage = list(set(upstream + downstream))
    return [
        LineageEntry(
            id=l.id, source_table=l.source_table, source_column=l.source_column,
            target_table=l.target_table, target_column=l.target_column,
            transformation_expression=l.transformation_expression,
        ) for l in all_lineage
    ]


@router.post("/lineage", response_model=LineageEntry)
def create_lineage(
    payload: LineageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = ColumnLineage(
        source_table=payload.source_table,
        source_column=payload.source_column,
        target_table=payload.target_table,
        target_column=payload.target_column,
        transformation_expression=payload.transformation_expression,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return LineageEntry(
        id=entry.id, source_table=entry.source_table, source_column=entry.source_column,
        target_table=entry.target_table, target_column=entry.target_column,
        transformation_expression=entry.transformation_expression,
    )


@router.get("/lineage", response_model=List[LineageEntry])
def list_all_lineage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all lineage entries for the DAG visualization."""
    entries = db.query(ColumnLineage).all()
    return [
        LineageEntry(
            id=l.id, source_table=l.source_table, source_column=l.source_column,
            target_table=l.target_table, target_column=l.target_column,
            transformation_expression=l.transformation_expression,
        ) for l in entries
    ]
