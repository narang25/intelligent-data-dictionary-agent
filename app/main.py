import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.connections import router as connections_router
from app.api.dashboard import router as dashboard_router
from app.api.tables import router as tables_router
from app.api.analysis import router as analysis_router
from app.api.quality import router as quality_router
from app.api.export import router as export_router
from app.api.explain import router as explain_router
from app.api.annotations import router as annotations_router
from app.api.lineage import router as lineage_router
from app.api.alerts import router as alerts_router
from app.api.guardrails import router as guardrails_router

from app.core.database import engine
from app.domain.models import Base

# Enable pgvector extension (required for embeddings)
pgvector_available = False
try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✅ pgvector extension enabled")
        pgvector_available = True
except Exception as e:
    print(f"⚠️ Could not enable pgvector: {e}")

# Create all tables. If pgvector is not available, skip the embeddings table.
from app.domain.models import Embedding
if pgvector_available:
    Base.metadata.create_all(bind=engine)
else:
    # Create all tables except the ones that require pgvector
    tables_to_create = [
        t for t in Base.metadata.sorted_tables
        if t.name != Embedding.__tablename__
    ]
    Base.metadata.create_all(bind=engine, tables=tables_to_create)
    print("⚠️ Skipped 'embeddings' table (requires pgvector). Core features still work.")

app = FastAPI(title="Intelligent Data Dictionary Agent", version="2.0.0")

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

# Legacy routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(health_router)

# New v1 API routers
app.include_router(connections_router)
app.include_router(dashboard_router)
app.include_router(tables_router)
app.include_router(analysis_router)
app.include_router(quality_router)
app.include_router(export_router)
app.include_router(explain_router)
app.include_router(annotations_router)
app.include_router(lineage_router)
app.include_router(alerts_router)
app.include_router(guardrails_router)


@app.get("/health")
def root():
    return {"message": "JARVIS v2.0 — AI Data Catalog running"}
