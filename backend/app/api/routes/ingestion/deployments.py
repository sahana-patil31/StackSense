from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.deployment import DeploymentCreate, DeploymentResponse
from app.schemas.ingestion_batch import BulkIngestionSummary
from app.core.security import require_engineer
from app.schemas.pagination import paginate
from app.models.deployment import Deployment
from app.services.ingestion.deployment_ingestion import bulk_ingest_deployments, get_deployment, ingest_deployment, list_deployments

router = APIRouter(prefix="/api/deployments", tags=["Deployments"])


@router.post("", response_model=DeploymentResponse)
def create_deployment(payload: DeploymentCreate, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> DeploymentResponse:
    try:
        deployment = ingest_deployment(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DeploymentResponse.model_validate(deployment)


@router.get("")
def list_deployment_items(
    repository_id: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service_name: str | None = Query(default=None),
    page: int | None = Query(default=None, ge=1), page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[DeploymentResponse]:
    query = db.query(Deployment)
    for field, value in ((Deployment.repository_id, repository_id), (Deployment.environment, environment), (Deployment.status, status), (Deployment.service_name, service_name)):
        if value:
            query = query.filter(field == value)
    deployments, pagination = paginate(query, page, page_size)
    items = [DeploymentResponse.model_validate(item) for item in deployments]
    return {"items": items, **pagination} if pagination else items


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment_item(deployment_id: str, db: Session = Depends(get_db)) -> DeploymentResponse:
    deployment = get_deployment(db, deployment_id)
    if deployment is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return DeploymentResponse.model_validate(deployment)


@router.post("/bulk", response_model=BulkIngestionSummary)
def bulk_create_deployments(payload: list[DeploymentCreate], db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> BulkIngestionSummary:
    if len(payload) > 500:
        raise HTTPException(status_code=413, detail="Bulk payload cannot exceed 500 items")
    return bulk_ingest_deployments(db, payload)
