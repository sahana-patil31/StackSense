"""Index operational and code records: python -m app.ai.index [repository_id]."""
import hashlib
import json
import os
import sys
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.ai.chunking import chunk_text
from app.ai.providers import get_embedding_provider
from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument
from app.models.repository import Repository

SOURCES = {
    "code_files": ("code_file", "path"), "code_entities": ("code_entity", "name"), "commits": ("commit", "sha"),
    "code_relationships": ("code_relationship", "relationship_type"),
    "deployments": ("deployment", "id"), "application_events": ("event", "id"), "anomalies": ("anomaly", "id"),
    "incidents": ("incident", "title"), "root_cause_analyses": ("root_cause", "id"),
}


def _safe_rows(db, model_name: str):
    try:
        from app import models
        model = getattr(models, model_name, None)
        return db.query(model).all() if model else []
    except SQLAlchemyError:
        db.rollback()
        return []


def _value(obj: Any, name: str, default=None):
    value = getattr(obj, name, default)
    if isinstance(value, (dict, list)):
        return value
    return value


def _text(obj: Any) -> str:
    data = {key: value for key, value in vars(obj).items() if not key.startswith("_") and key not in {"embedding", "document_metadata"}}
    return json.dumps(data, default=str, sort_keys=True)


def index_repository(db, repository_id: str | None = None) -> int:
    embedder = get_embedding_provider()
    count = 0
    for table, (source_type, title_field) in SOURCES.items():
        model_name = {"code_files": "CodeFile", "code_entities": "CodeEntity", "commits": "Commit", "code_relationships": "CodeRelationship", "deployments": "Deployment", "application_events": "ApplicationEvent", "anomalies": "Anomaly", "incidents": "Incident", "root_cause_analyses": "RootCauseAnalysis"}[table]
        for obj in _safe_rows(db, model_name):
            object_repo = getattr(obj, "repository_id", None)
            if repository_id and object_repo != repository_id:
                continue
            content = _text(obj)
            if not content.strip():
                continue
            source_id = str(getattr(obj, "id", None))
            metadata = {"content_hash": hashlib.sha256(content.encode()).hexdigest(), "table": table, "record_id": source_id}
            existing_docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.repository_id == object_repo, KnowledgeDocument.source_type == source_type, KnowledgeDocument.source_id.like(f"{source_id}%")).all()
            if existing_docs and all(doc.document_metadata.get("content_hash") == metadata["content_hash"] for doc in existing_docs):
                continue
            chunks = chunk_text(content)
            if not chunks:
                continue
            for chunk_number, chunk in enumerate(chunks):
                chunk_id = source_id if len(chunks) == 1 else f"{source_id}#{chunk_number}"
                existing = next((doc for doc in existing_docs if doc.source_id == chunk_id), None)
                chunk_metadata = {**metadata, "chunk": chunk_number, "source_id": source_id}
                if existing:
                    existing.title, existing.content, existing.document_metadata, existing.embedding = str(_value(obj, title_field, source_id)), chunk, chunk_metadata, embedder.embed(chunk)
                else:
                    db.add(KnowledgeDocument(repository_id=object_repo, source_type=source_type, source_id=chunk_id, title=str(_value(obj, title_field, source_id)), content=chunk, document_metadata=chunk_metadata, embedding=embedder.embed(chunk)))
            count += 1
    repositories = _safe_rows(db, "Repository")
    for repository in repositories:
        if repository_id and repository.id != repository_id:
            continue
        root = repository.url if repository.url and os.path.isdir(repository.url) else None
        if not root:
            continue
        for filename in ("README.md", "README.rst", "README.txt"):
            path = os.path.join(root, filename)
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as readme:
                content = readme.read()
            for chunk_number, chunk in enumerate(chunk_text(content)):
                source_id = f"{repository.id}:{filename}:{chunk_number}"
                metadata = {"table": "repository_documentation", "path": path, "chunk": chunk_number}
                existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.repository_id == repository.id, KnowledgeDocument.source_type == "repository_documentation", KnowledgeDocument.source_id == source_id).first()
                if not existing:
                    db.add(KnowledgeDocument(repository_id=repository.id, source_type="repository_documentation", source_id=source_id, title=filename, content=chunk, document_metadata=metadata, embedding=embedder.embed(chunk)))
                    count += 1
            break
    db.commit()
    return count


def main() -> None:
    repository_id = sys.argv[1] if len(sys.argv) > 1 else None
    db = SessionLocal()
    try:
        print(f"Indexed {index_repository(db, repository_id)} documents")
    finally:
        db.close()


if __name__ == "__main__":
    main()
