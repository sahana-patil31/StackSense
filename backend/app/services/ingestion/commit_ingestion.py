from sqlalchemy.orm import Session

from app.models.commit import Commit
from app.schemas.commit import CommitCreate
from app.schemas.ingestion_batch import BulkIngestionSummary
from app.services.ingestion.normalization import normalize_text, normalize_timestamp


def ingest_commit(db: Session, payload: CommitCreate) -> Commit:
    existing = (
        db.query(Commit)
        .filter(Commit.repository_id == payload.repository_id, Commit.sha == payload.sha)
        .first()
    )
    if existing is not None:
        raise ValueError("Commit already exists")

    commit = Commit(
        repository_id=payload.repository_id,
        sha=payload.sha,
        author_name=normalize_text(payload.author_name),
        author_email=normalize_text(payload.author_email),
        message=normalize_text(payload.message),
        committed_at=normalize_timestamp(payload.committed_at),
    )
    db.add(commit)
    db.commit()
    db.refresh(commit)
    return commit


def list_commits(db: Session, repository_id: str | None = None) -> list[Commit]:
    query = db.query(Commit)
    if repository_id:
        query = query.filter(Commit.repository_id == repository_id)
    return query.order_by(Commit.committed_at.desc()).all()


def get_commit(db: Session, commit_id: str) -> Commit | None:
    return db.query(Commit).filter(Commit.id == commit_id).first()


def bulk_ingest_commits(db: Session, payloads: list[CommitCreate]) -> BulkIngestionSummary:
    inserted = 0
    duplicates = 0
    for payload in payloads:
        try:
            ingest_commit(db, payload)
            inserted += 1
        except ValueError:
            duplicates += 1
    db.commit()
    return BulkIngestionSummary(received=len(payloads), inserted=inserted, duplicates=duplicates, failed=0)
