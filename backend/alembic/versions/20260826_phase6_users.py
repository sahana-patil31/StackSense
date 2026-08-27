"""Add users for Phase 6 authentication."""
from alembic import op
import sqlalchemy as sa

revision = "20260826_phase6_users"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")