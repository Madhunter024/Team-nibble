import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def generate_synthetic_data(num_samples=1000):
    """
    Generate synthetic HTTP request metric features:
    - req_frequency: requests per minute
    - payload_size: bytes
    - header_entropy: complexity measure of headers
    - error_rate: percentage of 4xx/5xx responses
    """
    np.random.seed(42)

    # Legitimate Normal Traffic (~90%)
    n_normal = int(num_samples * 0.9)
    normal_req_freq = np.random.normal(loc=15, scale=5, size=n_normal)
    normal_payload = np.random.normal(loc=450, scale=120, size=n_normal)
    normal_entropy = np.random.normal(loc=3.2, scale=0.4, size=n_normal)
    normal_error_rate = np.random.uniform(low=0.0, high=0.05, size=n_normal)

    # Anomaly / Attack Traffic (~10%)
    n_anomalous = num_samples - n_normal
    anomaly_req_freq = np.random.uniform(low=150, high=800, size=n_anomalous)
    anomaly_payload = np.random.uniform(low=5000, high=50000, size=n_anomalous)
    anomaly_entropy = np.random.uniform(low=5.5, high=8.0, size=n_anomalous)
    anomaly_error_rate = np.random.uniform(low=0.40, high=1.0, size=n_anomalous)

    # Combine into DataFrames
    df_normal = pd.DataFrame({
        'req_frequency': normal_req_freq,
        'payload_size': normal_payload,
        'header_entropy': normal_entropy,
        'error_rate': normal_error_rate,
        'label': 0
    })

    df_anomaly = pd.DataFrame({
        'req_frequency': anomaly_req_freq,
        'payload_size': anomaly_payload,
        'header_entropy': anomaly_entropy,
        'error_rate': anomaly_error_rate,
        'label': 1
    })

    df = pd.concat([df_normal, df_anomaly], ignore_index=True)
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    return df

def train_and_save_model():
    print("🤖 Generating synthetic network request dataset...")
    data = generate_synthetic_data()
    csv_path = os.path.join(os.path.dirname(__file__), "synthetic_requests.csv")
    data.to_csv(csv_path, index=False)
    print(f"📁 Dataset saved to {csv_path}")

    feature_cols = ['req_frequency', 'payload_size', 'header_entropy', 'error_rate']
    X = data[feature_cols]

    # Preprocessing
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train IsolationForest
    print("🌲 Training IsolationForest Anomaly Detection Model...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )
    model.fit(X_scaled)

    # Save model artifacts
    model_path = os.path.join(os.path.dirname(__file__), "isolation_forest.pkl")
    scaler_path = os.path.join(os.path.dirname(__file__), "scaler.pkl")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    print(f"✅ Model successfully saved to {model_path}")
    print(f"✅ Scaler saved to {scaler_path}")

if __name__ == "__main__":
    train_and_save_model()
