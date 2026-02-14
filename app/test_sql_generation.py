from dotenv import load_dotenv
from app.core.database import SessionLocal, engine
from app.services.ai_service import AIService
from app.services.sql_generation_service import SQLGenerationService, build_schema_context

load_dotenv()

session = SessionLocal()
ai_service = AIService()

sql_service = SQLGenerationService(ai_service)

schema_context = build_schema_context(session)

question = "Generate SQL to list all documentation records."

result = sql_service.generate_sql(schema_context, question)

print("\nParsed SQL Response:\n", result)

if "sql" in result:

    execution = sql_service.execute_safe_query(engine, result["sql"])

    print("\nExecution Result:\n", execution)
