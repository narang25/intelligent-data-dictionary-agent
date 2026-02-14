from app.domain.models import Table, Documentation, Embedding
from app.services.embedding_service import EmbeddingService
from sqlalchemy.orm import Session
import json


class AutoDocumentationService:

    def __init__(self, session: Session, ai_service):
        self.session = session
        self.ai_service = ai_service
        self.embedding_service = EmbeddingService(session)

    def generate_table_context(self, table):

        context = f"Table: {table.name}\nColumns:\n"

        for column in table.columns:
            context += f"- {column.name} ({column.data_type})\n"

        return context

    def generate_documentation(self, table):

        context = self.generate_table_context(table)

        system_prompt = """
You are a senior enterprise data architect.

Generate structured documentation in JSON format with:
- summary
- business_purpose
- data_quality_notes
- recommended_usage
"""

        user_prompt = f"""
Metadata:
{context}
"""

        response = self.ai_service.generate(system_prompt, user_prompt)

        clean_response = response.strip()

        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            clean_response = clean_response.replace("json", "").strip()

        try:
            parsed = json.loads(clean_response)
        except Exception:
            parsed = {
                "summary": response,
                "business_purpose": "",
                "data_quality_notes": "",
                "recommended_usage": ""
            }

        return parsed

    def run(self):

        tables = self.session.query(Table).all()

        for table in tables:

            # Skip if documentation already exists
            existing_doc = (
                self.session.query(Documentation)
                .filter_by(entity_type="table", entity_id=table.id)
                .first()
            )

            if existing_doc:
                continue

            doc_json = self.generate_documentation(table)

            doc_record = Documentation(
                entity_type="table",
                entity_id=table.id,
                description=json.dumps(doc_json)
            )

            self.session.add(doc_record)
            self.session.commit()

            # Generate embedding
            embedding_vector = self.embedding_service.generate_embedding(
                json.dumps(doc_json)
            )

            embedding_record = Embedding(
                entity_type="table",
                entity_id=table.id,
                vector=embedding_vector
            )

            self.session.add(embedding_record)
            self.session.commit()

        print("Auto documentation pipeline completed.")
