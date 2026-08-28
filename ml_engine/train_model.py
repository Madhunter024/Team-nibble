import os
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

SUSPICIOUS_PATTERNS = [
    r"'", r"--", r";", r"OR", r"AND", r"UNION", r"SELECT", r"DROP",
    r"DELETE", r"INSERT", r"UPDATE", r"<script", r"javascript:",
    r"eval\(", r"EXEC", r"BENCHMARK", r"SLEEP"
]

def count_suspicious_tokens(payload: str) -> int:
    """Count occurrence of SQLi/XSS suspicious patterns in payload."""
    if not payload:
        return 0
    count = 0
    payload_upper = str(payload).upper()
    for pattern in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, payload_upper, re.IGNORECASE)
        count += len(matches)
    return count

def generate_synthetic_data(num_samples: int = 1500) -> pd.DataFrame:
    """
    Generate mock normal vs anomalous API payload data:
    - Normal: short payloads, low request rates, 0 suspicious tokens.
    - Anomalous: long payloads, high rate spikes, SQLi/XSS tokens.
    """
    np.random.seed(42)
    n_normal = int(num_samples * 0.85)
    n_anomaly = num_samples - n_normal

    # Normal traffic
    normal_lengths = np.random.normal(loc=120, scale=40, size=n_normal).clip(10, 500)
    normal_rates = np.random.normal(loc=12, scale=5, size=n_normal).clip(1, 35)
    normal_tokens = np.zeros(n_normal)

    # Anomalous traffic
    anomaly_lengths = np.random.uniform(low=800, high=50000, size=n_anomaly)
    anomaly_rates = np.random.uniform(low=80, high=1000, size=n_anomaly)
    anomaly_tokens = np.random.randint(low=1, high=10, size=n_anomaly)

    df_normal = pd.DataFrame({
        'payload_len': normal_lengths,
        'request_rate': normal_rates,
        'suspicious_tokens': normal_tokens,
        'label': 0
    })

    df_anomaly = pd.DataFrame({
        'payload_len': anomaly_lengths,
        'request_rate': anomaly_rates,
        'suspicious_tokens': anomaly_tokens,
        'label': 1
    })

    df = pd.concat([df_normal, df_anomaly], ignore_index=True)
    return df.sample(frac=1.0, random_state=42).reset_index(drop=True)

def train_and_save_model() -> str:
    """Train IsolationForest model and save to ml_engine/model.pkl."""
    print("🤖 Generating mock normal and anomalous payload data...")
    df = generate_synthetic_data()

    feature_cols = ['payload_len', 'request_rate', 'suspicious_tokens']
    X = df[feature_cols]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("🌲 Training IsolationForest Anomaly Detection Model...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.15,
        random_state=42
    )
    model.fit(X_scaled)

    artifact = {
        'model': model,
        'scaler': scaler,
        'feature_cols': feature_cols
    }

    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    joblib.dump(artifact, model_path)
    print(f"✅ Model saved successfully to {model_path}")
    return model_path

if __name__ == "__main__":
    train_and_save_model()
