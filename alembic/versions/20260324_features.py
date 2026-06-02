"""Add all feature tables: annotations, column_lineage, profiling_history,
anomaly_alerts, column_permissions, and role on users.

Revision ID: 20260324_features
"""
from alembic import op
import sqlalchemy as sa

revision = "20260324_features"
down_revision = "20260324_multidb"
branch_labels = None
depends_on = None


def upgrade():
    # -- Role on users --
    op.add_column("users", sa.Column("role", sa.String(), server_default="analyst"))

    # -- Annotations (Feature 6) --
    op.create_table(
        "annotations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("table_name", sa.String, nullable=False),
        sa.Column("column_name", sa.String, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -- Column Lineage (Feature 2) --
    op.create_table(
        "column_lineage",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_table", sa.String, nullable=False),
        sa.Column("source_column", sa.String, nullable=False),
        sa.Column("target_table", sa.String, nullable=False),
        sa.Column("target_column", sa.String, nullable=False),
        sa.Column("transformation_expression", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -- Profiling History (Feature 3) --
    op.create_table(
        "profiling_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("column_id", sa.Integer, sa.ForeignKey("columns.id"), nullable=False),
        sa.Column("null_rate", sa.Float, nullable=True),
        sa.Column("duplicate_rate", sa.Float, nullable=True),
        sa.Column("mean", sa.Float, nullable=True),
        sa.Column("std_dev", sa.Float, nullable=True),
        sa.Column("profiled_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -- Anomaly Alerts (Feature 3) --
    op.create_table(
        "anomaly_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("column_id", sa.Integer, sa.ForeignKey("columns.id"), nullable=False),
        sa.Column("table_name", sa.String, nullable=False),
        sa.Column("column_name", sa.String, nullable=False),
        sa.Column("alert_type", sa.String, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("severity", sa.String, server_default="warning"),
        sa.Column("dismissed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -- Column Permissions (Feature 7) --
    op.create_table(
        "column_permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("table_name", sa.String, nullable=False),
        sa.Column("column_name", sa.String, nullable=False),
        sa.Column("allow", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("column_permissions")
    op.drop_table("anomaly_alerts")
    op.drop_table("profiling_history")
    op.drop_table("column_lineage")
    op.drop_table("annotations")
    op.drop_column("users", "role")
