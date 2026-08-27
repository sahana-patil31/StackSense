"""Allow unscoped assistant conversations.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
"""
from alembic import op


revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.alter_column("repository_id", nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.alter_column("repository_id", nullable=False)