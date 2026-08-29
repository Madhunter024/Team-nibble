import json
import inspect
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Query, Body, HTTPException, status
from pydantic import BaseModel, Field

try:
    from backend.middleware.rate_limiter import get_client_ip
    from backend.middleware.auth import create_access_token
    from backend.middleware.redis_rate_limit import tracker_instance
except ImportError:
    from middleware.rate_limiter import get_client_ip
    from middleware.auth import create_access_token
    from middleware.redis_rate_limit import tracker_instance

logger = logging.getLogger("nibdefender.targets")

router = APIRouter(prefix="/api/v1", tags=["Attacker Simulation Targets"])


class LoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "admin"})
    password: str = Field(..., json_schema_extra={"example": "secret123"})


class BulkItem(BaseModel):
    id: str = Field(..., json_schema_extra={"example": "item_1"})
    value: str = Field(..., json_schema_extra={"example": "sample_data"})


class BulkDataRequest(BaseModel):
    batch_name: str = Field("default_batch", json_schema_extra={"example": "test_batch"})
    items: List[Dict[str, Any]] = Field([], json_schema_extra={"example": [{"id": "1", "val": "abc"}]})


SQLI_PATTERNS = [
    "' OR '1'='1",
    "' or '1'='1",
    "UNION SELECT",
    "union select",
    "DROP TABLE",
    "drop table",
    "--",
    "';",
    "1=1"
]

XSS_PATTERNS = [
    "<script>",
    "</script>",
    "javascript:",
    "onerror=",
    "onload="
]


@router.post("/auth/login")
async def login_target(request: Request, credentials: LoginRequest = Body(...)):
    """
    Simulated vulnerable login endpoint targeted by brute-force attacks and credential stuffing.
    """
    client_ip = get_client_ip(request)
    username = credentials.username
    password = credentials.password

    # Check for SQL Injection syntax
    has_sqli = any(p in username for p in SQLI_PATTERNS) or any(p in password for p in SQLI_PATTERNS)
    if has_sqli:
        tracker_instance.add_alert(
            severity="HIGH",
            message=f"SQL Injection attack detected in login payload from IP {client_ip}. Username: '{username}'"
        )
        redis_client = getattr(request.app.state, "redis", None) or tracker_instance.redis
        if redis_client:
            try:
                event = json.dumps({
                    "event": "SQL_INJECTION_ATTACK",
                    "ip": client_ip,
                    "payload": f"username={username}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                if inspect.iscoroutinefunction(getattr(redis_client, "lpush", None)):
                    await redis_client.lpush("stream:threats", event)
                elif hasattr(redis_client, "lpush"):
                    redis_client.lpush("stream:threats", event)
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malicious syntax detected by Nibdefender WAF engine."
        )

    # Check valid test credentials
    if username == "admin" and password == "secret123":
        token = create_access_token({"sub": username, "role": "admin"})
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer"
        }

    # Record brute-force failure attempt
    tracker_instance.add_alert(
        severity="LOW",
        message=f"Failed login attempt for user '{username}' from IP {client_ip}."
    )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials."
    )


@router.get("/search")
async def search_target(request: Request, q: str = Query(..., examples=["laptop"])):
    """
    Simulated search target endpoint vulnerable to SQL Injection & XSS probes.
    """
    client_ip = get_client_ip(request)

    is_sqli = any(p in q for p in SQLI_PATTERNS)
    is_xss = any(p in q for p in XSS_PATTERNS)

    if hasattr(request.state, "telemetry") and isinstance(request.state.telemetry, dict):
        request.state.telemetry["is_potential_sqli"] = is_sqli
        request.state.telemetry["is_potential_xss"] = is_xss

    if is_sqli or is_xss:
        attack_type = "SQL_INJECTION" if is_sqli else "XSS_ATTACK"
        tracker_instance.add_alert(
            severity="HIGH",
            message=f"{attack_type} pattern detected in search parameter 'q' from IP {client_ip}: '{q}'"
        )
        redis_client = getattr(request.app.state, "redis", None) or tracker_instance.redis
        if redis_client:
            try:
                event = json.dumps({
                    "event": f"{attack_type}_ATTACK",
                    "ip": client_ip,
                    "query": q,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                if inspect.iscoroutinefunction(getattr(redis_client, "lpush", None)):
                    await redis_client.lpush("stream:threats", event)
                elif hasattr(redis_client, "lpush"):
                    redis_client.lpush("stream:threats", event)
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malicious {attack_type} syntax detected by WAF engine."
        )

    return {
        "status": "success",
        "query": q,
        "results_count": 3,
        "results": [
            {"id": "prod_1", "name": f"Result 1 for {q}"},
            {"id": "prod_2", "name": f"Result 2 for {q}"},
            {"id": "prod_3", "name": f"Result 3 for {q}"}
        ]
    }


@router.post("/data/bulk")
async def bulk_data_target(request: Request, payload: BulkDataRequest = Body(...)):
    """
    High-frequency bulk data target endpoint used for payload anomaly detection and velocity tests.
    """
    client_ip = get_client_ip(request)
    item_count = len(payload.items)

    return {
        "status": "processed",
        "client_ip": client_ip,
        "batch_name": payload.batch_name,
        "items_processed": item_count,
        "message": f"Successfully processed batch '{payload.batch_name}' containing {item_count} items."
    }
