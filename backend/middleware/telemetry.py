import time
import math
import json
import inspect
import logging
from typing import Dict, Any, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

try:
    from backend.middleware.rate_limiter import get_client_ip
except ImportError:
    from middleware.rate_limiter import get_client_ip

try:
    from backend.middleware.redis_rate_limit import tracker_instance
except ImportError:
    from middleware.redis_rate_limit import tracker_instance

logger = logging.getLogger("nibdefender.telemetry")


def calculate_shannon_entropy(text: str) -> float:
    """
    Calculate Shannon entropy of a string to identify automated bot scrapers & anomalous payloads.
    """
    if not text:
        return 0.0
    length = len(text)
    char_counts: Dict[str, int] = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1

    entropy = 0.0
    for count in char_counts.values():
        p = count / length
        entropy -= p * math.log2(p)

    return round(entropy, 4)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware extracting security telemetry features from incoming HTTP requests
    and streaming events to Redis for ML anomaly detection.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        current_time_sec = time.time()
        timestamp_ms = int(current_time_sec * 1000)

        client_ip = get_client_ip(request)
        endpoint = request.url.path
        method = request.method

        # Payload size from Content-Length header
        try:
            payload_size = int(request.headers.get("content-length", 0))
        except (ValueError, TypeError):
            payload_size = 0

        # Calculate Shannon entropy over User-Agent + header representation
        user_agent = request.headers.get("user-agent", "")
        headers_str = f"{user_agent}|{'|'.join(request.headers.keys())}"
        header_entropy = calculate_shannon_entropy(headers_str)

        # Request velocity: count of requests from this IP in the last 10 seconds
        redis_client = getattr(request.app.state, "redis", None) or tracker_instance.redis
        request_velocity = 1

        if redis_client:
            try:
                zset_key = f"rate_limit:{client_ip}"
                if inspect.iscoroutinefunction(getattr(redis_client, "zcount", None)):
                    vel = await redis_client.zcount(zset_key, current_time_sec - 10, "+inf")
                    request_velocity = max(1, vel)
                elif hasattr(redis_client, "zcount"):
                    vel = redis_client.zcount(zset_key, current_time_sec - 10, "+inf")
                    request_velocity = max(1, vel)
            except Exception as e:
                logger.debug(f"Error reading velocity from Redis: {e}")

        telemetry_data = {
            "client_ip": client_ip,
            "endpoint": endpoint,
            "method": method,
            "timestamp": timestamp_ms,
            "payload_size": payload_size,
            "header_entropy": header_entropy,
            "request_velocity": request_velocity
        }

        # Attach telemetry to request.state for downstream route handlers / ML inspection
        request.state.telemetry = telemetry_data

        # Async non-blocking push of telemetry to stream:telemetry
        if redis_client:
            try:
                telemetry_json = json.dumps(telemetry_data)
                if inspect.iscoroutinefunction(getattr(redis_client, "lpush", None)):
                    await redis_client.lpush("stream:telemetry", telemetry_json)
                    await redis_client.ltrim("stream:telemetry", 0, 999)
                elif hasattr(redis_client, "lpush"):
                    redis_client.lpush("stream:telemetry", telemetry_json)
                    redis_client.ltrim("stream:telemetry", 0, 999)
            except Exception as e:
                logger.debug(f"Failed streaming telemetry to Redis: {e}")

        response = await call_next(request)
        return response
