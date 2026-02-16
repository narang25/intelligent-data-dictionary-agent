from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from app.core.database import engine, SessionLocal
from app.services.ai_service import AIService
from app.services.chat_service import ChatService
from app.api.schemas import ChatRequest, ChatResponse, SQLResult
from app.tasks.ingestion_tasks import run_auto_documentation_task

load_dotenv()

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):

    session = SessionLocal()

    try:
        ai_service = AIService()
        chat_service = ChatService(engine, session, ai_service)

        result = chat_service.ask(request.question)
        print("SQL RESULT:", result)


        # 🔹 SQL MODE
        if result.get("mode") == "sql":

            return ChatResponse(
                session_id=result["session_id"],
                mode=result["mode"],
                answer=result["answer"],  # ✅ FIXED
                sql=result.get("sql"),
                explanation=result.get("explanation"),
                result=SQLResult(
                    columns=result["result"]["columns"],
                    rows=result["result"]["rows"]
                ) if result.get("result") else None
            )

        # 🔹 RAG MODE
        return ChatResponse(
            session_id=result["session_id"],
            mode=result["mode"],
            answer=result["answer"]
        )

    except Exception as e:
        print("Chat Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        session.close()


@router.post("/admin/run-auto-doc")
def run_auto_doc():
    task = run_auto_documentation_task.delay()
    return {"task_id": task.id}
