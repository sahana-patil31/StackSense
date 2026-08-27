from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_engineer
from app.schemas.pagination import paginate
from app.schemas.commit import CommitCreate, CommitResponse
from app.schemas.ingestion_batch import BulkIngestionSummary
from app.services.ingestion.commit_ingestion import bulk_ingest_commits, get_commit, ingest_commit, list_commits

router = APIRouter(prefix="/api/commits", tags=["Commits"])


@router.post("", response_model=CommitResponse)
def create_commit(payload: CommitCreate, db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> CommitResponse:
    try:
        commit = ingest_commit(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CommitResponse.model_validate(commit)


@router.get("")
def list_commit_items(
    repository_id: str | None = Query(default=None),
    page: int | None = Query(default=None, ge=1), page_size: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CommitResponse]:
    query = db.query(__import__("app.models.commit", fromlist=["Commit"]).Commit)
    if repository_id:
        query = query.filter(query.column_descriptions[0]["type"].repository_id == repository_id)
    commits, pagination = paginate(query, page, page_size)
    items = [CommitResponse.model_validate(item) for item in commits]
    return {"items": items, **pagination} if pagination else items


@router.get("/{commit_id}", response_model=CommitResponse)
def get_commit_item(commit_id: str, db: Session = Depends(get_db)) -> CommitResponse:
    commit = get_commit(db, commit_id)
    if commit is None:
        raise HTTPException(status_code=404, detail="Commit not found")
    return CommitResponse.model_validate(commit)


@router.post("/bulk", response_model=BulkIngestionSummary)
def bulk_create_commits(payload: list[CommitCreate], db: Session = Depends(get_db), _: object = Depends(require_engineer)) -> BulkIngestionSummary:
    if len(payload) > 500:
        raise HTTPException(status_code=413, detail="Bulk payload cannot exceed 500 items")
    return bulk_ingest_commits(db, payload)
