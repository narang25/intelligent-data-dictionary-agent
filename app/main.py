from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.auth import router as auth_router

from app.core.database import engine
from app.domain.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Intelligent Data Dictionary Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {"message": "JARVIS running"}
