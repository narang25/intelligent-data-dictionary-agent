import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.auth import router as auth_router

from app.core.database import engine
from app.domain.models import Base

# Enable pgvector extension (required for embeddings)
try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✅ pgvector extension enabled")
except Exception as e:
    print(f"⚠️ Could not enable pgvector: {e}")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Intelligent Data Dictionary Agent")

# CORS - Get origins from environment + defaults
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [
    "http://localhost:5173",
    "http://localhost:80",
    "http://localhost",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:80",
    "http://127.0.0.1",
]
if cors_origins_env:
    cors_origins.extend([o.strip() for o in cors_origins_env.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
