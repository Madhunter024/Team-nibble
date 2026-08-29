# 🧠 Nibdefender Local Machine Learning Engine

The **Nibdefender ML Engine** provides sub-15ms, 100% offline threat detection for web applications and API gateways. It operates completely locally using Scikit-Learn pipelines serialized with Joblib, removing all external cloud API dependencies and ensuring privacy, resilience, and ultra-low latency.

---

## 📐 Dual-Model Architecture

The engine combines two specialized machine learning models to detect both payload signatures and behavioral traffic anomalies:

### 1. SQL Injection & XSS Payload Classifier (`sqli_detector.joblib`)
- **Pipeline Architecture:** `TfidfVectorizer(ngram_range=(1, 3), analyzer='char_wb', max_features=3000, sublinear_tf=True)` + `SGDClassifier(loss='log_loss', max_iter=1000, random_state=42)`
- **Training Data:** Rich synthetic dataset containing SQL injection vectors (`' OR '1'='1`, `UNION SELECT`, `DROP TABLE`, `<script>`) and benign search/API parameters.
- **Inference Latency:** **~2.8 ms**
- **Output:** Classification probability (0.0 to 1.0) for SQLi / XSS payload threats.

### 2. Traffic Velocity & Metadata Anomaly Detector (`iso_forest.joblib`)
- **Model Architecture:** `IsolationForest(n_estimators=30, contamination=0.05, random_state=42)`
- **Features Extracted:**
  - `request_velocity`: Requests per minute from the source IP.
  - `payload_size`: Length of HTTP request body / URL string in bytes.
  - `header_entropy`: Shannon entropy score of incoming HTTP request headers.
- **Inference Latency:** **~5.5 ms**
- **Output:** Anomaly score (-1 for anomalous, +1 for normal) converted to normalized threat probability.

---

## ⚡ Performance & Benchmark Metrics

Target benchmark over 1,000 live inferences:

| Metric | Target | Measured Performance |
| :--- | :--- | :--- |
| **Average Latency** | < 15.0 ms | **9.35 ms** |
| **P50 (Median)** | < 15.0 ms | **8.88 ms** |
| **P95 Latency** | < 15.0 ms | **12.41 ms** |
| **P99 Latency** | < 15.0 ms | **14.11 ms** |
| **Offline Dependencies** | 0 external calls | **100% Local (Joblib)** |

---

## 🛠️ Setup & Training Instructions

### 1. Environment Installation
```bash
cd ml_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Train and Export Models
Train both models and save serialized `.joblib` artifacts:
```bash
python train_model.py
```
*Outputs:*
- `sqli_detector.joblib`
- `iso_forest.joblib`

### 3. Run Verification Benchmark
```bash
python inference.py
```

---

## 🔄 Dynamic API Traffic Sampling

The ML engine integrates with FastAPI middleware (`TelemetryMiddleware`) to support dynamic sampling rates:
- **25%** — *Max Efficiency* (75% CPU compute saved)
- **50%** — *Balanced Mode* (50% CPU compute saved)
- **75%** — *High Inspection* (25% CPU compute saved)
- **100%** — *Full Inspection* (100% requests monitored)

*Note: Critical threat signatures (SQLi / XSS / DDoS rate limit breaches) are always 100% inspected regardless of active sampling rate.*
