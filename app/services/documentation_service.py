import json
from app.domain.models import Table, ColumnModel, ColumnProfile, Documentation


class DocumentationService:

    def __init__(self, ai_service, session):
        self.ai_service = ai_service
        self.session = session

    def build_table_context(self, table: Table):
        context = {
            "table_name": table.name,
            "columns": []
        }

        for column in table.columns:
            profile = column.profile

            context["columns"].append({
                "name": column.name,
                "data_type": column.data_type,
                "is_nullable": column.is_nullable,
                "null_percentage": profile.null_percentage if profile else None,
                "distinct_count": profile.distinct_count if profile else None
            })

        return context

    def generate_table_documentation(self, table: Table):
        context = self.build_table_context(table)

        system_prompt = """
You are a senior data architect.
Generate structured JSON documentation for a database table.

Return ONLY valid JSON in this format:
{
  "summary": "...",
  "business_purpose": "...",
  "data_quality_notes": "...",
  "recommended_usage": "..."
}
"""

        user_prompt = f"""
Table Metadata:
{json.dumps(context, indent=2)}
"""

        response = self.ai_service.generate(system_prompt, user_prompt)
        clean_response = response.strip()

        # Remove markdown code fences if present
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            clean_response = clean_response.replace("json", "").strip()

        try:
            parsed = json.loads(clean_response)
        except Exception:
            parsed = {
                "summary": clean_response,
                "business_purpose": "",
                "data_quality_notes": "",
                "recommended_usage": ""
            }

        # Save documentation
        doc = Documentation(
            entity_type="table",
            entity_id=table.id,
            description=json.dumps(parsed, indent=2)
        )

        self.session.add(doc)
        self.session.commit()

        return parsed

    def generate_markdown(self, table: Table, json_doc: dict):

        md = f"# Table: {table.name}\n\n"
        md += f"## Summary\n{json_doc.get('summary', '')}\n\n"
        md += f"## Business Purpose\n{json_doc.get('business_purpose', '')}\n\n"
        md += f"## Data Quality Notes\n{json_doc.get('data_quality_notes', '')}\n\n"
        md += f"## Recommended Usage\n{json_doc.get('recommended_usage', '')}\n\n"

        md += "## Columns\n"

        for column in table.columns:
            md += f"- **{column.name}** ({column.data_type})\n"

        return md
