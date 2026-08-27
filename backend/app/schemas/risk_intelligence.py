from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class ContributingFactor(BaseModel):
    factor_name: str
    feature_value: Any
    impact: str  # HIGH, MEDIUM, LOW
    description: str


class DeploymentRiskResponse(BaseModel):
    id: str
    deployment_id: str
    model_version: str
    risk_score: int  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    failure_probability: float
    feature_snapshot: dict[str, Any]
    contributing_factors: List[ContributingFactor]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyResponse(BaseModel):
    id: str
    service_name: str
    window_start: datetime
    window_end: datetime
    anomaly_score: float
    is_anomaly: bool
    metrics_snapshot: dict[str, Any]
    detection_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceItem(BaseModel):
    evidence_type: str  # temporal_proximity, service_overlap, dependency_overlap, historical_association
    score: float
    description: str


class CandidateCause(BaseModel):
    candidate_type: str  # deployment, commit, service, code_entity
    candidate_id: str
    confidence_score: float
    evidence: List[EvidenceItem]


class RootCauseAnalysisResponse(BaseModel):
    id: str
    anomaly_id: str
    candidate_type: str
    candidate_id: str
    confidence_score: float
    evidence: List[EvidenceItem]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: str
    title: str
    status: str  # detected, investigating, resolved, closed
    severity: str  # low, medium, high, critical
    detected_at: datetime
    primary_anomaly_id: str
    probable_cause: str
    confidence: float
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
