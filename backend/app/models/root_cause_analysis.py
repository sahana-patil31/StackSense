from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RootCauseAnalysis(Base):
    __tablename__ = "root_cause_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    anomaly_id: Mapped[str] = mapped_column(String(36), ForeignKey("anomalies.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_type: Mapped[str] = mapped_column(String(50), nullable=False)  # deployment, commit, service, code_entity
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_root_cause_anomaly_candidate", "anomaly_id", "candidate_id"),
    )
