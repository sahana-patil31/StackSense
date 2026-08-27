from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeploymentRiskAnalysis(Base):
    __tablename__ = "deployment_risk_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False, default="risk_model_v1")
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    contributing_factors: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_deployment_risk_level", "risk_level"),
    )
