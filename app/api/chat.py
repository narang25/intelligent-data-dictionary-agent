from fastapi import APIRouter
from dotenv import load_dotenv
from app.core.database import engine, SessionLocal
from app.services.ai_service import AIService
from app.services.chat_service import ChatService
from app.api.schemas import ChatRequest, ChatResponse

load_dotenv()

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):

    session = SessionLocal()
    ai_service = AIService()

    chat_service = ChatService(engine, session, ai_service)

    answer = chat_service.ask(request.question)

    return ChatResponse(answer=answer)

from app.tasks.ingestion_tasks import run_auto_documentation_task

@router.post("/admin/run-auto-doc")
def run_auto_doc():
    task = run_auto_documentation_task.delay()
    return {"task_id": task.id}
