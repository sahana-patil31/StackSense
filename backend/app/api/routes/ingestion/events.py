from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.application_event import ApplicationEventCreate, ApplicationEventResponse
from app.schemas.ingestion_batch import BulkIngestionSummary
from app.core.security import require_engineer
from app.schemas.pagination import paginate
from app.models.application_event import ApplicationEvent
from app.services.ingestion.event_ingestion import bulk_ingest_events, get_event, ingest_event, list_events

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post("", response_model=ApplicationEventResponse)
def create_event(payload: ApplicationEventCreate, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> ApplicationEventResponse:
    try:
        event = ingest_event(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ApplicationEventResponse(
        id=event.id,
        service_name=event.service_name,
        timestamp=event.timestamp,
        severity=event.severity,
        event_type=event.event_type,
        message=event.message,
        error_type=event.error_type,
        metadata=event.event_metadata,
        created_at=event.created_at,
    )


@router.get("")
def list_event_items(
    service_name: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int | None = Query(default=None, ge=1), page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ApplicationEventResponse]:
    query = db.query(ApplicationEvent)
    for field, value in ((ApplicationEvent.service_name, service_name), (ApplicationEvent.severity, severity), (ApplicationEvent.event_type, event_type)):
        if value:
            query = query.filter(field == value)
    events, pagination = paginate(query, page, page_size)
    items = [
        ApplicationEventResponse(
            id=item.id,
            service_name=item.service_name,
            timestamp=item.timestamp,
            severity=item.severity,
            event_type=item.event_type,
            message=item.message,
            error_type=item.error_type,
            metadata=item.event_metadata,
            created_at=item.created_at,
        )
        for item in events
    ]
    return {"items": items, **pagination} if pagination else items


@router.get("/{event_id}", response_model=ApplicationEventResponse)
def get_event_item(event_id: str, db: Session = Depends(get_db)) -> ApplicationEventResponse:
    event = get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return ApplicationEventResponse(
        id=event.id,
        service_name=event.service_name,
        timestamp=event.timestamp,
        severity=event.severity,
        event_type=event.event_type,
        message=event.message,
        error_type=event.error_type,
        metadata=event.event_metadata,
        created_at=event.created_at,
    )


@router.post("/bulk", response_model=BulkIngestionSummary)
def bulk_create_events(payload: list[ApplicationEventCreate], db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> BulkIngestionSummary:
    if len(payload) > 500:
        raise HTTPException(status_code=413, detail="Bulk payload cannot exceed 500 items")
    return bulk_ingest_events(db, payload)
