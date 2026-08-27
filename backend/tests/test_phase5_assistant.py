from app.ai.providers import LocalHashEmbeddingProvider, LocalGroundedLLMProvider, ProviderError
from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument
from app.models.repository import Repository
from app.main import app
from fastapi.testclient import TestClient
from conftest import TestingSessionLocal


client = TestClient(app)


def test_local_embedding_is_fixed_dimension_and_rejects_empty_text() -> None:
    provider = LocalHashEmbeddingProvider()
    assert len(provider.embed("deployment risk")) == provider.dimension
    try:
        provider.embed(" ")
    except ProviderError:
        pass
    else:
        raise AssertionError("empty text must fail")


def test_chat_followup_sources_and_repository_isolation() -> None:
    first = client.post("/api/repositories", json={"name": "assistant-one", "provider": "github"}).json()["id"]
    second = client.post("/api/repositories", json={"name": "assistant-two", "provider": "github"}).json()["id"]
    db = TestingSessionLocal()
    try:
        embedding = LocalHashEmbeddingProvider()
        db.add(KnowledgeDocument(repository_id=first, source_type="incident", source_id="inc-1", title="Payment incident", content="Payment timeout incident in production", document_metadata={"service": "payments"}, embedding=embedding.embed("Payment timeout incident in production")))
        db.add(KnowledgeDocument(repository_id=second, source_type="incident", source_id="inc-2", title="Private incident", content="Private repository evidence", document_metadata={}, embedding=embedding.embed("Private repository evidence")))
        db.commit()
    finally:
        db.close()
    response = client.post("/api/assistant/chat", json={"repository_id": first, "question": "What happened in the payment incident?"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["conversation_id"]
    assert all(source["source_id"] == "inc-1" for source in data["sources"])
    followup = client.post("/api/assistant/chat", json={"repository_id": first, "conversation_id": data["conversation_id"], "question": "Summarize it"})
    assert followup.status_code == 200
    isolated = client.post("/api/assistant/chat", json={"repository_id": second, "question": "What happened?"})
    assert isolated.status_code == 200
    assert all(source["source_id"] != "inc-1" for source in isolated.json()["sources"])


def test_local_llm_is_explicit_when_evidence_is_missing() -> None:
    assert "Insufficient evidence" in LocalGroundedLLMProvider().answer("question", [])