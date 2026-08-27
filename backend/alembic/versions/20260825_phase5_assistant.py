"""Phase 5 assistant knowledge and conversations

Revision ID: e3f4a5b6c7d8
Revises: d2b3c4e5f6a7
"""
from alembic import op
import sqlalchemy as sa

revision = "e3f4a5b6c7d8"
down_revision = "d2b3c4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("knowledge_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False), sa.Column("source_id", sa.String(255)),
        sa.Column("title", sa.String(512), nullable=False), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False), sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_knowledge_documents_repository_id", "knowledge_documents", ["repository_id"])
    op.create_index("ix_knowledge_documents_source_type", "knowledge_documents", ["source_type"])
    op.create_index("ix_knowledge_documents_source_id", "knowledge_documents", ["source_id"])
    op.create_table("conversations",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("repository_id", sa.String(36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_conversations_repository_id", "conversations", ["repository_id"])
    op.create_table("conversation_messages",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("source_refs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_conversation_messages_conversation_id", "conversation_messages", ["conversation_id"])
    # PostgreSQL deployments may enable pgvector separately; JSON remains the portable fallback.


def downgrade() -> None:
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
    op.drop_table("knowledge_documents")