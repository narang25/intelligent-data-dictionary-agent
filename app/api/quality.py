"""
Data Quality API — compute and retrieve quality scores for a connection's tables.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.dependencies import get_db, get_current_user
from app.api.schemas import QualityResponse, TableQualityScore
from app.domain.models import (
    User, DatabaseConnection, Schema, Table, ColumnModel, DataQualityScore,
)
from app.services.connection_service import ConnectionService

router = APIRouter(prefix="/v1/connections", tags=["quality"])


@router.get("/{connection_id}/quality", response_model=QualityResponse)
def get_quality_scores(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cached quality scores."""
    conn = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    scores = (
        db.query(DataQualityScore)
        .filter_by(connection_id=connection_id)
        .all()
    )

    table_scores = [
        TableQualityScore(
            table_name=s.table_name,
            completeness=s.completeness,
            uniqueness=s.uniqueness,
            overall_score=s.overall_score,
            details=json.loads(s.details_json) if s.details_json else None,
        )
        for s in scores
    ]

    overall = sum(s.overall_score for s in scores) / len(scores) if scores else 0.0

    return QualityResponse(
        connection_id=connection_id,
        overall_score=round(overall, 2),
        tables=table_scores,
    )


@router.post("/{connection_id}/quality/analyze", response_model=QualityResponse)
def analyze_quality(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute quality metrics for all tables in the connection."""
    conn = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    svc = ConnectionService(db)
    engine = svc.get_engine(connection_id, current_user.id)

    # Clear existing scores
    db.query(DataQualityScore).filter_by(connection_id=connection_id).delete()

    table_scores = []

    for schema_obj in conn.schemas:
        for table in schema_obj.tables:
            schema_name = schema_obj.name
            table_name = table.name
            fqn = f'"{schema_name}"."{table_name}"'

            try:
                with engine.connect() as ext_conn:
                    # Row count
                    total_rows = ext_conn.execute(text(f"SELECT COUNT(*) FROM {fqn}")).scalar() or 0

                    if total_rows == 0:
                        score = DataQualityScore(
                            connection_id=connection_id,
                            table_name=f"{schema_name}.{table_name}",
                            completeness=0.0,
                            uniqueness=0.0,
                            overall_score=0.0,
                            details_json=json.dumps({"note": "empty table"}),
                        )
                        db.add(score)
                        table_scores.append(TableQualityScore(
                            table_name=f"{schema_name}.{table_name}",
                            completeness=0.0, uniqueness=0.0, overall_score=0.0,
                            details={"note": "empty table"},
                        ))
                        continue

                    # Per-column metrics
                    column_details = []
                    completeness_values = []
                    uniqueness_values = []

                    for col in table.columns:
                        col_name = f'"{col.name}"'

                        null_count = ext_conn.execute(
                            text(f"SELECT COUNT(*) FROM {fqn} WHERE {col_name} IS NULL")
                        ).scalar() or 0

                        distinct_count = ext_conn.execute(
                            text(f"SELECT COUNT(DISTINCT {col_name}) FROM {fqn}")
                        ).scalar() or 0

                        completeness = ((total_rows - null_count) / total_rows) * 100
                        uniqueness = (distinct_count / total_rows) * 100 if total_rows > 0 else 0

                        completeness_values.append(completeness)
                        uniqueness_values.append(uniqueness)

                        column_details.append({
                            "column": col.name,
                            "null_count": null_count,
                            "distinct_count": distinct_count,
                            "completeness": round(completeness, 2),
                            "uniqueness": round(uniqueness, 2),
                            "is_primary_key": col.is_primary_key or False,
                        })

                    avg_completeness = sum(completeness_values) / len(completeness_values) if completeness_values else 0
                    avg_uniqueness = sum(uniqueness_values) / len(uniqueness_values) if uniqueness_values else 0
                    overall = (avg_completeness * 0.6 + avg_uniqueness * 0.4)

                    score = DataQualityScore(
                        connection_id=connection_id,
                        table_name=f"{schema_name}.{table_name}",
                        completeness=round(avg_completeness, 2),
                        uniqueness=round(avg_uniqueness, 2),
                        overall_score=round(overall, 2),
                        details_json=json.dumps(column_details),
                    )
                    db.add(score)
                    table_scores.append(TableQualityScore(
                        table_name=f"{schema_name}.{table_name}",
                        completeness=round(avg_completeness, 2),
                        uniqueness=round(avg_uniqueness, 2),
                        overall_score=round(overall, 2),
                        details=column_details,
                    ))

            except Exception as e:
                table_scores.append(TableQualityScore(
                    table_name=f"{schema_name}.{table_name}",
                    completeness=0.0, uniqueness=0.0, overall_score=0.0,
                    details={"error": str(e)},
                ))

    db.commit()

    overall_db = sum(s.overall_score for s in table_scores) / len(table_scores) if table_scores else 0.0

    return QualityResponse(
        connection_id=connection_id,
        overall_score=round(overall_db, 2),
        tables=table_scores,
    )
