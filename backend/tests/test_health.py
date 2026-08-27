from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_contains_status() -> None:
    response = client.get("/api/health")
    payload = response.json()
    assert "status" in payload
    assert payload["status"] == "healthy"


def test_database_health_endpoint_behaves_correctly() -> None:
    response = client.get("/api/health/db")
    assert response.status_code in {200, 503}
    payload = response.json()
    if response.status_code == 200:
        assert payload["status"] == "healthy"
        assert payload["database"] == "connected"
    else:
        assert payload["detail"] == "Database unavailable"
