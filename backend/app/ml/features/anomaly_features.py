from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.application_event import ApplicationEvent


def aggregate_event_windows(
    db: Session,
    window_minutes: int = 5,
    service_name: str = None,
) -> List[Dict[str, Any]]:
    """Aggregates application events into time windows per service."""
    query = db.query(ApplicationEvent)
    if service_name:
        query = query.filter(ApplicationEvent.service_name == service_name)

    events = query.order_by(ApplicationEvent.timestamp.asc()).all()
    if not events:
        return []

    # Group events by service and 5-minute bucket
    buckets: Dict[tuple[str, datetime], Dict[str, Any]] = {}

    for event in events:
        svc = event.service_name or "default-service"
        ts = event.timestamp or event.created_at or datetime.now(timezone.utc)
        
        # Round down to nearest window_minutes boundary
        minute_bucket = (ts.minute // window_minutes) * window_minutes
        w_start = ts.replace(minute=minute_bucket, second=0, microsecond=0)

        key = (svc, w_start)
        if key not in buckets:
            buckets[key] = {
                "service_name": svc,
                "window_start": w_start,
                "window_end": w_start + timedelta(minutes=window_minutes),
                "total_events": 0,
                "error_count": 0,
                "critical_count": 0,
                "warning_count": 0,
            }

        b = buckets[key]
        b["total_events"] += 1
        sev = (event.severity or "").lower()

        if "error" in sev or event.error_type:
            b["error_count"] += 1
        if "critical" in sev:
            b["critical_count"] += 1
        if "warn" in sev:
            b["warning_count"] += 1

    results: List[Dict[str, Any]] = []
    for b in buckets.values():
        total = b["total_events"]
        err_count = b["error_count"] + b["critical_count"]
        b["error_rate"] = round(err_count / max(1, total), 4)
        results.append(b)

    return sorted(results, key=lambda x: x["window_start"])
