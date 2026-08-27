"""Initial projects table

Revision ID: 2d0f7b95e6f0
Revises: 
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "2d0f7b95e6f0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("projects")
