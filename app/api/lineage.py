"""API for data lineage tracking."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User, ColumnLineage, Relationship, Table, Schema

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
    connection_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all lineage entries for the DAG visualization."""
    
    # 1. Get manual lineage entries
    # Ideally, these would be filtered by connection_id too, but since they don't have it, we return all or filter by target table prefix if possible.
    # For now, return all manual entries.
    entries = db.query(ColumnLineage).all()
    
    result = [
        LineageEntry(
            id=l.id, source_table=l.source_table, source_column=l.source_column,
            target_table=l.target_table, target_column=l.target_column,
            transformation_expression=l.transformation_expression,
        ) for l in entries
    ]

    # 2. Get automated foreign keys (Relationships) for the active connection
    if connection_id:
        try:
            conn_id_int = int(connection_id)
            relationships = (
                db.query(Relationship)
                .join(Table, Relationship.table_id == Table.id)
                .join(Schema, Table.schema_id == Schema.id)
                .filter(Schema.connection_id == conn_id_int)
                .all()
            )
            
            # Start IDs for automated lineage high to avoid clashing with manual lineage IDs in the UI React keys
            auto_id_start = 1000000 
            
            for i, r in enumerate(relationships):
                # Ensure the table name has schema prefix if not already present
                src_tbl = r.source_table
                if "." not in src_tbl:
                    # In this DB we usually prefix with schema name. If it's not prefixed, try to prefix it
                    src_tbl_obj = db.query(Table).filter(Table.name == src_tbl).first()
                    if src_tbl_obj and src_tbl_obj.schema:
                        src_tbl = f"{src_tbl_obj.schema.name}.{src_tbl}"

                tgt_tbl = r.target_table
                if "." not in tgt_tbl:
                    # Target table is the one referenced by the foreign key.
                    # Try to resolve its schema.
                    tgt_tbl_obj = db.query(Table).filter(Table.name == tgt_tbl).first()
                    if tgt_tbl_obj and tgt_tbl_obj.schema:
                        tgt_tbl = f"{tgt_tbl_obj.schema.name}.{tgt_tbl}"

                result.append(
                    LineageEntry(
                        id=auto_id_start + i,
                        source_table=src_tbl,
                        source_column=r.source_column,
                        target_table=tgt_tbl,
                        target_column=r.target_column,
                        transformation_expression="Auto (Foreign Key)"
                    )
                )
        except Exception as e:
            print(f"Error fetching automated lineage: {e}")

    return result

@router.delete("/lineage/{entry_id}")
def delete_lineage(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a manual lineage entry by ID."""
    entry = db.query(ColumnLineage).filter(ColumnLineage.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Lineage entry not found")
    
    db.delete(entry)
    db.commit()
    return {"status": "success", "message": "Lineage entry deleted"}
