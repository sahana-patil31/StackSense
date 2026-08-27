import json
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.ml.features.deployment_features import FEATURE_KEYS


MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "ml_models")


def generate_synthetic_training_data(n_samples: int = 500, random_state: int = 42) -> pd.DataFrame:
    """Generates realistic synthetic historical deployment training dataset for development."""
    np.random.seed(random_state)

    files_changed = np.random.randint(1, 40, size=n_samples)
    lines_changed = np.random.randint(10, 1500, size=n_samples)
    code_entities_changed = np.random.randint(1, 100, size=n_samples)
    services_affected = np.random.choice([1, 2, 3, 4, 5], p=[0.5, 0.25, 0.15, 0.07, 0.03], size=n_samples)
    dependencies_affected = np.random.randint(0, 25, size=n_samples)
    test_coverage = np.random.uniform(0.3, 0.95, size=n_samples)
    hist_failures = np.random.randint(0, 10, size=n_samples)
    hist_incidents = np.random.randint(0, 5, size=n_samples)
    env_prod = np.random.choice([0.0, 1.0], p=[0.3, 0.7], size=n_samples)
    recent_freq = np.random.randint(1, 30, size=n_samples)
    prev_failure_rate = np.random.uniform(0.0, 0.4, size=n_samples)
    import_rels_affected = np.random.randint(0, 30, size=n_samples)

    # Compute risk score probability formula for synthetic labels
    risk_signal = (
        (files_changed / 40.0) * 0.25 +
        (lines_changed / 1500.0) * 0.20 +
        (services_affected / 5.0) * 0.25 +
        (1.0 - test_coverage) * 0.20 +
        prev_failure_rate * 0.25 +
        env_prod * 0.15 +
        np.random.normal(0, 0.1, size=n_samples)
    )

    # Target: 1 = failed deployment, 0 = successful deployment
    target = (risk_signal > 0.55).astype(int)

    df = pd.DataFrame({
        "files_changed": files_changed,
        "lines_changed": lines_changed,
        "code_entities_changed": code_entities_changed,
        "number_of_services_affected": services_affected,
        "number_of_dependencies_affected": dependencies_affected,
        "test_coverage": test_coverage,
        "historical_deployment_failures": hist_failures,
        "historical_incidents_after_deployment": hist_incidents,
        "deployment_environment_prod": env_prod,
        "recent_deployment_frequency": recent_freq,
        "previous_failure_rate_for_repository": prev_failure_rate,
        "number_of_import_relationships_affected": import_rels_affected,
        "deployment_failed": target,
        "is_synthetic": True,
    })

    return df


def train_and_evaluate_model():
    """Trains Random Forest risk model and Logistic Regression baseline, prints metrics, saves artifacts."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    df = generate_synthetic_training_data(n_samples=500, random_state=42)
    X = df[FEATURE_KEYS]
    y = df["deployment_failed"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Baseline: Logistic Regression
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_probs = lr.predict_proba(X_test)[:, 1]

    # Primary: Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_probs = rf.predict_proba(X_test)[:, 1]

    # Evaluation Metrics
    rf_acc = float(accuracy_score(y_test, rf_preds))
    rf_prec = float(precision_score(y_test, rf_preds, zero_division=0))
    rf_rec = float(recall_score(y_test, rf_preds, zero_division=0))
    rf_f1 = float(f1_score(y_test, rf_preds, zero_division=0))
    rf_auc = float(roc_auc_score(y_test, rf_probs))

    lr_acc = float(accuracy_score(y_test, lr_preds))
    lr_auc = float(roc_auc_score(y_test, lr_probs))

    model_filename = os.path.join(MODELS_DIR, "risk_model_v1.joblib")
    meta_filename = os.path.join(MODELS_DIR, "risk_model_v1_meta.json")

    joblib.dump(rf, model_filename)

    metadata = {
        "model_type": "RandomForestClassifier",
        "baseline_model_type": "LogisticRegression",
        "version": "risk_model_v1",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_size": len(df),
        "dataset_source": "synthetic_development_data (is_synthetic=True)",
        "features": FEATURE_KEYS,
        "metrics": {
            "random_forest": {
                "accuracy": round(rf_acc, 4),
                "precision": round(rf_prec, 4),
                "recall": round(rf_rec, 4),
                "f1_score": round(rf_f1, 4),
                "roc_auc": round(rf_auc, 4),
            },
            "logistic_regression": {
                "accuracy": round(lr_acc, 4),
                "roc_auc": round(lr_auc, 4),
            },
        },
    }

    with open(meta_filename, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("=== STACKSENSE DEPLOYMENT RISK MODEL TRAINING ===")
    print(f"Model saved to: {model_filename}")
    print(f"Random Forest Accuracy: {rf_acc:.4f} | F1: {rf_f1:.4f} | ROC-AUC: {rf_auc:.4f}")
    print(f"Logistic Regression Baseline Accuracy: {lr_acc:.4f} | ROC-AUC: {lr_auc:.4f}")
    return metadata


if __name__ == "__main__":
    train_and_evaluate_model()
