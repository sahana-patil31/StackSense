from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.security import require_engineer
from app.models.incident import Incident
from app.models.root_cause_analysis import RootCauseAnalysis
from app.schemas.risk_intelligence import IncidentResponse, RootCauseAnalysisResponse
from app.ml.correlation.root_cause import analyze_root_cause_for_anomaly

router = APIRouter(tags=["Incidents & Root Cause"])


@router.post("/api/incidents/analyze/{anomaly_id}", response_model=List[RootCauseAnalysisResponse])
def trigger_root_cause_analysis(
    anomaly_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_engineer),
) -> List[RootCauseAnalysisResponse]:
    """Runs deterministic evidence-based root-cause correlation for an anomaly."""
    try:
        rc_records, incident = analyze_root_cause_for_anomaly(db, anomaly_id=anomaly_id)
        return [RootCauseAnalysisResponse.model_validate(r) for r in rc_records]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident_item(
    incident_id: str,
    db: Session = Depends(get_db),
) -> IncidentResponse:
    """Returns details for a specific incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return IncidentResponse.model_validate(incident)


@router.get("/api/incidents", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status (detected, investigating, resolved, closed)"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    db: Session = Depends(get_db),
) -> List[IncidentResponse]:
    """Returns list of incidents with optional filtering."""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status.lower())
    if severity:
        query = query.filter(Incident.severity == severity.lower())

    try:
        incidents = query.order_by(Incident.detected_at.desc()).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return [IncidentResponse.model_validate(i) for i in incidents]
