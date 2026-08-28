import time
import random
import requests
import sys

TARGET_BASE_URL = "http://localhost:8000"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "ThreatBot/1.0",
    "sqlmap/1.7.2#stable (https://sqlmap.org)",
    "Nikto/2.1.6",
    "Python-requests/2.31.0"
]

SQLI_PAYLOADS = [
    "' OR 1=1 --",
    "' OR '1'='1",
    "admin' UNION SELECT username, password FROM users--",
    "<script>alert('XSS_TEST')</script>",
    "admin; DROP TABLE logs;--"
]

def send_normal_request():
    """Send normal legitimate requests to dummy endpoints."""
    url = f"{TARGET_BASE_URL}/api/v1/data"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        res = requests.get(url, headers=headers, timeout=2)
        print(f"🟢 [NORMAL REQUEST] Path: /api/v1/data | Status: {res.status_code}")
    except Exception as e:
        print(f"🔴 [Normal Request Failed] {e}")

def send_sqli_attack():
    """Send SQL injection attack string to login endpoint."""
    url = f"{TARGET_BASE_URL}/api/v1/login"
    payload = {
        "username": random.choice(SQLI_PAYLOADS),
        "password": "password123"
    }
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=2)
        print(f"🔥 [SQLi ATTACK SENT] Payload: '{payload['username']}' | Status: {res.status_code}")
    except Exception as e:
        print(f"🔥 [Attack Request Error] {e}")

def send_burst_attack(count: int = 55):
    """Spam rapid requests to trigger 50 req/min rate limit and IP block."""
    print(f"\n⚡ [BURST ATTACK] Rapidly firing {count} requests to trigger rate limit (50 req/min)...")
    url = f"{TARGET_BASE_URL}/api/v1/data"
    blocked_triggered = False

    for i in range(1, count + 1):
        try:
            res = requests.get(url, timeout=1)
            if res.status_code == 429:
                print(f"⛔ [RATE LIMIT & BLOCK TRIGGERED] Request #{i}: HTTP 429 - {res.json().get('detail', 'Blocked')}")
                blocked_triggered = True
                break
            else:
                if i % 10 == 0:
                    print(f"   Sent {i}/{count} requests (Status {res.status_code})...")
        except Exception as e:
            print(f"   Request #{i} error: {e}")

    if not blocked_triggered:
        print("   Burst completed. Checking status...")

def main():
    print("=" * 60)
    print("🏴‍☠️ AI-Powered API Threat Defender - Attacker Simulation")
    print(f"Targeting backend at: {TARGET_BASE_URL}")
    print("Press Ctrl+C at any time to stop.")
    print("=" * 60 + "\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n--- Wave #{iteration} ---")

            # 1. Send normal legitimate requests
            send_normal_request()
            time.sleep(0.5)

            # 2. Send malicious SQL injection attempt
            send_sqli_attack()
            time.sleep(0.5)

            # 3. Trigger rapid high-rate burst on wave 3
            if iteration % 3 == 0:
                send_burst_attack(count=55)

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
