from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate
from app.schemas.pagination import paginate
from app.core.security import require_engineer
from app.models.repository import Repository
from app.services.ingestion.repository_ingestion import get_repository, ingest_repository, list_repositories

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


@router.post("", response_model=RepositoryResponse)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> RepositoryResponse:
    try:
        repository = ingest_repository(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RepositoryResponse.model_validate(repository)


@router.get("")
def list_repository_items(page: int | None = Query(default=None, ge=1), page_size: int | None = Query(default=None, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Repository).order_by(Repository.created_at.desc())
    repositories, pagination = paginate(query, page, page_size)
    items = [RepositoryResponse.model_validate(item) for item in repositories]
    return {"items": items, **pagination} if pagination else items


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository_item(repository_id: str, db: Session = Depends(get_db)) -> RepositoryResponse:
    repository = get_repository(db, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryResponse.model_validate(repository)


@router.patch("/{repository_id}", response_model=RepositoryResponse)
def update_repository(repository_id: str, payload: RepositoryUpdate, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> RepositoryResponse:
    repository = get_repository(db, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(repository, key, str(value) if key == "url" and value is not None else value)
    db.commit()
    db.refresh(repository)
    return RepositoryResponse.model_validate(repository)


@router.delete("/{repository_id}", status_code=204)
def delete_repository(repository_id: str, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> None:
    repository = get_repository(db, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    db.delete(repository)
    db.commit()
