"""Phase 2 ingestion tables

Revision ID: bf7b3332b1e0
Revises: 2d0f7b95e6f0
Create Date: 2026-08-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "bf7b3332b1e0"
down_revision = "2d0f7b95e6f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("default_branch", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "commits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.String(length=36), nullable=False),
        sa.Column("sha", sa.String(length=255), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "sha", name="uq_commit_repository_sha"),
    )
    op.create_table(
        "deployments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.String(length=36), nullable=False),
        sa.Column("commit_sha", sa.String(length=255), nullable=True),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "application_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("event_type", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ingestion_batches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("data_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("records_received", sa.Integer(), nullable=False),
        sa.Column("records_inserted", sa.Integer(), nullable=False),
        sa.Column("records_failed", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ingestion_batches")
    op.drop_table("application_events")
    op.drop_table("deployments")
    op.drop_table("commits")
    op.drop_table("repositories")
