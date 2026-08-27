from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_phase4_risk_analysis_flow() -> None:
    # 1. Create a repository and a deployment
    repo_resp = client.post(
        "/api/repositories",
        json={"name": "risk-service", "provider": "github"},
    )
    assert repo_resp.status_code == 200
    repo_id = repo_resp.json()["id"]

    dep_resp = client.post(
        "/api/deployments",
        json={
            "repository_id": repo_id,
            "commit_sha": "sha-risk-100",
            "environment": "production",
            "status": "success",
            "service_name": "risk-service",
            "deployed_at": "2026-08-17T12:00:00Z",
        },
    )
    assert dep_resp.status_code == 200
    dep_id = dep_resp.json()["id"]

    # 2. Trigger risk analysis POST
    risk_resp = client.post(f"/api/risk/deployments/{dep_id}/analyze")
    assert risk_resp.status_code == 200, risk_resp.text
    risk_data = risk_resp.json()
    assert risk_data["deployment_id"] == dep_id
    assert 0 <= risk_data["risk_score"] <= 100
    assert risk_data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "contributing_factors" in risk_data

    # 3. GET risk analysis for deployment
    get_risk = client.get(f"/api/risk/deployments/{dep_id}")
    assert get_risk.status_code == 200
    assert get_risk.json()["id"] == risk_data["id"]

    # 4. GET list risk analyses
    list_risk = client.get("/api/risk/deployments")
    assert list_risk.status_code == 200
    assert len(list_risk.json()) >= 1


def test_phase4_anomaly_detection_and_root_cause_flow() -> None:
    # 1. Post a batch of events with error spike
    for i in range(10):
        client.post(
            "/api/events",
            json={
                "service_name": "payment-api",
                "timestamp": "2026-08-17T14:00:00Z",
                "severity": "ERROR" if i > 3 else "INFO",
                "message": "Payment processing exception" if i > 3 else "Normal request",
                "error_type": "PaymentFailedError" if i > 3 else None,
            },
        )

    # 2. Run anomaly detection
    det_resp = client.post("/api/anomalies/detect?service_name=payment-api")
    assert det_resp.status_code == 200, det_resp.text
    anomalies = det_resp.json()
    assert len(anomalies) >= 1
    anom_id = anomalies[0]["id"]

    # 3. GET anomalies
    get_anom = client.get(f"/api/anomalies/{anom_id}")
    assert get_anom.status_code == 200
    assert get_anom.json()["id"] == anom_id

    # 4. Trigger Root Cause Incident Analysis
    rc_resp = client.post(f"/api/incidents/analyze/{anom_id}")
    assert rc_resp.status_code == 200, rc_resp.text
    candidates = rc_resp.json()
    assert isinstance(candidates, list)

    # 5. List incidents
    incidents_resp = client.get("/api/incidents")
    assert incidents_resp.status_code == 200
    incidents = incidents_resp.json()
    assert len(incidents) >= 1
    assert incidents[0]["primary_anomaly_id"] == anom_id
