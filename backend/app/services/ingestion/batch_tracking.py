from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ingestion_batch import IngestionBatch


def create_batch(db: Session, source: str, data_type: str) -> IngestionBatch:
    batch = IngestionBatch(source=source, data_type=data_type, status="running")
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def finalize_batch(
    db: Session,
    batch: IngestionBatch,
    records_received: int,
    records_inserted: int,
    records_failed: int,
    error_summary: str | None = None,
) -> IngestionBatch:
    batch.records_received = records_received
    batch.records_inserted = records_inserted
    batch.records_failed = records_failed
    batch.status = "completed" if records_failed == 0 else "failed"
    batch.completed_at = datetime.now(timezone.utc)
    batch.error_summary = error_summary
    db.commit()
    db.refresh(batch)
    return batch
