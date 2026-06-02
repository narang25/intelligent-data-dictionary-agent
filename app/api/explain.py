"""
API router for SQL query explanation.
Accepts any SQL string, returns plain English explanation, performance risks, and optimized version.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.domain.models import User
from app.services.ai_service import AIService
from app.services.sql_generation_service import build_schema_context

router = APIRouter(prefix="/v1", tags=["explain"])


class ExplainRequest(BaseModel):
    sql: str


class ExplainResponse(BaseModel):
    explanation: str
    performance_risks: List[str]
    optimized_sql: Optional[str] = None


@router.post("/explain", response_model=ExplainResponse)
def explain_sql(
    payload: ExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explain a SQL query in plain English with performance analysis."""
    try:
        ai = AIService()
        schema_context = build_schema_context(db)

        system_prompt = """You are a senior database performance engineer and SQL expert.

Given a SQL query and the database schema context, return a JSON object with exactly these keys:
{
  "explanation": "A clear, plain English explanation of what this query does, step by step",
  "performance_risks": ["list of identified performance risks such as missing indexes, full table scans, N+1 patterns, cartesian products, etc."],
  "optimized_sql": "An optimized version of the query if improvements are possible, or null if the query is already optimal"
}

Be specific about:
- What data is being retrieved and from which tables
- How tables are joined and filtered
- What aggregations or transformations are applied
- Any potential performance bottlenecks

Return ONLY valid JSON."""

        user_prompt = f"""Schema Context:
{schema_context}

SQL Query to explain:
{payload.sql}
"""

        response = ai.generate(system_prompt, user_prompt, json_mode=True)

        import json
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
                "explanation": response,
                "performance_risks": [],
                "optimized_sql": None,
            }

        return ExplainResponse(
            explanation=result.get("explanation", "Could not generate explanation"),
            performance_risks=result.get("performance_risks", []),
            optimized_sql=result.get("optimized_sql"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
