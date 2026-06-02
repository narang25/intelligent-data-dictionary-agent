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
                "is_primary_key": column.is_primary_key,
                "is_foreign_key": column.is_foreign_key,
                "null_percentage": profile.null_percentage if profile else None,
                "distinct_count": profile.distinct_count if profile else None
            })

        return context

    def generate_table_documentation(self, table: Table):
        context = self.build_table_context(table)

        system_prompt = """
You are a Staff-Level Enterprise Data Architect. Your task is to generate 99.9% accurate, strictly schema-grounded documentation for database tables. 

CRITICAL INSTRUCTIONS:
1. NO HALLUCINATIONS: Do not guess business meaning if the column names do not obviously imply it. Stick to the facts.
2. SCHEMA GROUNDING: Explicitly mention Primary Keys (PK), Foreign Keys (FK), and nullability in your breakdown. Rely ONLY on the provided schema metadata and profiles.
3. CONTEXTUAL ACCURACY: If a table is a join table, dimension table, or fact table, state that clearly.
4. JSON FORMAT ONLY: You MUST output exactly and only valid JSON matching this schema:
{
  "summary": "Precise 2-sentence technical summary of the table's role.",
  "business_purpose": "The exact business function this table serves, based STRICTLY on its name and columns.",
  "data_quality_notes": "Observations on nullability, distinct counts, or constraints based ONLY on the metadata.",
  "recommended_usage": "When and how data analysts should query this table."
}
"""

        user_prompt = f"Strict Schema Metadata:\n{json.dumps(context, indent=2)}"

        response = self.ai_service.generate(system_prompt, user_prompt, json_mode=True)
        clean_response = response.strip()

        # Remove markdown code fences if present
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1].replace("json", "").strip()

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
