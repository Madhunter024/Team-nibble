import os
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import IsolationForest

def train_sqli_detector(output_path: str):
    """
    Trains a character n-gram TF-IDF + SGDClassifier pipeline for SQL Injection and malicious syntax detection.
    """
    sqli_payloads = [
        "' OR '1'='1",
        "' OR 1=1 --",
        "admin' --",
        "' OR 'a'='a",
        "1; DROP TABLE users",
        "UNION SELECT username, password FROM users",
        "UNION SELECT NULL, NULL, NULL",
        "' UNION SELECT 1, @@version --",
        "1' OR '1'='1' --",
        "<script>alert(1)</script>",
        "javascript:alert('xss')",
        "SELECT * FROM accounts WHERE id = 1 OR 1=1",
        "'; EXEC xp_cmdshell('dir') --",
        "1 AND 1=1",
        "1' AND '1'='1",
        "admin' #",
        "' HAVING 1=1 --",
        "' GROUP BY username HAVING 1=1 --",
        "1 PROCEDURE ANALYSE()",
        "1 OR SLEEP(5)#",
        "1 BENCHMARK(1000000,MD5(1))",
        "ORDER BY 1--",
        "ORDER BY 10--",
        "<img src=x onerror=alert(1)>",
        "'; DELETE FROM logs WHERE 1=1 --",
        "'; UPDATE users SET role='admin' WHERE username='attacker' --",
        "admin' OR '1'='1'/*",
        "1' OR 1=1 LIMIT 1 --",
        "' OR ''='",
        "1' UNION ALL SELECT NULL,NULL,NULL--",
    ]

    benign_payloads = [
        "laptop",
        "smartphone",
        "wireless headphones",
        "username=john_doe&action=login",
        "search?q=python+programming",
        "category=electronics&page=2",
        "user_id=1024",
        "endpoint=/api/v1/search?q=test",
        "hello world",
        "admin",
        "secret123",
        "page=1&limit=20",
        "item_id=abc-123-xyz",
        "filter=active&sort=asc",
        "query=security+gateway",
        "format=json&compress=true",
        "session_token=abc123def456",
        "title=getting+started+with+fastapi",
        "ref=homepage&source=nav",
        "lang=en-US",
        "view=grid&theme=dark",
        "product_name=keyboard",
        "status=success",
        "tags=python,machine-learning,security",
        "comment=Great article! Thanks for sharing.",
        "email=user@example.com",
        "firstname=Alice&lastname=Smith",
        "order_by=date&dir=desc",
        "tab=overview",
        "city=New+York&zip=10001",
    ]

    X = sqli_payloads + benign_payloads
    y = [1] * len(sqli_payloads) + [0] * len(benign_payloads)

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 3), analyzer='char_wb')),
        ('clf', SGDClassifier(loss='log_loss', max_iter=1000, random_state=42))
    ])

    pipeline.fit(X, y)
    joblib.dump(pipeline, output_path)
    print(f"✅ SQLi Classifier successfully trained and saved to: {output_path}")


def train_iso_forest(output_path: str):
    """
    Trains an IsolationForest model on normal request baseline features: [request_velocity, payload_size, header_entropy].
    """
    np.random.seed(42)
    n_samples = 1000

    # Normal baseline feature distributions
    velocity = np.random.uniform(low=1, high=15, size=n_samples)
    payload_size = np.random.uniform(low=10, high=1500, size=n_samples)
    header_entropy = np.random.uniform(low=2.0, high=4.5, size=n_samples)

    X_normal = np.column_stack([velocity, payload_size, header_entropy])

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_normal)

    joblib.dump(model, output_path)
    print(f"✅ IsolationForest Anomaly Detector successfully trained and saved to: {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqli_path = os.path.join(base_dir, "sqli_detector.joblib")
    iso_path = os.path.join(base_dir, "iso_forest.joblib")

    print("🚀 Initializing dual-model offline training pipeline...")
    train_sqli_detector(sqli_path)
    train_iso_forest(iso_path)
    print("✨ Dual-model offline pipeline training complete!")
