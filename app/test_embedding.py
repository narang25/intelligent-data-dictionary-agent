from app.core.database import SessionLocal
from app.services.embedding_service import EmbeddingService
from app.domain.models import Documentation

session = SessionLocal()

embedding_service = EmbeddingService(session)

docs = session.query(Documentation).all()

for doc in docs:
    embedding_service.store_embedding(
        entity_type=doc.entity_type,
        entity_id=doc.entity_id,
        text=doc.description
    )

print("Embeddings stored successfully!")
