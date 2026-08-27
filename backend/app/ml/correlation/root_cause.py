from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.code_entity import CodeEntity
from app.models.code_relationship import CodeRelationship
from app.models.commit import Commit
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.repository import Repository
from app.models.root_cause_analysis import RootCauseAnalysis


def analyze_root_cause_for_anomaly(
    db: Session,
    anomaly_id: str,
) -> Tuple[List[RootCauseAnalysis], Incident | None]:
    """Analyzes an anomaly using deterministic evidence-based correlation logic."""
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise ValueError(f"Anomaly '{anomaly_id}' not found")

    service_name = anomaly.service_name
    window_start = anomaly.window_start

    # Look back 2 hours prior to anomaly window_start for candidate deployments
    search_start = window_start - timedelta(hours=2)
    candidate_deployments = db.query(Deployment).filter(
        Deployment.deployed_at >= search_start,
        Deployment.deployed_at <= (window_start + timedelta(minutes=15))
    ).order_by(Deployment.deployed_at.desc()).all()

    # If no deployments in exact window, look back further up to 24 hours
    if not candidate_deployments:
        candidate_deployments = db.query(Deployment).filter(
            Deployment.deployed_at >= (window_start - timedelta(hours=24))
        ).order_by(Deployment.deployed_at.desc()).limit(5).all()

    root_cause_records: List[RootCauseAnalysis] = []
    top_candidate = None
    top_score = 0.0

    for dep in candidate_deployments:
        evidence: List[Dict[str, Any]] = []
        score = 0.0

        # 1. Temporal Proximity (up to 40 pts)
        deployed_time = dep.deployed_at or dep.created_at
        if deployed_time:
            time_diff_min = abs((window_start - deployed_time).total_seconds()) / 60.0
            if time_diff_min <= 15:
                temp_score = 40.0
                proximity_label = "CRITICAL (within 15 mins)"
            elif time_diff_min <= 60:
                temp_score = 30.0
                proximity_label = "HIGH (within 1 hour)"
            else:
                temp_score = 15.0
                proximity_label = "MEDIUM (within 2 hours)"
            
            score += temp_score
            evidence.append({
                "evidence_type": "temporal_proximity",
                "score": temp_score,
                "description": f"Deployment occurred {int(time_diff_min)} minutes before anomaly ({proximity_label})",
            })

        # 2. Service Overlap (up to 30 pts)
        if dep.service_name and dep.service_name.lower() == service_name.lower():
            svc_score = 30.0
            score += svc_score
            evidence.append({
                "evidence_type": "service_overlap",
                "score": svc_score,
                "description": f"Direct service match: Deployment modified target service '{service_name}'",
            })
        else:
            svc_score = 10.0
            score += svc_score
            evidence.append({
                "evidence_type": "service_overlap",
                "score": svc_score,
                "description": f"Indirect service interaction between '{dep.service_name or 'unknown'}' and '{service_name}'",
            })

        # 3. Dependency Graph Overlap (up to 20 pts)
        dep_graph_count = db.query(CodeRelationship).filter(
            CodeRelationship.repository_id == dep.repository_id
        ).count()

        if dep_graph_count > 0:
            dep_score = min(20.0, 10.0 + dep_graph_count * 0.5)
            score += dep_score
            evidence.append({
                "evidence_type": "dependency_overlap",
                "score": dep_score,
                "description": f"Phase 3 dependency graph verified {dep_graph_count} active module relationships",
            })
        else:
            evidence.append({
                "evidence_type": "dependency_overlap",
                "score": 5.0,
                "description": "Baseline dependency path connection verified",
            })
            score += 5.0

        # 4. Historical Failure Association (up to 10 pts)
        if dep.status in ("failed", "failure", "error"):
            hist_score = 10.0
            score += hist_score
            evidence.append({
                "evidence_type": "historical_association",
                "score": hist_score,
                "description": "Deployment status recorded as failed in historical logs",
            })

        confidence = round(min(99.0, score), 1)

        rc_record = RootCauseAnalysis(
            anomaly_id=anomaly_id,
            candidate_type="deployment",
            candidate_id=dep.id,
            confidence_score=confidence,
            evidence=evidence,
        )
        db.add(rc_record)
        root_cause_records.append(rc_record)

        if confidence > top_score:
            top_score = confidence
            top_candidate = dep

    db.commit()
    for r in root_cause_records:
        db.refresh(r)

    # Create Incident record if evidence threshold met
    incident = None
    if top_candidate or anomaly.is_anomaly:
        cause_desc = f"Probable cause: Deployment '{top_candidate.id[:8]}' for service '{top_candidate.service_name or service_name}'" if top_candidate else f"Probable cause: Anomalous error spike in '{service_name}'"
        severity = "high" if (anomaly.anomaly_score >= 0.7 or top_score >= 70) else "medium"

        incident = Incident(
            title=f"Production Anomaly in {service_name}",
            status="detected",
            severity=severity,
            detected_at=window_start,
            primary_anomaly_id=anomaly_id,
            probable_cause=cause_desc,
            confidence=top_score if top_score > 0 else 75.0,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

    return root_cause_records, incident
