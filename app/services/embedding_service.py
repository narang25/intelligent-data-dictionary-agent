from sentence_transformers import SentenceTransformer
from app.domain.models import Embedding
import os
import time


class EmbeddingService:
    _model = None  # Class-level cache

    def __init__(self, session):
        self.session = session
        if EmbeddingService._model is None:
            EmbeddingService._model = self._load_model()
        self.model = EmbeddingService._model

    def _load_model(self):
        """Load model with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Try to load from cache first
                model = SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2",
                    cache_folder="/app/models"
                )
                return model
            except Exception as e:
                print(f"Model load attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    # Final fallback - try without cache folder
                    try:
                        return SentenceTransformer("all-MiniLM-L6-v2")
                    except Exception as e2:
                        print(f"Final model load failed: {e2}")
                        raise

    def generate_embedding(self, text: str):
        return self.model.encode(text).tolist()

    def store_embedding(self, entity_type: str, entity_id: int, text: str, connection_id: str = None):

        vector = self.generate_embedding(text)

        embedding = Embedding(
            connection_id=connection_id,
            entity_type=entity_type,
            entity_id=entity_id,
            vector=vector
        )

        self.session.add(embedding)
        self.session.commit()

        return vector
