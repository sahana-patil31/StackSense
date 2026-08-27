from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.application_event import ApplicationEvent
from app.models.commit import Commit
from app.models.deployment import Deployment
from app.models.deployment_risk_analysis import DeploymentRiskAnalysis
from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.models.repository import Repository
from app.schemas.overview import OverviewResponse, RecentCommitSummary, RecentDeploymentSummary, RecentEventSummary

router = APIRouter(prefix="/api/overview", tags=["Overview"])


@router.get("", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> OverviewResponse:
    repository_count = db.query(Repository).count()
    commit_count = db.query(Commit).count()
    deployment_count = db.query(Deployment).count()
    event_count = db.query(ApplicationEvent).count()
    active_incident_count = db.query(Incident).filter(Incident.status.notin_(["resolved", "closed"])).count()
    anomaly_count = db.query(Anomaly).filter(Anomaly.is_anomaly.is_(True)).count()
    high_risk_count = db.query(DeploymentRiskAnalysis).filter(DeploymentRiskAnalysis.risk_level.in_(["HIGH", "CRITICAL"])).count()

    recent_commits = db.query(Commit).order_by(Commit.created_at.desc()).limit(5).all()
    recent_deployments = db.query(Deployment).order_by(Deployment.created_at.desc()).limit(5).all()
    recent_events = db.query(ApplicationEvent).filter(ApplicationEvent.severity.in_(["error", "critical"])).order_by(ApplicationEvent.timestamp.desc()).limit(5).all()

    return OverviewResponse(
        repositories=repository_count,
        commits=commit_count,
        deployments=deployment_count,
        events=event_count,
        active_incidents=active_incident_count,
        anomalies=anomaly_count,
        high_risk_deployments=high_risk_count,
        recent_commits=[
            RecentCommitSummary(id=item.id, message=item.message or "", sha=item.sha) for item in recent_commits
        ],
        recent_deployments=[
            RecentDeploymentSummary(id=item.id, service_name=item.service_name or "", status=item.status) for item in recent_deployments
        ],
        recent_events=[
            RecentEventSummary(id=item.id, message=item.message or "", severity=item.severity or "") for item in recent_events
        ],
    )
