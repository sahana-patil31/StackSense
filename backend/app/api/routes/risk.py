from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_engineer
from app.models.deployment import Deployment
from app.models.deployment_risk_analysis import DeploymentRiskAnalysis
from app.schemas.risk_intelligence import DeploymentRiskResponse
from app.ml.features.deployment_features import extract_deployment_features
from app.ml.risk.predict import predict_deployment_risk

router = APIRouter(prefix="/api/risk", tags=["Deployment Risk"])


@router.post("/deployments/{deployment_id}/analyze", response_model=DeploymentRiskResponse)
def analyze_deployment_risk(
    deployment_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_engineer),
) -> DeploymentRiskResponse:
    """Calculates and stores deployment risk score, level, probability, and factor breakdown."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

    features = extract_deployment_features(db, deployment_id)
    score, level, prob, factors, model_ver = predict_deployment_risk(features)

    analysis = DeploymentRiskAnalysis(
        deployment_id=deployment_id,
        model_version=model_ver,
        risk_score=score,
        risk_level=level,
        failure_probability=round(prob, 4),
        feature_snapshot=features,
        contributing_factors=factors,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return DeploymentRiskResponse.model_validate(analysis)


@router.get("/deployments/{deployment_id}", response_model=DeploymentRiskResponse)
def get_deployment_risk(
    deployment_id: str,
    db: Session = Depends(get_db),
) -> DeploymentRiskResponse:
    """Returns the latest risk analysis for a specific deployment."""
    analysis = (
        db.query(DeploymentRiskAnalysis)
        .filter(DeploymentRiskAnalysis.deployment_id == deployment_id)
        .order_by(DeploymentRiskAnalysis.created_at.desc())
        .first()
    )
    if not analysis:
        # Auto-trigger analysis if not previously analyzed
        return analyze_deployment_risk(deployment_id, db)
    return DeploymentRiskResponse.model_validate(analysis)


@router.get("/deployments", response_model=List[DeploymentRiskResponse])
def list_deployment_risk_analyses(
    risk_level: Optional[str] = Query(None, description="Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)"),
    db: Session = Depends(get_db),
) -> List[DeploymentRiskResponse]:
    """Returns historical deployment risk analyses with optional filtering."""
    query = db.query(DeploymentRiskAnalysis)
    if risk_level:
        query = query.filter(DeploymentRiskAnalysis.risk_level == risk_level.upper())

    analyses = query.order_by(DeploymentRiskAnalysis.created_at.desc()).all()
    return [DeploymentRiskResponse.model_validate(a) for a in analyses]
