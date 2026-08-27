import math
from typing import Any
from sqlalchemy.orm import Session
from app.models.knowledge_document import KnowledgeDocument
from app.ai.providers import EmbeddingProvider
from app.ai.router import QueryRouter, QueryType


class HybridRetriever:
    def __init__(self, embedder: EmbeddingProvider, router: QueryRouter | None = None):
        self.embedder, self.router = embedder, router or QueryRouter()

    def search(self, db: Session, question: str, repository_id: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
        query_vector = self.embedder.embed(question)
        query = db.query(KnowledgeDocument)
        if repository_id:
            query = query.filter(KnowledgeDocument.repository_id == repository_id)
        docs = query.all()
        kind = self.router.classify(question)
        scored = []
        for doc in docs:
            vector = doc.embedding or []
            similarity = sum(a * b for a, b in zip(query_vector, vector)) / max(math.sqrt(sum(a*a for a in query_vector)) * math.sqrt(sum(a*a for a in vector)), 1e-9)
            keyword = sum(word.lower() in (doc.title + " " + doc.content).lower() for word in question.split() if len(word) > 3)
            type_bonus = 0.15 if kind.value.lower() in doc.source_type.lower() else 0
            scored.append((similarity + keyword * 0.05 + type_bonus, doc))
        scored.sort(key=lambda value: value[0], reverse=True)
        result, seen = [], set()
        for score, doc in scored:
            key = (doc.source_type, doc.source_id, doc.title)
            if key in seen:
                continue
            seen.add(key)
            result.append({"source_type": doc.source_type, "source_id": doc.source_id, "title": doc.title, "content": doc.content, "metadata": doc.document_metadata, "score": round(score, 6)})
            if len(result) >= limit:
                break
        return result
