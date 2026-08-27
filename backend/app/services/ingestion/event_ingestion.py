from sqlalchemy.orm import Session

from app.models.application_event import ApplicationEvent
from app.schemas.application_event import ApplicationEventCreate
from app.schemas.ingestion_batch import BulkIngestionSummary
from app.services.ingestion.normalization import normalize_metadata, normalize_severity, normalize_text, normalize_timestamp


def ingest_event(db: Session, payload: ApplicationEventCreate) -> ApplicationEvent:
    event = ApplicationEvent(
        service_name=normalize_text(payload.service_name),
        timestamp=normalize_timestamp(payload.timestamp),
        severity=normalize_severity(payload.severity),
        event_type=normalize_text(payload.event_type),
        message=normalize_text(payload.message),
        error_type=normalize_text(payload.error_type),
        event_metadata=normalize_metadata(payload.metadata),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(
    db: Session,
    service_name: str | None = None,
    severity: str | None = None,
    event_type: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[ApplicationEvent]:
    query = db.query(ApplicationEvent)
    if service_name:
        query = query.filter(ApplicationEvent.service_name == service_name)
    if severity:
        query = query.filter(ApplicationEvent.severity == severity.lower())
    if event_type:
        query = query.filter(ApplicationEvent.event_type == event_type)
    if start_time:
        start_dt = normalize_timestamp(start_time)
        if start_dt is not None:
            query = query.filter(ApplicationEvent.timestamp >= start_dt)
    if end_time:
        end_dt = normalize_timestamp(end_time)
        if end_dt is not None:
            query = query.filter(ApplicationEvent.timestamp <= end_dt)
    return query.order_by(ApplicationEvent.timestamp.desc()).all()


def get_event(db: Session, event_id: str) -> ApplicationEvent | None:
    return db.query(ApplicationEvent).filter(ApplicationEvent.id == event_id).first()


def bulk_ingest_events(db: Session, payloads: list[ApplicationEventCreate]) -> BulkIngestionSummary:
    inserted = 0
    for payload in payloads:
        ingest_event(db, payload)
        inserted += 1
    db.commit()
    return BulkIngestionSummary(received=len(payloads), inserted=inserted, duplicates=0, failed=0)
