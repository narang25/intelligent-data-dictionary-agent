from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.ai_service import AIService
from app.services.auto_documentation_service import AutoDocumentationService


@celery_app.task
def run_auto_documentation_task():

    session = SessionLocal()
    ai_service = AIService()

    service = AutoDocumentationService(session, ai_service)

    service.run()

    session.close()

    return "Auto documentation completed"
