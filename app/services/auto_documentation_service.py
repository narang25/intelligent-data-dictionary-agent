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
        context = {
            "table_name": table.name,
            "columns": []
        }
        for column in table.columns:
            context["columns"].append({
                "name": column.name,
                "data_type": column.data_type,
                "is_nullable": column.is_nullable,
                "is_primary_key": column.is_primary_key,
                "is_foreign_key": column.is_foreign_key
            })
        return json.dumps(context, indent=2)

    def generate_documentation(self, table):

        context = self.generate_table_context(table)

        system_prompt = """
You are a Staff-Level Enterprise Data Architect. Your task is to generate 99.9% accurate, strictly schema-grounded documentation for database tables. 

CRITICAL INSTRUCTIONS:
1. NO HALLUCINATIONS: Do not guess business meaning if the column names do not obviously imply it.
2. SCHEMA GROUNDING: You must explicitly mention Primary Keys (PK) and Foreign Keys (FK) in your summary. Rely ONLY on the provided schema metadata.
3. CONTEXTUAL ACCURACY: If a table looks like a join table, state that it is a many-to-many join table. If a table looks like a dimension table or fact table, state that.
4. JSON FORMAT ONLY: You MUST output exactly and only valid JSON matching this schema:
{
  "summary": "Precise 2-sentence technical summary of the table's role.",
  "business_purpose": "The exact business function this table serves, based STRICTLY on its name and columns.",
  "data_quality_notes": "Observations on nullability or constraints based ONLY on the metadata.",
  "recommended_usage": "When and how analysts should use this table."
}
"""

        user_prompt = f"Strict Schema Metadata:\n{context}"

        response = self.ai_service.generate(system_prompt, user_prompt, json_mode=True)

        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1].replace("json", "").strip()

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

    def run(self, connection_id=None):

        query = self.session.query(Table)
        if connection_id:
            from app.domain.models import Schema
            query = query.join(Schema).filter(Schema.connection_id == connection_id)
            
        tables = query.all()

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
                connection_id=str(connection_id) if connection_id else None,
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
                connection_id=str(connection_id) if connection_id else None,
                entity_type="table",
                entity_id=table.id,
                vector=embedding_vector
            )

            self.session.add(embedding_record)
            self.session.commit()

        print("Auto documentation pipeline completed.")
