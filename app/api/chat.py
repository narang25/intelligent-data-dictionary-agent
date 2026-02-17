from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import ChatRequest, ChatResponse, SQLResult
from app.api.dependencies import get_db, get_current_user
from app.domain.models import User
from app.services.ai_service import AIService
from app.services.chat_service import ChatService
from app.core.database import engine

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        ai_service = AIService()
        chat_service = ChatService(engine, db, ai_service)

        result = chat_service.ask(request.question)

        if result.get("mode") == "sql":
            return ChatResponse(
                session_id=result["session_id"],
                mode=result["mode"],
                answer=result["answer"],
                sql=result.get("sql"),
                explanation=result.get("explanation"),
                result=SQLResult(
                    columns=result["result"]["columns"],
                    rows=result["result"]["rows"]
                ) if result.get("result") else None
            )

        return ChatResponse(
            session_id=result["session_id"],
            mode=result["mode"],
            answer=result["answer"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
