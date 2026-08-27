"""Phase 3 code analysis tables

Revision ID: c1a2b3c4d5e6
Revises: bf7b3332b1e0
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c1a2b3c4d5e6"
down_revision = "bf7b3332b1e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("files_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("entities_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relationships_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_runs_repository_id", "analysis_runs", ["repository_id"])

    op.create_table(
        "code_files",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.String(length=36), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("analysis_status", sa.String(length=50), nullable=False, server_default="success"),
        sa.Column("analysis_error", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_files_repository_id", "code_files", ["repository_id"])
    op.create_index("ix_code_files_repo_path", "code_files", ["repository_id", "path"], unique=True)

    op.create_table(
        "code_entities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.String(length=36), nullable=False),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("parent_entity_id", sa.String(length=36), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("qualified_name", sa.String(length=512), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("end_line", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["code_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_entity_id"], ["code_entities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_entities_repository_id", "code_entities", ["repository_id"])
    op.create_index("ix_code_entities_file_id", "code_entities", ["file_id"])
    op.create_index("ix_code_entities_parent_entity_id", "code_entities", ["parent_entity_id"])
    op.create_index("ix_code_entities_name", "code_entities", ["name"])
    op.create_index("ix_code_entities_repo_type", "code_entities", ["repository_id", "entity_type"])

    op.create_table(
        "code_relationships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("repository_id", sa.String(length=36), nullable=False),
        sa.Column("source_entity_id", sa.String(length=36), nullable=False),
        sa.Column("target_entity_id", sa.String(length=36), nullable=True),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_target", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_entity_id"], ["code_entities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_entity_id"], ["code_entities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_relationships_repository_id", "code_relationships", ["repository_id"])
    op.create_index("ix_code_relationships_source_entity_id", "code_relationships", ["source_entity_id"])
    op.create_index("ix_code_relationships_target_entity_id", "code_relationships", ["target_entity_id"])
    op.create_index("ix_code_relationships_repo_type", "code_relationships", ["repository_id", "relationship_type"])


def downgrade() -> None:
    op.drop_table("code_relationships")
    op.drop_table("code_entities")
    op.drop_table("code_files")
    op.drop_table("analysis_runs")
