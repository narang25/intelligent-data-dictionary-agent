"""
AI Analysis API — database-level and table-level AI analysis, batch documentation.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.api.schemas import (
    AIAnalysisRequest, DatabaseAnalysisResponse, TableAnalysisResponse,
)
from app.domain.models import (
    User, DatabaseConnection, Schema, Table, ColumnModel, AIAnalysisCache,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/v1/connections", tags=["analysis"])


def _get_connection_or_404(db, connection_id, user_id):
    conn = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=user_id, is_active=True)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn


@router.post("/{connection_id}/ai/analyze", response_model=DatabaseAnalysisResponse)
def analyze_database(
    connection_id: int,
    payload: AIAnalysisRequest = AIAnalysisRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI analysis of the full database schema: domain, model type, entity groups."""
    conn = _get_connection_or_404(db, connection_id, current_user.id)

    # Determine analysis type for cache
    analysis_type = "overview_enhanced" if payload.enhanced else "overview_quick"

    # Check cache
    if not payload.force_refresh:
        cached = (
            db.query(AIAnalysisCache)
            .filter_by(connection_id=connection_id, entity_type="database", analysis_type=analysis_type)
            .first()
        )
        if cached:
            data = json.loads(cached.result_json)
            data["cached"] = True
            return DatabaseAnalysisResponse(**data)

    # Build schema context
    context_lines = []
    for schema_obj in conn.schemas:
        for table in schema_obj.tables:
            if payload.enhanced:
                cols = ", ".join(
                    [f"{c.name} ({c.data_type}{'|PK' if c.is_primary_key else ''}{'|FK' if c.is_foreign_key else ''})"
                     for c in table.columns]
                )
                context_lines.append(f"Table: {schema_obj.name}.{table.name} [{table.row_count or '?'} rows] — Columns: {cols}")
            else:
                # Minimal context to save tokens
                context_lines.append(f"Table: {schema_obj.name}.{table.name} [{table.row_count or '?'} rows]")

    schema_context = "\n".join(context_lines)

    if not schema_context:
        raise HTTPException(status_code=400, detail="No schema data found. Run sync first.")

    ai = AIService()
    
    if payload.enhanced:
        system_prompt = """You are a senior enterprise data architect. Analyze the database schema and return a JSON object with:
{
  "business_purpose": "string — what business domain this database serves",
  "domain": "string — industry/domain (e.g., retail, finance, healthcare)",
  "model_type": "string — OLTP or OLAP or hybrid",
  "architecture_observations": ["list of architectural observations"],
  "key_entity_groups": ["list of main entity groups/subjects"]
}
Return ONLY valid JSON, no markdown fences."""
    else:
        system_prompt = """You are a senior data architect. Analyze the provided table names and return a JSON object with:
{
  "business_purpose": "A detailed 4-5 sentence paragraph explaining what this database is used for, the key business domains it covers, who would use it, the types of workflows it supports, and how different parts of the schema relate to each other.",
  "suggested_questions": ["A specific analytical question about the data", "Another insightful question a business user would ask", "A third question about data quality or trends"],
  "key_tables": ["table1_name", "table2_name", "table3_name"]
}
Return ONLY valid JSON, no markdown fences."""

    user_prompt = f"Database: {conn.name}\nSchema:\n{schema_context}"

    response = ai.generate(system_prompt, user_prompt, json_mode=True)

    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        result = {
            "business_purpose": response,
            "suggested_questions": [],
            "key_tables": [],
            "domain": "unknown",
            "model_type": "unknown",
            "architecture_observations": [],
            "key_entity_groups": [],
        }

    # Cache result
    cache_entry = AIAnalysisCache(
        connection_id=connection_id,
        entity_type="database",
        entity_name=conn.name,
        analysis_type=analysis_type,
        result_json=json.dumps(result),
    )
    db.add(cache_entry)
    db.commit()

    result["cached"] = False
    return DatabaseAnalysisResponse(**result)


