"""
Export API — generate data dictionary exports in JSON, Markdown, HTML formats.
"""
import json
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.security import jwt, SECRET_KEY, ALGORITHM
from app.api.dependencies import get_db, get_current_user
from app.api.schemas import ExportRequest, ExportStatusResponse
from app.domain.models import (
    User, DatabaseConnection, Schema, Table, AIAnalysisCache, ExportJob,
)

router = APIRouter(prefix="/v1", tags=["export"])

EXPORT_DIR = "/tmp/jarvis_exports"


def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _build_dictionary_data(db, conn: DatabaseConnection):
    """Build structured data dictionary from stored metadata + AI cache."""
    data = {
        "database": conn.name,
        "host": conn.host,
        "db_type": conn.db_type,
        "exported_at": datetime.utcnow().isoformat(),
        "schemas": [],
    }

    for schema_obj in conn.schemas:
        schema_data = {"name": schema_obj.name, "tables": []}

        for table in schema_obj.tables:
            # Check for AI analysis cache
            ai_cache = (
                db.query(AIAnalysisCache)
                .filter_by(connection_id=conn.id, entity_type="table",
                           entity_name=table.name, analysis_type="overview")
                .first()
            )
            ai_analysis = json.loads(ai_cache.result_json) if ai_cache else None

            table_data = {
                "name": table.name,
                "row_count": table.row_count,
                "ai_analysis": ai_analysis,
                "columns": [
                    {
                        "name": c.name,
                        "data_type": c.data_type,
                        "is_nullable": c.is_nullable,
                        "is_primary_key": c.is_primary_key or False,
                        "is_foreign_key": c.is_foreign_key or False,
                        "ai_description": c.ai_description,
                    }
                    for c in table.columns
                ],
                "relationships": [
                    {
                        "source_column": r.source_column,
                        "target_table": r.target_table,
                        "target_column": r.target_column,
                    }
                    for r in table.relationships
                ],
            }
            schema_data["tables"].append(table_data)

        data["schemas"].append(schema_data)
    return data


def _export_json(data: dict, filepath: str):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _build_markdown_string(data: dict) -> str:
    lines = [f"# Data Dictionary: {data['database']}\n"]
    lines.append(f"**Host:** {data['host']}  ")
    lines.append(f"**Type:** {data['db_type']}  ")
    lines.append(f"**Exported:** {data['exported_at']}\n")

    for schema in data["schemas"]:
        lines.append(f"\n## Schema: {schema['name']}\n")

        for table in schema["tables"]:
            lines.append(f"\n### Table: {table['name']}\n")
            if table.get("row_count"):
                lines.append(f"**Rows:** {table['row_count']:,}\n")

            if table.get("ai_analysis"):
                ai = table["ai_analysis"]
                if ai.get("business_context"):
                    lines.append(f"\n> {ai['business_context']}\n")

            lines.append("\n| Column | Type | Nullable | PK | FK | Description |")
            lines.append("|--------|------|----------|----|----|-------------|")
            for col in table["columns"]:
                pk = "✓" if col["is_primary_key"] else ""
                fk = "✓" if col["is_foreign_key"] else ""
                desc = col.get("ai_description") or ""
                lines.append(
                    f"| {col['name']} | {col['data_type']} | {col['is_nullable']} | {pk} | {fk} | {desc} |"
                )

            if table["relationships"]:
                lines.append("\n**Relationships:**\n")
                for rel in table["relationships"]:
                    lines.append(f"- `{rel['source_column']}` → `{rel['target_table']}.{rel['target_column']}`")

    return "\n".join(lines)


def _export_markdown(data: dict, filepath: str):
    md_str = _build_markdown_string(data)
    with open(filepath, "w") as f:
        f.write(md_str)


