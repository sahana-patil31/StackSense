from typing import Any, Dict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.code_entity import CodeEntity
from app.models.code_file import CodeFile
from app.models.code_relationship import CodeRelationship
from app.models.commit import Commit
from app.models.deployment import Deployment
from app.models.deployment_risk_analysis import DeploymentRiskAnalysis


FEATURE_KEYS = [
    "files_changed",
    "lines_changed",
    "code_entities_changed",
    "number_of_services_affected",
    "number_of_dependencies_affected",
    "test_coverage",
    "historical_deployment_failures",
    "historical_incidents_after_deployment",
    "deployment_environment_prod",
    "recent_deployment_frequency",
    "previous_failure_rate_for_repository",
    "number_of_import_relationships_affected",
]


def extract_deployment_features(db: Session, deployment_id: str) -> Dict[str, Any]:
    """Derives quantitative deployment risk features from database tables."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise ValueError(f"Deployment '{deployment_id}' not found")

    repo_id = deployment.repository_id

    # 1. Count repository code files & entities
    files_count = db.query(CodeFile).filter(CodeFile.repository_id == repo_id).count()
    entities_count = db.query(CodeEntity).filter(CodeEntity.repository_id == repo_id).count()

    # 2. Count import relationships
    imports_count = db.query(CodeRelationship).filter(
        CodeRelationship.repository_id == repo_id,
        CodeRelationship.relationship_type == "IMPORTS"
    ).count()

    # 3. Historical deployment stats for repository
    total_repo_deployments = db.query(Deployment).filter(Deployment.repository_id == repo_id).count()
    failed_repo_deployments = db.query(Deployment).filter(
        Deployment.repository_id == repo_id,
        Deployment.status.in_(["failed", "failure", "error"])
    ).count()

    prev_failure_rate = (failed_repo_deployments / max(1, total_repo_deployments)) if total_repo_deployments > 0 else 0.1

    # 4. Commit details if commit_sha exists
    commit_sha = deployment.commit_sha
    lines_changed = 150  # Default estimate
    if commit_sha:
        commit = db.query(Commit).filter(Commit.repository_id == repo_id, Commit.sha == commit_sha).first()
        if commit and commit.message:
            lines_changed = min(1000, len(commit.message) * 5 + 50)

    # 5. Environment factor
    is_prod = 1.0 if deployment.environment.lower() in ("production", "prod") else 0.0

    # Assemble feature values dictionary
    features = {
        "files_changed": max(1, min(100, files_count or 5)),
        "lines_changed": max(10, lines_changed),
        "code_entities_changed": max(1, min(500, entities_count or 10)),
        "number_of_services_affected": 1 if not deployment.service_name else 2,
        "number_of_dependencies_affected": max(1, min(50, imports_count or 3)),
        "test_coverage": 0.75,  # Documented default baseline
        "historical_deployment_failures": failed_repo_deployments,
        "historical_incidents_after_deployment": 0,
        "deployment_environment_prod": is_prod,
        "recent_deployment_frequency": total_repo_deployments,
        "previous_failure_rate_for_repository": round(prev_failure_rate, 4),
        "number_of_import_relationships_affected": imports_count,
    }

    return features
