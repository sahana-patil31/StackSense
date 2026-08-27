from sqlalchemy.orm import Session

from app.models.deployment import Deployment
from app.schemas.deployment import DeploymentCreate
from app.schemas.ingestion_batch import BulkIngestionSummary
from app.services.ingestion.normalization import normalize_environment, normalize_status, normalize_text, normalize_timestamp


def ingest_deployment(db: Session, payload: DeploymentCreate) -> Deployment:
    deployment = Deployment(
        repository_id=payload.repository_id,
        commit_sha=payload.commit_sha,
        environment=normalize_environment(payload.environment),
        status=normalize_status(payload.status),
        service_name=normalize_text(payload.service_name),
        deployed_at=normalize_timestamp(payload.deployed_at),
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment


def list_deployments(
    db: Session,
    repository_id: str | None = None,
    environment: str | None = None,
    status: str | None = None,
    service_name: str | None = None,
) -> list[Deployment]:
    query = db.query(Deployment)
    if repository_id:
        query = query.filter(Deployment.repository_id == repository_id)
    if environment:
        query = query.filter(Deployment.environment == environment.lower())
    if status:
        query = query.filter(Deployment.status == status.lower())
    if service_name:
        query = query.filter(Deployment.service_name == service_name)
    return query.order_by(Deployment.deployed_at.desc()).all()


def get_deployment(db: Session, deployment_id: str) -> Deployment | None:
    return db.query(Deployment).filter(Deployment.id == deployment_id).first()


def bulk_ingest_deployments(db: Session, payloads: list[DeploymentCreate]) -> BulkIngestionSummary:
    inserted = 0
    for payload in payloads:
        ingest_deployment(db, payload)
        inserted += 1
    db.commit()
    return BulkIngestionSummary(received=len(payloads), inserted=inserted, duplicates=0, failed=0)
