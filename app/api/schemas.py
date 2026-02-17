from pydantic import BaseModel, EmailStr
from typing import Optional, List


# =========================
# Chat Schemas
# =========================
class ChatRequest(BaseModel):
    question: str


class SQLResult(BaseModel):
    columns: List[str]
    rows: List[List[str]]


class ChatResponse(BaseModel):
    session_id: int
    mode: str
    answer: str
    sql: Optional[str] = None
    explanation: Optional[str] = None
    result: Optional[SQLResult] = None


# =========================
# Auth Schemas
# =========================
class UserSignup(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
