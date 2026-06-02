from celery import Celery
import os

celery_app = Celery(
    "jarvis_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=["app.tasks.ingestion_tasks", "app.tasks.schema_watch_tasks"]
)

# Celery Beat schedule for Feature 1 — Schema Sync
celery_app.conf.beat_schedule = {
    "check-schema-drift-every-5-min": {
        "task": "schema_watch.check_all_connections",
        "schedule": 300.0,  # every 5 minutes
    },
}
celery_app.conf.timezone = "UTC"
