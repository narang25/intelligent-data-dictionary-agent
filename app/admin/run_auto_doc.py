from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.domain.models import Documentation
from app.services.embedding_service import EmbeddingService
from app.services.vector_search_service import VectorSearchService
from app.services.ai_service import AIService

def run():

    print("🚀 Starting Auto Documentation Pipeline...")

    session = SessionLocal()
    embedding_service = EmbeddingService(session)
    ai_service = AIService()

    # Get all tables from all schemas (excluding system)
    query = """
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    AND table_type='BASE TABLE';
    """

    tables = session.execute(text(query)).fetchall()

    for schema, table in tables:

        print(f"📄 Documenting {schema}.{table}")

        # Get column info
        column_query = f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
        AND table_name = '{table}';
        """

        columns = session.execute(text(column_query)).fetchall()

        column_text = "\n".join(
            [f"- {col} ({dtype})" for col, dtype in columns]
        )

        system_prompt = """
        You are an enterprise data architect.
        Generate structured documentation in JSON format:
        {
            "summary": "",
            "business_purpose": "",
            "data_quality_notes": "",
            "recommended_usage": ""
        }
        """

        user_prompt = f"""
        Table: {schema}.{table}

        Columns:
        {column_text}
        """

        documentation_text = ai_service.generate(system_prompt, user_prompt)

        # Save documentation
        unique_entity_id = abs(hash(f"{schema}.{table}")) % (10**9)

        doc = Documentation(
            entity_type="table",
            entity_id=unique_entity_id,
            description=documentation_text
        )


        session.add(doc)
        session.commit()

        # Generate embedding
        vector = embedding_service.generate_embedding(documentation_text)

        # Store in embeddings table
        insert_vector = text("""
        INSERT INTO embeddings (entity_type, entity_id, vector)
        VALUES (:entity_type, :entity_id, :vector)
        ON CONFLICT (entity_type, entity_id)
        DO UPDATE SET vector = EXCLUDED.vector;
        """)

        session.execute(insert_vector, {
            "entity_type": "table",
            "entity_id": unique_entity_id,
            "vector": vector
        })

        session.commit()

    print("✅ Auto documentation completed.")

if __name__ == "__main__":
    run()
