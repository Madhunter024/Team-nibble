import time
import random
import requests
import sys

TARGET_BASE_URL = "http://localhost:8000"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "NibdefenderAttackerBot/1.0",
    "sqlmap/1.7.2#stable (https://sqlmap.org)",
    "Nikto/2.1.6",
    "Python-urllib/3.10"
]

MALICIOUS_PAYLOADS = [
    {"username": "' OR '1'='1", "password": "password123"},
    {"username": "admin' UNION SELECT username, password FROM users--", "password": "1"},
    {"username": "<script>alert('XSS_ATTACK')</script>", "password": "test"},
    {"username": "admin; DROP TABLE logs;--", "password": "drop"},
]

def send_legitimate_request():
    """Send normal request to ping endpoint."""
    try:
        res = requests.get(f"{TARGET_BASE_URL}/api/v1/public/ping", timeout=2)
        print(f"[Legitimate Traffic] Status {res.status_code} | Headers: {res.headers.get('X-RateLimit-Remaining', 'N/A')} remaining")
    except Exception as e:
        print(f"[Legitimate Traffic Error] {e}")

def send_attack_payload():
    """Send malicious SQLi/XSS payload to login endpoint."""
    payload = random.choice(MALICIOUS_PAYLOADS)
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        res = requests.post(f"{TARGET_BASE_URL}/api/v1/login", json=payload, headers=headers, timeout=2)
        print(f"🔥 [MALICIOUS PAYLOAD SENT] Status {res.status_code} | Payload: {payload['username']}")
    except Exception as e:
        print(f"🔥 [Attack Error] {e}")

def send_ddos_burst(count=30):
    """Spam high-velocity rapid requests to trigger rate limiter."""
    print(f"⚡ [DDoS Burst Attack] Firing {count} rapid requests...")
    for i in range(count):
        try:
            res = requests.get(f"{TARGET_BASE_URL}/api/v1/public/ping", timeout=1)
            if res.status_code == 429:
                print(f"⛔ [RATE LIMIT TRIGGERED] Request #{i+1}: 429 Too Many Requests (Blocked by Redis Rate Limiter!)")
                break
        except Exception:
            pass

def main():
    print("==================================================")
    print("🏴‍☠️ Nibdefender Attacker Simulation Suite Started")
    print(f"Targeting: {TARGET_BASE_URL}")
    print("Press Ctrl+C to terminate the attack loop.")
    print("==================================================\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n--- [Attack Wave #{iteration}] ---")
            
            # 1. Normal background request
            send_legitimate_request()
            time.sleep(0.5)

            # 2. Randomly trigger malicious payload attack
            if random.random() < 0.6:
                send_attack_payload()
                time.sleep(0.5)

            # 3. Randomly trigger DDoS rate-limit spam burst
            if iteration % 4 == 0:
                send_ddos_burst(count=40)

            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n🛑 Attacker simulation terminated by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