def _build_html_string(data: dict) -> str:
    """Generate styled HTML data dictionary suitable for PDF generation."""
    
    html_parts = []
    html_parts.append(f"<h1>Data Dictionary: {data['database']}</h1>")
    html_parts.append(f"<p><strong>Host:</strong> {data['host']}<br>")
    html_parts.append(f"<strong>Type:</strong> {data['db_type']}<br>")
    html_parts.append(f"<strong>Exported:</strong> {data['exported_at']}</p>")

    for schema in data["schemas"]:
        html_parts.append(f"<h2>Schema: {schema['name']}</h2>")

        for table in schema["tables"]:
            html_parts.append(f"<h3>Table: {table['name']}</h3>")
            if table.get("row_count"):
                html_parts.append(f"<p><strong>Rows:</strong> {table['row_count']:,}</p>")

            if table.get("ai_analysis"):
                ai = table["ai_analysis"]
                if ai.get("business_context"):
                    html_parts.append(f"<blockquote>{ai['business_context']}</blockquote>")

            html_parts.append("<table>")
            html_parts.append("<thead><tr><th>Column</th><th>Type</th><th>Nullable</th><th>PK</th><th>FK</th><th>Description</th></tr></thead>")
            html_parts.append("<tbody>")
            for col in table["columns"]:
                pk = "✓" if col["is_primary_key"] else ""
                fk = "✓" if col["is_foreign_key"] else ""
                desc = col.get("ai_description") or ""
                html_parts.append(
                    f"<tr><td>{col['name']}</td><td>{col['data_type']}</td><td>{col['is_nullable']}</td><td>{pk}</td><td>{fk}</td><td>{desc}</td></tr>"
                )
            html_parts.append("</tbody></table>")

            if table["relationships"]:
                html_parts.append("<p><strong>Relationships:</strong></p><ul>")
                for rel in table["relationships"]:
                    html_parts.append(f"<li><code>{rel['source_column']}</code> &rarr; <code>{rel['target_table']}.{rel['target_column']}</code></li>")
                html_parts.append("</ul>")

    content_html = "\n".join(html_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Data Dictionary: {data['database']}</title>
<style>
  body {{ font-family: 'Inter', -apple-system, sans-serif; max-width: 1000px; margin: 0 auto; padding: 2rem; background: #ffffff; color: #1e293b; line-height: 1.5; }}
  h1 {{ color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }}
  h2 {{ color: #334155; margin-top: 2rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem; }}
  h3 {{ color: #475569; margin-top: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 14px; page-break-inside: avoid; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 0.5rem 0.75rem; text-align: left; }}
  th {{ background: #f8fafc; color: #334155; font-weight: 600; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  blockquote {{ border-left: 4px solid #3b82f6; margin: 1rem 0; padding: 0.5rem 1rem; background: #eff6ff; border-radius: 0 8px 8px 0; font-style: italic; }}
  code {{ background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; color: #0284c7; font-family: monospace; }}
  .container {{ background: #ffffff; }}
</style>
</head>
<body>
<div class="container" id="pdf-content">
{content_html}
</div>
</body>
</html>"""
    return html


def _export_html(data: dict, filepath: str):
    html_str = _build_html_string(data)
    with open(filepath, "w") as f:
        f.write(html_str)


@router.post("/connections/{connection_id}/export", response_model=ExportStatusResponse)
def create_export(
    connection_id: int,
    payload: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a data dictionary export."""
    conn = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    fmt = payload.format.lower()
    if fmt not in ("json", "markdown", "html"):
        raise HTTPException(status_code=400, detail="Supported formats: json, markdown, html")

    _ensure_export_dir()
    ext = {"json": "json", "markdown": "md", "html": "html"}[fmt]
    filename = f"{conn.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{ext}"
    filepath = os.path.join(EXPORT_DIR, filename)

    # Build data
    data = _build_dictionary_data(db, conn)

    # Export
    if fmt == "json":
        _export_json(data, filepath)
    elif fmt == "markdown":
        _export_markdown(data, filepath)
    elif fmt == "html":
        _export_html(data, filepath)

    # Record job
    job = ExportJob(
        connection_id=connection_id,
        user_id=current_user.id,
        format=fmt,
        status="completed",
        file_path=filepath,
        completed_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return ExportStatusResponse(
        job_id=job.id,
        status=job.status,
        format=job.format,
        file_path=job.file_path,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/connections/{connection_id}/export/preview")
def preview_export(
    connection_id: int,
    format: str = Query("json"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview the data dictionary content."""
    conn = (
        db.query(DatabaseConnection)
        .filter_by(id=connection_id, user_id=current_user.id, is_active=True)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    data = _build_dictionary_data(db, conn)
    
    fmt = format.lower()
    if fmt == "markdown":
        return {"preview": _build_markdown_string(data), "format": "markdown"}
    elif fmt == "html":
        return {"preview": _build_html_string(data), "format": "html"}
    
    # Default to json
    return {"preview": data, "format": "json"}


@router.get("/export/{job_id}/download")
def download_export(
    job_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Download an exported file using a query token for browser compatibility."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    job = (
        db.query(ExportJob)
        .filter_by(id=job_id, user_id=user.id)
        .first()
    )
    if not job or not job.file_path:
        raise HTTPException(status_code=404, detail="Export job not found")

    if not os.path.exists(job.file_path):
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    return FileResponse(
        job.file_path,
        filename=os.path.basename(job.file_path),
        media_type="application/octet-stream",
    )
