from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.security import require_engineer
from app.models.anomaly import Anomaly
from app.schemas.risk_intelligence import AnomalyResponse
from app.ml.anomaly.detect import detect_production_anomalies

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])


@router.post("/detect", response_model=List[AnomalyResponse])
def run_anomaly_detection(
    service_name: Optional[str] = Query(None, description="Optional service name to filter detection"),
    window_minutes: int = Query(5, description="Time window in minutes"),
    db: Session = Depends(get_db),
    _: object = Depends(require_engineer),
) -> List[AnomalyResponse]:
    """Runs anomaly detection over application events and stores results."""
    anomalies = detect_production_anomalies(db, window_minutes=window_minutes, service_name=service_name)
    return [AnomalyResponse.model_validate(a) for a in anomalies]


@router.get("", response_model=List[AnomalyResponse])
def list_anomalies(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    is_anomaly: Optional[bool] = Query(None, description="Filter by is_anomaly boolean flag"),
    db: Session = Depends(get_db),
) -> List[AnomalyResponse]:
    """Returns detected anomalies with optional filtering."""
    query = db.query(Anomaly)
    if service_name:
        query = query.filter(Anomaly.service_name == service_name)
    if is_anomaly is not None:
        query = query.filter(Anomaly.is_anomaly == is_anomaly)

    try:
        anomalies = query.order_by(Anomaly.window_start.desc()).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return [AnomalyResponse.model_validate(a) for a in anomalies]


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly_item(
    anomaly_id: str,
    db: Session = Depends(get_db),
) -> AnomalyResponse:
    """Returns details for a specific anomaly."""
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly '{anomaly_id}' not found")
    return AnomalyResponse.model_validate(anomaly)
