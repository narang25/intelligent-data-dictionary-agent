"""CRUD API for collaborative annotations on tables and columns."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User, Annotation

router = APIRouter(prefix="/v1", tags=["annotations"])


class AnnotationCreate(BaseModel):
    table_name: str
    column_name: Optional[str] = None
    content: str


class AnnotationUpdate(BaseModel):
    content: str


class AnnotationResponse(BaseModel):
    id: int
    table_name: str
    column_name: Optional[str] = None
    content: str
    author_id: int
    author_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@router.get("/annotations", response_model=List[AnnotationResponse])
def list_annotations(
    table_name: Optional[str] = None,
    column_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Annotation)
    if table_name:
        q = q.filter(Annotation.table_name == table_name)
    if column_name:
        q = q.filter(Annotation.column_name == column_name)
    annotations = q.order_by(Annotation.created_at.desc()).all()
    return [
        AnnotationResponse(
            id=a.id, table_name=a.table_name, column_name=a.column_name,
            content=a.content, author_id=a.author_id,
            author_email=a.author.email if a.author else None,
            created_at=a.created_at, updated_at=a.updated_at,
        ) for a in annotations
    ]


@router.post("/annotations", response_model=AnnotationResponse)
def create_annotation(
    payload: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ann = Annotation(
        table_name=payload.table_name,
        column_name=payload.column_name,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return AnnotationResponse(
        id=ann.id, table_name=ann.table_name, column_name=ann.column_name,
        content=ann.content, author_id=ann.author_id,
        author_email=current_user.email,
        created_at=ann.created_at, updated_at=ann.updated_at,
    )


@router.put("/annotations/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(
    annotation_id: int,
    payload: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ann = db.query(Annotation).filter_by(id=annotation_id).first()
    if not ann:
        raise HTTPException(404, "Annotation not found")
    if ann.author_id != current_user.id:
        raise HTTPException(403, "Can only edit your own annotations")
    ann.content = payload.content
    db.commit()
    db.refresh(ann)
    return AnnotationResponse(
        id=ann.id, table_name=ann.table_name, column_name=ann.column_name,
        content=ann.content, author_id=ann.author_id,
        author_email=current_user.email,
        created_at=ann.created_at, updated_at=ann.updated_at,
    )


@router.delete("/annotations/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ann = db.query(Annotation).filter_by(id=annotation_id).first()
    if not ann:
        raise HTTPException(404, "Annotation not found")
    if ann.author_id != current_user.id:
        raise HTTPException(403, "Can only delete your own annotations")
    db.delete(ann)
    db.commit()
    return {"status": "deleted"}
