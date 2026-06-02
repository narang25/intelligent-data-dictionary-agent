"""API for anomaly alerts."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User, AnomalyAlert

router = APIRouter(prefix="/v1", tags=["alerts"])


class AlertResponse(BaseModel):
    id: int
    table_name: str
    column_name: str
    alert_type: str
    message: str
    severity: str
    dismissed: bool
    created_at: Optional[datetime] = None


@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AnomalyAlert)
    if active_only:
        q = q.filter(AnomalyAlert.dismissed == False)
    alerts = q.order_by(AnomalyAlert.created_at.desc()).all()
    return [
        AlertResponse(
            id=a.id, table_name=a.table_name, column_name=a.column_name,
            alert_type=a.alert_type, message=a.message, severity=a.severity,
            dismissed=a.dismissed, created_at=a.created_at,
        ) for a in alerts
    ]


@router.post("/alerts/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(AnomalyAlert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.dismissed = True
    db.commit()
    return {"status": "dismissed"}
