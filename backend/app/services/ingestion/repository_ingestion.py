from typing import Any

from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.ingestion.normalization import normalize_text


def ingest_repository(db: Session, payload: RepositoryCreate) -> Repository:
    normalized_name = normalize_text(payload.name)
    if normalized_name is None:
        raise ValueError("Repository name is required")

    repository = Repository(
        name=normalized_name,
        url=str(payload.url) if payload.url else None,
        provider=payload.provider,
        default_branch=payload.default_branch,
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return repository


def list_repositories(db: Session) -> list[Repository]:
    return db.query(Repository).order_by(Repository.created_at.desc()).all()


def get_repository(db: Session, repository_id: str) -> Repository | None:
    return db.query(Repository).filter(Repository.id == repository_id).first()
