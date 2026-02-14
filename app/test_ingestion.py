import os
from dotenv import load_dotenv
from app.core.database import SessionLocal
from app.services.schema_ingestion_service import SchemaIngestionService

load_dotenv()

session = SessionLocal()

service = SchemaIngestionService(
    db_url=os.getenv("DATABASE_URL"),
    session=session
)

service.ingest()
