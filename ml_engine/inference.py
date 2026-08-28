import os
import joblib
import numpy as np
from typing import Dict, Any

class AnomalyDetector:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.dirname(__file__)

        self.model_path = os.path.join(model_dir, "isolation_forest.pkl")
        self.scaler_path = os.path.join(model_dir, "scaler.pkl")
        
        self.model = None
        self.scaler = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Load trained model and scaler if present, else warn."""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print("🌲 IsolationForest model and scaler loaded successfully.")
        else:
            print("⚠️ Model files not found. Run train_model.py first to generate .pkl artifacts.")

    def predict_anomaly(self, req_frequency: float, payload_size: float, header_entropy: float, error_rate: float) -> Dict[str, Any]:
        """
        Predict whether request parameters indicate an anomaly.
        Returns prediction status and raw decision score.
        """
        if not self.model or not self.scaler:
            # Fallback heuristic if model not trained yet
            is_anomaly = req_frequency > 100 or payload_size > 10000 or header_entropy > 5.0
            return {
                "is_anomaly": is_anomaly,
                "anomaly_score": 0.85 if is_anomaly else 0.10,
                "status": "HEURISTIC_FALLBACK"
            }

        features = np.array([[req_frequency, payload_size, header_entropy, error_rate]])
        scaled_features = self.scaler.transform(features)

        # IsolationForest returns -1 for anomalies, 1 for normal
        prediction = self.model.predict(scaled_features)[0]
        score = self.model.decision_function(scaled_features)[0]

        # Convert decision function to normalized 0.0 - 1.0 anomaly score
        normalized_score = float(1.0 / (1.0 + np.exp(score)))

        return {
            "is_anomaly": bool(prediction == -1),
            "anomaly_score": round(normalized_score, 4),
            "status": "ANOMALOUS" if prediction == -1 else "NORMAL"
        }

if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # Test normal request
    normal_sample = detector.predict_anomaly(req_frequency=12, payload_size=400, header_entropy=3.1, error_rate=0.01)
    print("Normal Sample Test:", normal_sample)

    # Test suspicious burst request
    attack_sample = detector.predict_anomaly(req_frequency=350, payload_size=25000, header_entropy=6.8, error_rate=0.75)
    print("Attack Sample Test:", attack_sample)