@router.post("/{connection_id}/tables/{table_name}/ai/analyze", response_model=TableAnalysisResponse)
def analyze_table(
    connection_id: int,
    table_name: str,
    payload: AIAnalysisRequest = AIAnalysisRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI analysis of a specific table: business context, insights, recommendations."""
    conn = _get_connection_or_404(db, connection_id, current_user.id)

    # Check cache
    if not payload.force_refresh:
        cached = (
            db.query(AIAnalysisCache)
            .filter_by(connection_id=connection_id, entity_type="table",
                       entity_name=table_name, analysis_type="overview")
            .first()
        )
        if cached:
            data = json.loads(cached.result_json)
            data["table_name"] = table_name
            data["cached"] = True
            return TableAnalysisResponse(**data)

    # Find the table
    schema_ids = [s.id for s in conn.schemas]
    table = (
        db.query(Table)
        .filter(Table.schema_id.in_(schema_ids), Table.name == table_name)
        .first()
    )
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    cols_desc = "\n".join([
        f"  - {c.name} ({c.data_type}, nullable={c.is_nullable}, PK={c.is_primary_key}, FK={c.is_foreign_key})"
        for c in table.columns
    ])
    rels = "\n".join([
        f"  - {r.source_column} → {r.target_table}.{r.target_column}"
        for r in table.relationships
    ]) or "  None"

    ai = AIService()
    system_prompt = """You are a senior enterprise data architect. Analyze this table and return a JSON object with:
{
  "business_context": "string — what this table represents in business terms",
  "key_insights": ["list of important observations about this table"],
  "recommendations": ["list of recommendations for improving this table"]
}
Return ONLY valid JSON, no markdown fences."""

    user_prompt = f"""Table: {table.schema.name}.{table.name}
Row count: {table.row_count or 'unknown'}
Columns:
{cols_desc}
Relationships:
{rels}"""

    response = ai.generate(system_prompt, user_prompt, json_mode=True)

    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        result = {
            "business_context": response,
            "key_insights": [],
            "recommendations": [],
        }

    # Cache
    cache_entry = AIAnalysisCache(
        connection_id=connection_id,
        entity_type="table",
        entity_name=table_name,
        analysis_type="overview",
        result_json=json.dumps(result),
    )
    db.add(cache_entry)
    db.commit()

    result["table_name"] = table_name
    result["cached"] = False
    return TableAnalysisResponse(**result)


@router.post("/{connection_id}/ai/generate-docs")
def trigger_batch_documentation(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger batch AI documentation generation (Celery task)."""
    conn = _get_connection_or_404(db, connection_id, current_user.id)

    from app.domain.models import Documentation, Table, Embedding
    schema_ids = [s.id for s in conn.schemas]
    table_ids = [t.id for t in db.query(Table.id).filter(Table.schema_id.in_(schema_ids)).all()]
    
    if table_ids:
        db.query(Documentation).filter(
            Documentation.entity_type == "table",
            Documentation.entity_id.in_(table_ids)
        ).delete(synchronize_session=False)
        
        db.query(Embedding).filter(
            Embedding.entity_type == "table",
            Embedding.entity_id.in_(table_ids)
        ).delete(synchronize_session=False)
        
        db.commit()

    from app.tasks.ingestion_tasks import run_batch_documentation_task
    task = run_batch_documentation_task.apply_async(args=[connection_id, current_user.id], queue="celery")

    return {"status": "queued", "task_id": str(task.id)}


@router.get("/{connection_id}/ai/generate-docs/status")
def batch_documentation_status(
    connection_id: int,
    task_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check batch documentation job status."""
    if task_id:
        from app.core.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        return {"task_id": task_id, "status": result.status, "result": result.result}

    # Count tables with vs without AI descriptions
    conn = _get_connection_or_404(db, connection_id, current_user.id)
    schema_ids = [s.id for s in conn.schemas]
    
    if not schema_ids:
        return {"total_tables": 0, "documented": 0, "remaining": 0}
        
    table_ids = [t.id for t in db.query(Table.id).filter(Table.schema_id.in_(schema_ids)).all()]
    total = len(table_ids)
    
    if not table_ids:
        cached = 0
    else:
        from app.domain.models import Documentation
        cached = (
            db.query(Documentation)
            .filter(Documentation.entity_type == "table", Documentation.entity_id.in_(table_ids))
            .count()
        )
    return {"total_tables": total, "documented": cached, "remaining": total - cached}
