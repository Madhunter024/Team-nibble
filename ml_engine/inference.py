import os
import re
import joblib
import numpy as np

SUSPICIOUS_PATTERNS = [
    r"'", r"--", r";", r"OR", r"AND", r"UNION", r"SELECT", r"DROP",
    r"DELETE", r"INSERT", r"UPDATE", r"<script", r"javascript:",
    r"eval\(", r"EXEC", r"BENCHMARK", r"SLEEP"
]

def count_suspicious_tokens(payload: str) -> int:
    """Count occurrence of SQLi/XSS patterns in payload."""
    if not payload:
        return 0
    count = 0
    payload_upper = str(payload).upper()
    for pattern in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, payload_upper, re.IGNORECASE)
        count += len(matches)
    return count

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

_model_artifact = None

def _load_model_artifact():
    """Load model.pkl if available."""
    global _model_artifact
    if _model_artifact is None and os.path.exists(MODEL_PATH):
        try:
            _model_artifact = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"⚠️ Warning: Failed to load model.pkl ({e}). Fallback logic will be used.")
            _model_artifact = None
    return _model_artifact

def detect_anomaly(payload: str, request_rate: int) -> bool:
    """
    Interface Contract:
    Signature: detect_anomaly(payload: str, request_rate: int) -> bool
    Returns True if anomalous/malicious, False if normal.
    """
    payload_str = payload if payload is not None else ""
    payload_len = len(payload_str)
    suspicious_count = count_suspicious_tokens(payload_str)

    if suspicious_count > 0 or request_rate > 50 or payload_len > 4000:
        return True

    artifact = _load_model_artifact()

    if artifact and 'model' in artifact and 'scaler' in artifact:
        try:
            model = artifact['model']
            scaler = artifact['scaler']
            X = np.array([[float(payload_len), float(request_rate), float(suspicious_count)]])
            X_scaled = scaler.transform(X)
            prediction = model.predict(X_scaled)[0]
            # IsolationForest returns -1 for anomaly, 1 for normal
            is_anomaly = bool(prediction == -1 and (suspicious_count > 0 or request_rate > 35 or payload_len > 800))
            return is_anomaly
        except Exception as e:
            pass

    return False

if __name__ == "__main__":
    print("Normal test:", detect_anomaly("username=john", 15))
    print("SQLi test:", detect_anomaly("username=' OR '1'='1", 10))
