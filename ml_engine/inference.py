import os
import joblib
import numpy as np
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger("nibdefender.ml_inference")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ISO_MODEL_PATH = os.path.join(BASE_DIR, "iso_forest.joblib")
TRANSFORMERS_MODEL_NAME = "cssupport/mobilebert-sql-injection-detect"

_iso_forest = None
_tokenizer = None
_hf_model = None
_hf_load_failed = False
_model_lock = threading.Lock()


def _load_iso_forest():
    """Safely loads iso_forest.joblib using relative path resolution."""
    global _iso_forest
    if _iso_forest is None and os.path.exists(ISO_MODEL_PATH):
        try:
            _iso_forest = joblib.load(ISO_MODEL_PATH)
        except Exception as e:
            logger.warning(f"Failed to load iso_forest.joblib from {ISO_MODEL_PATH}: {e}")
            _iso_forest = None


def _load_mobilebert():
    """
    Lazy-loads Hugging Face 'cssupport/mobilebert-sql-injection-detect'
    model and tokenizer in a thread-safe manner.
    """
    global _tokenizer, _hf_model, _hf_load_failed
    if _tokenizer is None and not _hf_load_failed:
        with _model_lock:
            if _tokenizer is None and not _hf_load_failed:
                try:
                    import torch
                    from transformers import AutoTokenizer, AutoModelForSequenceClassification

                    logger.info(f"Loading MobileBERT SQL Injection model ({TRANSFORMERS_MODEL_NAME})...")
                    try:
                        _tokenizer = AutoTokenizer.from_pretrained(TRANSFORMERS_MODEL_NAME)
                    except Exception:
                        from transformers import MobileBertTokenizer
                        _tokenizer = MobileBertTokenizer.from_pretrained("google/mobilebert-uncased")

                    _hf_model = AutoModelForSequenceClassification.from_pretrained(TRANSFORMERS_MODEL_NAME)
                    _hf_model.eval()
                    logger.info("✅ MobileBERT SQL Injection model loaded successfully.")
                except Exception as e:
                    logger.warning(f"MobileBERT model load warning (will fallback to heuristic SQLi inspection): {e}")
                    _hf_load_failed = True


def detect_threat_locally(telemetry: dict, raw_payload: str = "") -> dict:
    """
    Perform 100% local, self-contained ML threat detection inference using
    MobileBERT (for SQL Injection) and IsolationForest (for API request anomaly detection).

    Returns:
    {
        "is_anomaly": bool,
        "anomaly_score": float,
        "threat_type": str,
        "sqli_detected": bool,
        "confidence": float,
        "inference_engine": "MobileBERT + IsolationForest"
    }
    """
    _load_iso_forest()

    telemetry = telemetry or {}
    if not raw_payload:
        raw_payload = str(telemetry.get("raw_payload", "") or telemetry.get("endpoint", "") or "")

    sqli_detected = False
    confidence = 0.0

    # 1. MobileBERT SQL Injection Inference
    if raw_payload and not _hf_load_failed:
        _load_mobilebert()
        if _hf_model is not None and _tokenizer is not None:
            try:
                import torch
                inputs = _tokenizer(raw_payload, return_tensors="pt", truncation=True, max_length=128)
                with torch.no_grad():
                    outputs = _hf_model(**inputs)
                    logits = outputs.logits
                    probs = torch.softmax(logits, dim=-1)[0]
                    
                    pred_class = int(torch.argmax(probs).item())
                    if len(probs) > 1:
                        # Class 1 is SQLi in cssupport/mobilebert-sql-injection-detect
                        sqli_prob = float(probs[1].item())
                        sqli_detected = bool(sqli_prob > 0.5 or pred_class == 1)
                        confidence = sqli_prob if sqli_detected else float(probs[0].item())
                    else:
                        sqli_prob = float(probs[0].item())
                        sqli_detected = bool(sqli_prob > 0.5)
                        confidence = sqli_prob
            except Exception as e:
                logger.debug(f"MobileBERT inference exception: {e}")

    # Fallback heuristic inspection if transformer unavailable or cold-start fallback
    lower_payload = raw_payload.lower()
    known_sqli_patterns = [
        "' or '1'='1", "union select", "drop table", "or 1=1", "admin' --",
        "select * from", "<script>", "javascript:", "'; exec", "sleep("
    ]
    if any(pattern in lower_payload for pattern in known_sqli_patterns):
        sqli_detected = True
        confidence = max(confidence, 0.98)

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

    # 3. Combine Evaluation Rules
    is_anomaly = bool(sqli_detected or iso_pred == -1)

    threat_type = "NORMAL"
    if sqli_detected:
        threat_type = "SQL_INJECTION"
    elif velocity > 30:
        threat_type = "HIGH_VELOCITY_DDOS"
    elif iso_pred == -1:
        threat_type = "ISOLATION_FOREST_ANOMALY"

    # Compute normalized anomaly score (0.0 to 1.0)
    if threat_type == "SQL_INJECTION":
        anomaly_score = max(confidence, 0.88)
    elif threat_type == "HIGH_VELOCITY_DDOS":
        anomaly_score = min(0.99, 0.6 + (velocity / 50.0))
    elif iso_pred == -1:
        anomaly_score = min(0.95, max(0.75, 0.85 - decision_score))
    else:
        anomaly_score = max(0.12, round(confidence * 0.5, 4))

    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": round(float(anomaly_score), 4),
        "threat_type": threat_type,
        "sqli_detected": bool(sqli_detected),
        "confidence": round(float(confidence), 4),
        "inference_engine": "MobileBERT + IsolationForest"
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
