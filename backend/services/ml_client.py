import os
import sys
import uuid
import json
import inspect
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add root directory to sys.path to allow importing ml_engine
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from ml_engine.inference import detect_anomaly as ml_detect_anomaly
except ImportError:
    ml_detect_anomaly = None

try:
    from ml_engine.ai_reporter import generate_threat_report as ml_generate_threat_report
except ImportError:
    ml_generate_threat_report = None

try:
    from backend.middleware.rate_limiter import block_ip
    from backend.middleware.redis_rate_limit import tracker_instance
except ImportError:
    from middleware.rate_limiter import block_ip
    from middleware.redis_rate_limit import tracker_instance

logger = logging.getLogger("nibdefender.ml_client")


async def evaluate_request_anomaly(telemetry_data: dict, redis_client=None) -> dict:
    """
    Evaluates request telemetry for anomalies using ML Engine inference:
    1. Runs ML anomaly detection or heuristic fallback.
    2. Computes an anomaly_score (0.0 to 1.0) and threat_type.
    3. If anomaly_score > 0.85, automatically blocks client IP for 24h.
    4. Generates an AI CISO threat report and pushes event to Redis `list:incidents`.
    """
    client_ip = telemetry_data.get("client_ip", "127.0.0.1")
    endpoint = telemetry_data.get("endpoint", "/")
    velocity = telemetry_data.get("request_velocity", 1)
    payload_size = telemetry_data.get("payload_size", 0)
    entropy = telemetry_data.get("header_entropy", 0.0)
    raw_payload = telemetry_data.get("raw_payload", f"endpoint={endpoint}&size={payload_size}")
    is_sqli = telemetry_data.get("is_potential_sqli", False)
    is_xss = telemetry_data.get("is_potential_xss", False)

    # 1. ML Engine Inference Call
    if ml_detect_anomaly is not None:
        try:
            is_anomaly = ml_detect_anomaly(raw_payload, int(velocity))
        except Exception as e:
            logger.warning(f"Error running ML detect_anomaly ({e}). Using heuristic fallback.")
            is_anomaly = velocity > 15 or payload_size > 5000 or is_sqli or is_xss
    else:
        is_anomaly = velocity > 15 or payload_size > 5000 or is_sqli or is_xss

    # 2. Compute Threat Type and Anomaly Score
    threat_type = "NORMAL"
    anomaly_score = 0.15

    if is_sqli:
        threat_type = "SQL_INJECTION"
        anomaly_score = 0.95
        is_anomaly = True
    elif is_xss:
        threat_type = "XSS_ATTACK"
        anomaly_score = 0.90
        is_anomaly = True
    elif velocity > 20:
        threat_type = "HIGH_VELOCITY_DDOS"
        anomaly_score = min(0.99, 0.5 + (velocity / 50.0))
        is_anomaly = True
    elif is_anomaly:
        threat_type = "ISOLATION_FOREST_ANOMALY"
        anomaly_score = 0.88
    elif entropy > 5.2 or payload_size > 10000:
        threat_type = "ANOMALOUS_PAYLOAD"
        anomaly_score = 0.75
        is_anomaly = True

    result = {
        "is_anomaly": is_anomaly,
        "anomaly_score": round(anomaly_score, 4),
        "threat_type": threat_type
    }

    # 3. Autonomous Mitigation & AI Incident Logging if Anomaly Detected
    if is_anomaly:
        action = "FLAGGED"
        if anomaly_score > 0.85:
            action = "BLOCKED"
            await block_ip(redis_client, client_ip, duration_seconds=86400)
            logger.warning(f"IP {client_ip} automatically blocked due to high anomaly score {anomaly_score}.")

        # Generate CISO Incident Report
        if ml_generate_threat_report is not None:
            try:
                ciso_report = await asyncio.to_thread(
                    ml_generate_threat_report, client_ip, threat_type, raw_payload
                )
            except Exception as e:
                ciso_report = (
                    f"[CISO Incident Summary] Flagged high-risk {threat_type} vector originating from IP {client_ip}. "
                    f"Action taken: {action}."
                )
        else:
            ciso_report = (
                f"[CISO Incident Summary] Flagged high-risk {threat_type} vector originating from IP {client_ip}. "
                f"Action taken: {action}."
            )

        incident_record = {
            "id": f"inc_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip": client_ip,
            "endpoint": endpoint,
            "threat_type": threat_type,
            "severity": "CRITICAL" if action == "BLOCKED" else "HIGH",
            "score": anomaly_score,
            "action": action,
            "ciso_report": ciso_report
        }

        # Save to Redis list:incidents
        if redis_client:
            try:
                rec_json = json.dumps(incident_record)
                if inspect.iscoroutinefunction(getattr(redis_client, "lpush", None)):
                    await redis_client.lpush("list:incidents", rec_json)
                    await redis_client.ltrim("list:incidents", 0, 999)
                elif hasattr(redis_client, "lpush"):
                    redis_client.lpush("list:incidents", rec_json)
                    redis_client.ltrim("list:incidents", 0, 999)
            except Exception as e:
                logger.warning(f"Failed to store incident in Redis list:incidents: {e}")

        # Add to ThreatTracker alert log
        tracker_instance.add_alert(
            severity="CRITICAL" if action == "BLOCKED" else "HIGH",
            message=f"{threat_type} detected from {client_ip} (score: {anomaly_score}). Action: {action}."
        )

    return result
