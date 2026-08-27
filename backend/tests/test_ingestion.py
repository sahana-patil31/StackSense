import os

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_repository_crud_flow() -> None:
    response = client.post(
        "/api/repositories",
        json={
            "name": "payment-service",
            "url": "https://github.com/acme/payment-service",
            "provider": "github",
            "default_branch": "main",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "payment-service"

    list_response = client.get("/api/repositories")
    assert list_response.status_code == 200
    repositories = list_response.json()
    assert len(repositories) >= 1


def test_commit_duplicate_prevention() -> None:
    response = client.post(
        "/api/commits",
        json={
            "repository_id": "repo-1",
            "sha": "abc123",
            "author_name": "Ada Lovelace",
            "author_email": "ada@example.com",
            "message": "Add ingestion support",
            "committed_at": "2026-08-10T12:00:00Z",
        },
    )
    assert response.status_code == 200

    duplicate = client.post(
        "/api/commits",
        json={
            "repository_id": "repo-1",
            "sha": "abc123",
            "author_name": "Ada Lovelace",
            "author_email": "ada@example.com",
            "message": "Add ingestion support",
            "committed_at": "2026-08-10T12:00:00Z",
        },
    )
    assert duplicate.status_code == 409


def test_deployment_filtering_and_validation() -> None:
    response = client.post(
        "/api/deployments",
        json={
            "repository_id": "repo-1",
            "commit_sha": "def456",
            "environment": "production",
            "status": "success",
            "service_name": "payment-service",
            "deployed_at": "2026-08-10T13:00:00Z",
        },
    )
    assert response.status_code == 200

    filtered = client.get("/api/deployments?environment=production&status=success")
    assert filtered.status_code == 200
    payload = filtered.json()
    assert len(payload) >= 1

    invalid = client.post(
        "/api/deployments",
        json={
            "repository_id": "repo-1",
            "commit_sha": "def456",
            "environment": "production",
            "status": "unknown",
            "service_name": "payment-service",
            "deployed_at": "2026-08-10T13:00:00Z",
        },
    )
    assert invalid.status_code == 422


def test_event_filtering_and_bulk_ingestion_summary() -> None:
    event = client.post(
        "/api/events",
        json={
            "service_name": "payment-service",
            "timestamp": "2026-08-10T14:00:00Z",
            "severity": " ERROR ",
            "event_type": "payment_failed",
            "message": "  Payment failed  ",
            "error_type": "PaymentError",
            "metadata": {"attempt": 2},
        },
    )
    assert event.status_code == 200

    filtered = client.get("/api/events?service_name=payment-service&severity=error")
    assert filtered.status_code == 200
    assert len(filtered.json()) >= 1

    summary = client.post(
        "/api/commits/bulk",
        json=[
            {
                "repository_id": "repo-1",
                "sha": "bulk-1",
                "author_name": "Ada",
                "author_email": "ada@example.com",
                "message": "Bulk commit",
                "committed_at": "2026-08-10T15:00:00Z",
            },
            {
                "repository_id": "repo-1",
                "sha": "bulk-1",
                "author_name": "Ada",
                "author_email": "ada@example.com",
                "message": "Bulk commit",
                "committed_at": "2026-08-10T15:00:00Z",
            },
        ],
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["received"] == 2
    assert payload["inserted"] + payload["duplicates"] == 2
