"""API for role-based column permissions (query guardrails)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User, ColumnPermission

router = APIRouter(prefix="/v1", tags=["guardrails"])


class PermissionResponse(BaseModel):
    id: int
    role: str
    table_name: str
    column_name: str
    allow: bool


class PermissionCreate(BaseModel):
    role: str
    table_name: str
    column_name: str
    allow: bool = False


@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(ColumnPermission)
    if role:
        q = q.filter(ColumnPermission.role == role)
    perms = q.all()
    return [
        PermissionResponse(id=p.id, role=p.role, table_name=p.table_name,
                           column_name=p.column_name, allow=p.allow)
        for p in perms
    ]


@router.post("/permissions", response_model=PermissionResponse)
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = ColumnPermission(
        role=payload.role, table_name=payload.table_name,
        column_name=payload.column_name, allow=payload.allow,
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return PermissionResponse(id=perm.id, role=perm.role, table_name=perm.table_name,
                              column_name=perm.column_name, allow=perm.allow)


@router.delete("/permissions/{perm_id}")
def delete_permission(
    perm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(ColumnPermission).filter_by(id=perm_id).first()
    if not perm:
        raise HTTPException(404, "Permission not found")
    db.delete(perm)
    db.commit()
    return {"status": "deleted"}


@router.get("/permissions/restricted-columns")
def get_restricted_columns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all restricted columns for the current user's role (analyst by default)."""
    role = getattr(current_user, 'role', 'analyst') or 'analyst'
    restricted = db.query(ColumnPermission).filter_by(role=role, allow=False).all()
    return {
        "role": role,
        "restricted": [
            {"table_name": p.table_name, "column_name": p.column_name}
            for p in restricted
        ]
    }
