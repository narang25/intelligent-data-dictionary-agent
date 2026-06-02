"""add multi-database columns to database_connections

Revision ID: 20260324_multidb
Revises: 
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa

revision = '20260324_multidb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('database_connections', sa.Column('account', sa.String(), nullable=True))
    op.add_column('database_connections', sa.Column('warehouse', sa.String(), nullable=True))
    op.add_column('database_connections', sa.Column('role', sa.String(), nullable=True))
    op.add_column('database_connections', sa.Column('credentials_json', sa.Text(), nullable=True))
    # Make encrypted_password nullable (BigQuery doesn't use passwords)
    op.alter_column('database_connections', 'encrypted_password', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column('database_connections', 'encrypted_password', existing_type=sa.Text(), nullable=False)
    op.drop_column('database_connections', 'credentials_json')
    op.drop_column('database_connections', 'role')
    op.drop_column('database_connections', 'warehouse')
    op.drop_column('database_connections', 'account')
