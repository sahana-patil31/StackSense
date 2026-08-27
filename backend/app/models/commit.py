from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Commit(Base):
    __tablename__ = "commits"
    __table_args__ = (
        UniqueConstraint("repository_id", "sha", name="uq_commit_repository_sha"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sha: Mapped[str] = mapped_column(String(255), nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
