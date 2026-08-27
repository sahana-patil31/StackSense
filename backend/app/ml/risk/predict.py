import json
import os
import joblib
import pandas as pd
from typing import Any, Dict, List, Tuple

from app.ml.features.deployment_features import FEATURE_KEYS

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "ml_models")
MODEL_PATH = os.path.join(MODELS_DIR, "risk_model_v1.joblib")


def load_risk_model():
    """Loads saved Random Forest model or returns None."""
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


def calculate_risk_level(risk_score: int) -> str:
    """Classifies 0-100 risk score into risk level string."""
    if risk_score <= 29:
        return "LOW"
    elif risk_score <= 59:
        return "MEDIUM"
    elif risk_score <= 79:
        return "HIGH"
    else:
        return "CRITICAL"


def predict_deployment_risk(feature_snapshot: Dict[str, Any]) -> Tuple[int, str, float, List[Dict[str, Any]], str]:
    """Predicts deployment failure probability and generates risk score, risk level, and contributing factors."""
    model = load_risk_model()
    model_version = "risk_model_v1"

    # Prepare DataFrame matching feature names
    row_data = {k: [feature_snapshot.get(k, 0.0)] for k in FEATURE_KEYS}
    df_feat = pd.DataFrame(row_data)

    if model is not None:
        prob_array = model.predict_proba(df_feat)
        failure_prob = float(prob_array[0][1])
    else:
        # Heuristic fallback if model binary is missing
        f_files = feature_snapshot.get("files_changed", 5)
        f_lines = feature_snapshot.get("lines_changed", 100)
        f_svcs = feature_snapshot.get("number_of_services_affected", 1)
        f_cov = feature_snapshot.get("test_coverage", 0.7)
        raw_prob = (f_files / 40.0) * 0.3 + (f_lines / 1000.0) * 0.3 + (f_svcs / 5.0) * 0.2 + (1.0 - f_cov) * 0.2
        failure_prob = min(0.99, max(0.05, float(raw_prob)))

    risk_score = int(round(failure_prob * 100))
    risk_level = calculate_risk_level(risk_score)

    # Determine contributing factors breakdown
    factors: List[Dict[str, Any]] = []

    files_changed = feature_snapshot.get("files_changed", 0)
    if files_changed > 10:
        factors.append({
            "factor_name": "files_changed",
            "feature_value": files_changed,
            "impact": "HIGH" if files_changed > 20 else "MEDIUM",
            "description": f"{files_changed} files changed in deployment",
        })

    lines_changed = feature_snapshot.get("lines_changed", 0)
    if lines_changed > 300:
        factors.append({
            "factor_name": "lines_changed",
            "feature_value": lines_changed,
            "impact": "HIGH" if lines_changed > 800 else "MEDIUM",
            "description": f"{lines_changed} lines of code modified",
        })

    services_affected = feature_snapshot.get("number_of_services_affected", 1)
    if services_affected > 1:
        factors.append({
            "factor_name": "number_of_services_affected",
            "feature_value": services_affected,
            "impact": "HIGH" if services_affected > 3 else "MEDIUM",
            "description": f"{services_affected} services affected across dependency graph",
        })

    deps_affected = feature_snapshot.get("number_of_dependencies_affected", 0)
    if deps_affected > 5:
        factors.append({
            "factor_name": "number_of_dependencies_affected",
            "feature_value": deps_affected,
            "impact": "MEDIUM",
            "description": f"{deps_affected} dependency relationships affected",
        })

    coverage = feature_snapshot.get("test_coverage", 0.75)
    if coverage < 0.7:
        factors.append({
            "factor_name": "test_coverage",
            "feature_value": f"{int(coverage * 100)}%",
            "impact": "HIGH" if coverage < 0.5 else "MEDIUM",
            "description": f"Test coverage is {int(coverage * 100)}%, below 70% baseline",
        })

    prev_fail_rate = feature_snapshot.get("previous_failure_rate_for_repository", 0.0)
    if prev_fail_rate > 0.1:
        factors.append({
            "factor_name": "previous_failure_rate_for_repository",
            "feature_value": f"{int(prev_fail_rate * 100)}%",
            "impact": "HIGH" if prev_fail_rate > 0.25 else "MEDIUM",
            "description": f"Historical repository failure rate is {int(prev_fail_rate * 100)}%",
        })

    if not factors:
        factors.append({
            "factor_name": "baseline",
            "feature_value": "Normal",
            "impact": "LOW",
            "description": "Standard low-risk deployment metrics",
        })

    return risk_score, risk_level, failure_prob, factors, model_version
