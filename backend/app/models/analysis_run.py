from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, running, completed, failed, partial
    files_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    entities_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relationships_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
