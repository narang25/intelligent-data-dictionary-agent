from dotenv import load_dotenv
from app.core.database import SessionLocal
from app.services.ai_service import AIService
from app.services.auto_documentation_service import AutoDocumentationService

load_dotenv()

session = SessionLocal()
ai_service = AIService()

service = AutoDocumentationService(session, ai_service)

service.run()
