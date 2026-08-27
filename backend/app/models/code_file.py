from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CodeFile(Base):
    __tablename__ = "code_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    analysis_status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")
    analysis_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_code_files_repo_path", "repository_id", "path", unique=True),
    )
