import os
from dotenv import load_dotenv
from app.core.database import SessionLocal
from app.services.ai_service import AIService
from app.services.documentation_service import DocumentationService
from app.domain.models import Table

load_dotenv()

session = SessionLocal()

ai_service = AIService()
doc_service = DocumentationService(ai_service, session)

table = session.query(Table).filter_by(name="documentation").first()

json_doc = doc_service.generate_table_documentation(table)

print("Generated JSON:\n", json_doc)

markdown = doc_service.generate_markdown(table, json_doc)

print("\nGenerated Markdown:\n")
print(markdown)

