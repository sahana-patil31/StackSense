from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    metrics_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    detection_method: Mapped[str] = mapped_column(String(100), nullable=False, default="IsolationForest")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_anomalies_service_window", "service_name", "window_start"),
    )
