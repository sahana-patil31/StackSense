from datetime import datetime, timezone
from typing import List
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.ml.features.anomaly_features import aggregate_event_windows


def detect_production_anomalies(
    db: Session,
    window_minutes: int = 5,
    service_name: str = None,
) -> List[Anomaly]:
    """Runs anomaly detection over aggregated event windows and returns detected Anomaly records."""
    windows = aggregate_event_windows(db, window_minutes=window_minutes, service_name=service_name)
    if not windows:
        return []

    # Extract feature matrix: total_events, error_count, critical_count, error_rate
    features = []
    for w in windows:
        features.append([
            float(w["total_events"]),
            float(w["error_count"]),
            float(w["critical_count"]),
            float(w["error_rate"]),
        ])

    X = np.array(features)

    # Use IsolationForest if sample size >= 4, else statistical thresholding
    anomalies: List[Anomaly] = []

    if len(X) >= 4:
        clf = IsolationForest(contamination=0.15, random_state=42)
        clf.fit(X)
        scores = clf.decision_function(X)  # Higher is more normal, lower is more anomalous
        predictions = clf.predict(X)  # -1 = anomaly, 1 = normal

        for idx, w in enumerate(windows):
            is_anom = predictions[idx] == -1 or w["error_rate"] >= 0.35
            norm_score = float(max(0.0, min(1.0, (0.5 - scores[idx]))))
            if is_anom and norm_score < 0.5:
                norm_score = 0.75

            anomaly = Anomaly(
                service_name=w["service_name"],
                window_start=w["window_start"],
                window_end=w["window_end"],
                anomaly_score=round(norm_score, 4),
                is_anomaly=is_anom,
                metrics_snapshot={
                    "total_events": w["total_events"],
                    "error_count": w["error_count"],
                    "critical_count": w["critical_count"],
                    "warning_count": w["warning_count"],
                    "error_rate": w["error_rate"],
                },
                detection_method="IsolationForest",
            )
            db.add(anomaly)
            anomalies.append(anomaly)
    else:
        # Simple statistical thresholding for small dataset
        for w in windows:
            is_anom = w["error_rate"] >= 0.3 or w["critical_count"] >= 3
            score = round(min(1.0, w["error_rate"] + (w["critical_count"] * 0.2)), 4)

            anomaly = Anomaly(
                service_name=w["service_name"],
                window_start=w["window_start"],
                window_end=w["window_end"],
                anomaly_score=score,
                is_anomaly=is_anom,
                metrics_snapshot={
                    "total_events": w["total_events"],
                    "error_count": w["error_count"],
                    "critical_count": w["critical_count"],
                    "warning_count": w["warning_count"],
                    "error_rate": w["error_rate"],
                },
                detection_method="StatisticalThresholding",
            )
            db.add(anomaly)
            anomalies.append(anomaly)

    db.commit()
    for a in anomalies:
        db.refresh(a)

    return anomalies
