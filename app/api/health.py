from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import engine
import redis
import os

router = APIRouter()


@router.get("/health")
def health_check():

    status = {
        "api": "ok",
        "database": "unknown",
        "redis": "unknown"
    }

    # Check DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception:
        status["database"] = "error"

    # Check Redis
    try:
        r = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )
        r.ping()
        status["redis"] = "ok"
    except Exception:
        status["redis"] = "error"

    overall = (
        "ok"
        if status["database"] == "ok"
        and status["redis"] == "ok"
        else "degraded"
    )

    return {
        "status": overall,
        "services": status
    }
