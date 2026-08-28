import time
import logging
from typing import Optional, Dict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger("nibdefender.rate_limit")

class RedisRateLimiter:
    """
    IP Rate limiting and automatic IP blocking using Redis (with in-memory fallback).
    """

    def __init__(self, redis_client=None, rate_limit: int = 100, window_seconds: int = 60):
        self.redis = redis_client
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        # In-memory storage fallback if Redis is unavailable
        self.memory_store: Dict[str, list] = {}
        self.blocked_ips: set = set()

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP address is in the blocked list."""
        if self.redis:
            try:
                return bool(self.redis.sismember("blocked_ips", ip))
            except Exception as e:
                logger.warning(f"Redis error checking blocked IP: {e}")
        return ip in self.blocked_ips

    def block_ip(self, ip: str, duration: int = 3600) -> None:
        """Block an IP address for a specific duration."""
        if self.redis:
            try:
                self.redis.sadd("blocked_ips", ip)
                self.redis.expire(f"blocked:{ip}", duration)
            except Exception as e:
                logger.warning(f"Redis error blocking IP: {e}")
        self.blocked_ips.add(ip)
        logger.info(f"IP address {ip} has been blocked.")

    def check_rate_limit(self, ip: str) -> tuple[bool, int]:
        """
        Check if request limit is exceeded for the IP.
        Returns tuple: (is_allowed: bool, current_request_count: int)
        """
        current_time = time.time()
        
        if self.redis:
            try:
                key = f"rate_limit:{ip}"
                pipeline = self.redis.pipeline()
                pipeline.zremrangebyscore(key, 0, current_time - self.window_seconds)
                pipeline.zadd(key, {str(current_time): current_time})
                pipeline.zcard(key)
                pipeline.expire(key, self.window_seconds)
                results = pipeline.execute()
                request_count = results[2]
                return request_count <= self.rate_limit, request_count
            except Exception as e:
                logger.warning(f"Redis error during rate limit check: {e}")

        # In-memory fallback algorithm
        timestamps = self.memory_store.get(ip, [])
        valid_timestamps = [ts for ts in timestamps if ts > current_time - self.window_seconds]
        valid_timestamps.append(current_time)
        self.memory_store[ip] = valid_timestamps
        
        count = len(valid_timestamps)
        return count <= self.rate_limit, count


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: Optional[RedisRateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RedisRateLimiter()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        client_ip = request.client.host if request.client else "unknown"

        # Check if IP is explicitly blocked
        if self.rate_limiter.is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Access Forbidden", "detail": f"IP address {client_ip} has been blocked by Nibdefender security."}
            )

        # Check rate limit
        allowed, count = self.rate_limiter.check_rate_limit(client_ip)
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} ({count} requests)")
            # Auto block IP if requests exceed 2x threshold
            if count > self.rate_limiter.rate_limit * 2:
                self.rate_limiter.block_ip(client_ip)

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded. Please slow down.",
                    "current_count": count
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rate_limiter.rate_limit - count))
        return response
