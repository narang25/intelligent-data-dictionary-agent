from sentence_transformers import SentenceTransformer
from app.domain.models import Embedding


class EmbeddingService:

    def __init__(self, session):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.session = session

    def generate_embedding(self, text: str):
        return self.model.encode(text).tolist()

    def store_embedding(self, entity_type: str, entity_id: int, text: str):

        vector = self.generate_embedding(text)

        embedding = Embedding(
            entity_type=entity_type,
            entity_id=entity_id,
            vector=vector
        )

        self.session.add(embedding)
        self.session.commit()

        return vector
