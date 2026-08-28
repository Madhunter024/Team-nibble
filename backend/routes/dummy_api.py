from fastapi import APIRouter, Request, Depends, Query, Body, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

try:
    from backend.middleware.jwt_auth import verify_jwt, create_access_token
    from backend.middleware.redis_rate_limit import tracker_instance
except ImportError:
    from middleware.jwt_auth import verify_jwt, create_access_token
    from middleware.redis_rate_limit import tracker_instance



router = APIRouter(prefix="/api/v1", tags=["Threat Metrics & Security Target"])

# --- Pydantic Schemas for API Contract ---

class ThreatLogItem(BaseModel):
    id: str = Field(..., example="inc_1001")
    ip: str = Field(..., example="192.168.1.105")
    threat_type: str = Field(..., example="SQL_INJECTION")
    severity: str = Field(..., example="CRITICAL")  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: str = Field(..., example="2026-08-28T17:42:00Z")
    ai_summary: str = Field(..., example="Detected SQL injection attempt in login username parameter.")
    payload: Optional[str] = Field(None, example="username=' OR '1'='1")

class EngineStatus(BaseModel):
    redis_token_bucket: str = Field("ACTIVE", example="ACTIVE")
    pyjwt_token_guard: str = Field("STRICT", example="STRICT")
    isolation_forest_ml: str = Field("TRAINED", example="TRAINED")
    langchain_reporter: str = Field("READY", example="READY")

class ThreatMetricsResponse(BaseModel):
    total_requests_monitored: int = Field(..., example=148920)
    velocity_peak_percentage: float = Field(..., example=14.2)
    active_ip_blocks: int = Field(..., example=42)
    ml_anomaly_index: float = Field(..., example=0.94)
    high_risk_attacks_count: int = Field(..., example=3)
    engine_status: EngineStatus
    incidents: List[ThreatLogItem]

# In-memory incident log store for dashboard feeding
INCIDENT_LOGS: List[Dict[str, Any]] = [
    {
        "id": "inc_1001",
        "ip": "192.168.1.105",
        "threat_type": "SQL_INJECTION",
        "severity": "CRITICAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_summary": "High entropy SQL syntax detected in auth payload. Automated IP ban enforced.",
        "payload": "username=' UNION SELECT password FROM users--"
    },
    {
        "id": "inc_1002",
        "ip": "10.0.4.12",
        "threat_type": "RATE_LIMIT_EXCEEDED",
        "severity": "HIGH",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_summary": "DDoS velocity burst detected (340 req/min). Redis rate-limiter activated.",
        "payload": "GET /api/v1/public/ping x340"
    }
]

@router.get("/data")
async def get_data():
    """Dummy data endpoint for testing normal requests."""
    return {"message": "Data retrieved successfully", "status": "active"}

@router.get("/public/ping")
async def ping():
    """Public health check endpoint."""
    return {"status": "ok", "message": "Nibdefender security core online"}

@router.post("/login")
async def login(credentials: Dict[str, Any] = Body(...), request: Request = None):
    """
    Fake Login Endpoint (Target for Brute-force & SQLi attacks).
    """
    username = str(credentials.get("username", ""))
    password = str(credentials.get("password", ""))
    client_ip = request.client.host if request and request.client else "192.168.1.105"

    # Basic honeypot response
    if username == "admin" and password == "secret123":
        token = create_access_token({"sub": username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}

    # Log suspicious attempt if sql injection detected in input
    sql_patterns = ["' OR '1'='1", "' OR 1=1", "UNION SELECT", "DROP TABLE", "--", "';"]
    if any(pattern in username for pattern in sql_patterns) or any(pattern in password for pattern in sql_patterns):
        new_inc = {
            "id": f"inc_{len(INCIDENT_LOGS) + 1001}",
            "ip": client_ip,
            "threat_type": "SQL_INJECTION",
            "severity": "HIGH",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ai_summary": f"SQL Injection payload detected from IP {client_ip}: username={username}",
            "payload": f"username={username}"
        }
        INCIDENT_LOGS.insert(0, new_inc)
        
        # Record alert in ThreatTracker
        tracker_instance.add_alert(
            severity="HIGH",
            message=f"SQL Injection attack detected from IP {client_ip} on /api/v1/login"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malicious syntax detected by WAF engine."
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@router.get("/user/profile")
async def get_profile(payload: dict = Depends(verify_jwt)):
    """Protected Endpoint requiring valid JWT token."""
    return {
        "user_id": 1042,
        "username": payload.get("sub", "user"),
        "role": payload.get("role", "member"),
        "email": "target_user@nibdefender.io"
    }

@router.get("/payment/transfer")
async def transfer_money(
    amount: float = Query(...),
    recipient: str = Query(...),
    payload: dict = Depends(verify_jwt)
):
    """Protected financial endpoint targeted by attackers."""
    return {
        "status": "success",
        "transaction_id": "tx_9981247",
        "amount": amount,
        "recipient": recipient
    }

@router.get("/logs/incidents")
async def get_incident_logs():
    """Retrieve simulated incident logs for ThreatFeed UI."""
    return {"incidents": INCIDENT_LOGS}

@router.get("/threat-metrics", response_model=ThreatMetricsResponse)
async def get_threat_metrics():
    """
    Finalized JSON endpoint for real-time security dashboard metrics & incident logs.
    Shared contract between Backend, Frontend, and ML model pipeline.
    """
    # Transform in-memory dicts into Pydantic ThreatLogItems
    incident_items = [
        ThreatLogItem(
            id=item["id"],
            ip=item["ip"],
            threat_type=item["threat_type"],
            severity=item["severity"],
            timestamp=item["timestamp"],
            ai_summary=item["ai_summary"],
            payload=item.get("payload")
        ) for item in INCIDENT_LOGS
    ]

    return ThreatMetricsResponse(
        total_requests_monitored=148920 + len(INCIDENT_LOGS) * 15,
        velocity_peak_percentage=14.2,
        active_ip_blocks=42 + len([i for i in INCIDENT_LOGS if i['severity'] == 'CRITICAL']),
        ml_anomaly_index=0.94,
        high_risk_attacks_count=len(INCIDENT_LOGS),
        engine_status=EngineStatus(
            redis_token_bucket="ACTIVE",
            pyjwt_token_guard="STRICT",
            isolation_forest_ml="TRAINED",
            langchain_reporter="READY"
        ),
        incidents=incident_items
    )

