import json
from pathlib import Path

from app.core.database import SessionLocal
from app.schemas.commit import CommitCreate
from app.schemas.deployment import DeploymentCreate
from app.schemas.application_event import ApplicationEventCreate
from app.schemas.repository import RepositoryCreate
from app.services.ingestion.commit_ingestion import ingest_commit
from app.services.ingestion.deployment_ingestion import ingest_deployment
from app.services.ingestion.event_ingestion import ingest_event
from app.services.ingestion.repository_ingestion import ingest_repository


BASE_DIR = Path(__file__).resolve().parent / "sample_data"


def load_sample_data() -> None:
    db = SessionLocal()
    try:
        with open(BASE_DIR / "repositories.json", "r", encoding="utf-8") as handle:
            repositories = json.load(handle)
        with open(BASE_DIR / "commits.json", "r", encoding="utf-8") as handle:
            commits = json.load(handle)
        with open(BASE_DIR / "deployments.json", "r", encoding="utf-8") as handle:
            deployments = json.load(handle)
        with open(BASE_DIR / "events.json", "r", encoding="utf-8") as handle:
            events = json.load(handle)

        for raw in repositories:
            ingest_repository(db, RepositoryCreate(**raw))

        for raw in commits:
            ingest_commit(db, CommitCreate(**raw))

        for raw in deployments:
            ingest_deployment(db, DeploymentCreate(**raw))

        for raw in events:
            ingest_event(db, ApplicationEventCreate(**raw))
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_data()
