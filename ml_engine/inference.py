import os
import joblib
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger("nibdefender.ml_inference")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLI_MODEL_PATH = os.path.join(BASE_DIR, "sqli_detector.joblib")
ISO_MODEL_PATH = os.path.join(BASE_DIR, "iso_forest.joblib")

_sqli_pipeline = None
_iso_forest = None


def _load_models():
    """Safely loads sqli_detector.joblib and iso_forest.joblib using relative path resolution."""
    global _sqli_pipeline, _iso_forest
    if _sqli_pipeline is None and os.path.exists(SQLI_MODEL_PATH):
        try:
            _sqli_pipeline = joblib.load(SQLI_MODEL_PATH)
        except Exception as e:
            logger.warning(f"Failed to load sqli_detector.joblib from {SQLI_MODEL_PATH}: {e}")
            _sqli_pipeline = None

    if _iso_forest is None and os.path.exists(ISO_MODEL_PATH):
        try:
            _iso_forest = joblib.load(ISO_MODEL_PATH)
        except Exception as e:
            logger.warning(f"Failed to load iso_forest.joblib from {ISO_MODEL_PATH}: {e}")
            _iso_forest = None


def detect_threat_locally(telemetry: dict, raw_payload: str = "") -> dict:
    """
    Perform 100% local, self-contained ML threat detection inference using Scikit-Learn.
    
    Returns structured dictionary:
    {
        "is_anomaly": bool,
        "anomaly_score": float,
        "threat_type": str,
        "inference_engine": "Local Scikit-Learn Engine"
    }
    """
    _load_models()

    telemetry = telemetry or {}
    if not raw_payload:
        raw_payload = str(telemetry.get("raw_payload", "") or telemetry.get("endpoint", "") or "")

    # 1. SQL Injection / Malicious Syntax Probability
    sqli_prob = 0.0
    if _sqli_pipeline is not None and raw_payload:
        try:
            probs = _sqli_pipeline.predict_proba([raw_payload])[0]
            classes = list(_sqli_pipeline.classes_)
            if 1 in classes:
                sqli_prob = float(probs[classes.index(1)])
        except Exception as e:
            logger.debug(f"SQLi model prediction error: {e}")

    # Fallback heuristic check if keyword present
    lower_payload = raw_payload.lower()
    known_attack_patterns = ["' or '1'='1", "union select", "drop table", "<script>", "javascript:", "or 1=1", "admin' --"]
    if any(pattern in lower_payload for pattern in known_attack_patterns):
        sqli_prob = max(sqli_prob, 0.95)

    # 2. IsolationForest Anomaly Prediction on [request_velocity, payload_size, header_entropy]
    velocity = float(telemetry.get("request_velocity", 1))
    payload_size = float(telemetry.get("payload_size", len(raw_payload)))
    header_entropy = float(telemetry.get("header_entropy", 3.0))

    iso_pred = 1
    decision_score = 0.0

    if _iso_forest is not None:
        try:
            features = np.array([[velocity, payload_size, header_entropy]])
            iso_pred = int(_iso_forest.predict(features)[0])  # -1 for anomaly, 1 for normal
            decision_score = float(_iso_forest.decision_function(features)[0])
        except Exception as e:
            logger.debug(f"IsolationForest prediction error: {e}")

    if velocity > 30 or payload_size > 5000:
        iso_pred = -1

    # 3. Combine evaluation rules: Flag as anomaly if sqli_prob > 0.7 or iso_pred == -1
    is_anomaly = bool(sqli_prob > 0.7 or iso_pred == -1)

    threat_type = "NORMAL"
    if sqli_prob > 0.7:
        threat_type = "SQL_INJECTION"
    elif velocity > 30:
        threat_type = "HIGH_VELOCITY_DDOS"
    elif iso_pred == -1:
        threat_type = "ISOLATION_FOREST_ANOMALY"

    # Compute normalized anomaly score (0.0 to 1.0)
    if threat_type == "SQL_INJECTION":
        anomaly_score = max(sqli_prob, 0.85)
    elif threat_type == "HIGH_VELOCITY_DDOS":
        anomaly_score = min(0.99, 0.6 + (velocity / 50.0))
    elif iso_pred == -1:
        anomaly_score = min(0.95, max(0.75, 0.85 - decision_score))
    else:
        anomaly_score = max(0.15, round(sqli_prob, 4))

    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": round(float(anomaly_score), 4),
        "threat_type": threat_type,
        "inference_engine": "Local Scikit-Learn Engine"
    }


def detect_anomaly(payload: str, request_rate: int) -> bool:
    """Backward compatibility wrapper."""
    telemetry = {
        "request_velocity": request_rate,
        "payload_size": len(payload or ""),
        "header_entropy": 3.0
    }
    result = detect_threat_locally(telemetry, raw_payload=payload)
    return result["is_anomaly"]


if __name__ == "__main__":
    test_telemetry_normal = {"request_velocity": 5, "payload_size": 120, "header_entropy": 3.2}
    test_telemetry_ddos = {"request_velocity": 120, "payload_size": 250, "header_entropy": 3.5}
    
    print("Normal test:", detect_threat_locally(test_telemetry_normal, "search?q=laptop"))
    print("SQLi test:", detect_threat_locally(test_telemetry_normal, "username=' OR '1'='1"))
    print("DDoS test:", detect_threat_locally(test_telemetry_ddos, "search?q=ddos"))
