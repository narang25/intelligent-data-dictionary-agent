from pydantic import BaseModel
from typing import Optional, List, Any


class ChatRequest(BaseModel):
    question: str


class SQLResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


class ChatResponse(BaseModel):
    session_id: int
    mode: str
    answer: str

    # Optional SQL fields
    sql: Optional[str] = None
    explanation: Optional[str] = None
    result: Optional[SQLResult] = None
