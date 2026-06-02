import json
import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.ai_service import AIService
from app.services.auto_documentation_service import AutoDocumentationService

logger = logging.getLogger(__name__)


@celery_app.task
def run_auto_documentation_task():
    """Legacy: generate docs for all tables in internal DB."""
    session = SessionLocal()
    ai_service = AIService()
    service = AutoDocumentationService(session, ai_service)
    service.run()
    session.close()
    return "Auto documentation completed"


@celery_app.task
def sync_connection_schema_task(connection_id: int, user_id: int):
    """Extract schema from an external DB connection."""
    from app.services.connection_service import ConnectionService
    session = SessionLocal()
    try:
        svc = ConnectionService(session)
        stats = svc.sync_schema(connection_id, user_id)
        return {"status": "completed", "stats": stats}
    except Exception as e:
        logger.error(f"Schema sync failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        session.close()


@celery_app.task
def run_batch_documentation_task(connection_id: int, user_id: int):
    """Generate high-accuracy AI documentation for all tables in a connection."""
    from app.domain.models import DatabaseConnection, Documentation, Embedding
    from app.services.auto_documentation_service import AutoDocumentationService
    from app.services.embedding_service import EmbeddingService
    
    session = SessionLocal()
    ai = AIService()
    embedding_svc = EmbeddingService(session)
    auto_doc_svc = AutoDocumentationService(session, ai)

    try:
        conn = session.query(DatabaseConnection).filter_by(id=connection_id).first()
        if not conn:
            return {"status": "failed", "error": "Connection not found"}

        documented = 0
        for schema_obj in conn.schemas:
            for table in schema_obj.tables:
                
                # Check for existing documentation to avoid duplicates
                existing_doc = (
                    session.query(Documentation)
                    .filter_by(entity_type="table", entity_id=table.id)
                    .first()
                )
                if existing_doc:
                    continue

                # Generate high-accuracy documentation
                doc_json = auto_doc_svc.generate_documentation(table)

                # Save documentation record
                doc_record = Documentation(
                    connection_id=str(connection_id),
                    entity_type="table",
                    entity_id=table.id,
                    description=json.dumps(doc_json)
                )
                session.add(doc_record)
                session.commit()

                # Generate and save embedding record
                embedding_vector = embedding_svc.generate_embedding(
                    json.dumps(doc_json)
                )
                embedding_record = Embedding(
                    connection_id=str(connection_id),
                    entity_type="table",
                    entity_id=table.id,
                    vector=embedding_vector
                )
                session.add(embedding_record)
                session.commit()
                
                documented += 1

        return {"status": "completed", "documented": documented}
    except Exception as e:
        logger.error(f"Batch documentation failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        session.close()

