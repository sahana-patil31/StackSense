from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_auth_hashes_passwords_and_assigns_roles() -> None:
    first = client.post("/api/auth/register", json={"email": "admin@example.com", "password": "correct horse battery"})
    assert first.status_code == 201
    assert first.json()["user"]["role"] == "ADMIN"
    second = client.post("/api/auth/register", json={"email": "viewer@example.com", "password": "correct horse battery"})
    assert second.status_code == 201
    assert second.json()["user"]["role"] == "VIEWER"
    assert client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong password"}).status_code == 401
    token = first.json()["access_token"]
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["email"] == "admin@example.com"


def test_request_id_errors_metrics_and_system_health() -> None:
    response = client.get("/api/repositories/does-not-exist", headers={"X-Request-ID": "phase6-test"})
    assert response.status_code == 404
    assert response.json()["request_id"] == "phase6-test"
    assert response.headers["X-Request-ID"] == "phase6-test"
    assert client.get("/api/health/system").status_code == 200
    assert "stacksense_http_requests_total" in client.get("/api/metrics").text


def test_repository_pagination_returns_envelope_when_requested() -> None:
    response = client.get("/api/repositories?page=1&page_size=1")
    assert response.status_code == 200
    assert set(response.json()) == {"items", "page", "page_size", "total"}