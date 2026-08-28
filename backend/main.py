import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as aioredis

# Add project root and backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from backend.config import settings
except ImportError:
    from config import settings

try:
    from backend.middleware.rate_limiter import RateLimitMiddleware
    from backend.middleware.redis_rate_limit import tracker_instance
    from backend.routes.dummy_api import router as dummy_router
except ImportError:
    from middleware.rate_limiter import RateLimitMiddleware
    from middleware.redis_rate_limit import tracker_instance
    from routes.dummy_api import router as dummy_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nibdefender.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async lifespan context manager to initialize and gracefully close
    the Redis connection pool on startup and shutdown.
    """
    logger.info("Initializing Redis async connection pool...")
    redis_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2
    )
    app.state.redis = redis_client

    try:
        await redis_client.ping()
        logger.info("Successfully connected to Redis instance.")
    except Exception as e:
        logger.warning(f"Redis unreachable during startup ({e}). Running in resilient mode.")

    yield

    logger.info("Closing Redis connection pool...")
    try:
        await redis_client.aclose()
        logger.info("Redis connection pool gracefully closed.")
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")


app = FastAPI(
    title="Nibdefender API Gateway",
    description="Real-time FastAPI & Redis threat detection and rate limiting engine.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware dynamically using settings
origins = settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Rate Limiting & Dynamic IP Blacklist Middleware globally
app.add_middleware(RateLimitMiddleware)

# Include Routers
app.include_router(dummy_router)


@app.get("/api/threat-metrics")
@app.get("/api/v1/threat-metrics")
async def get_threat_metrics():
    """
    Frontend Interface Contract endpoint returning total requests, blocked IPs count,
    blocked IP list, and recent security alerts.
    """
    return tracker_instance.get_metrics_snapshot()


@app.get("/")
async def root():
    return {
        "system": "Nibdefender API Gateway",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint verifying application status and Redis ping connection.
    Returns: {"status": "healthy", "redis": "connected" | "disconnected"}
    """
    redis_status = "disconnected"
    redis_client = getattr(request.app.state, "redis", None)

    if redis_client:
        try:
            is_alive = await redis_client.ping()
            if is_alive:
                redis_status = "connected"
        except Exception as e:
            logger.warning(f"Redis ping failed during health check: {e}")
            redis_status = "disconnected"

    return {
        "status": "healthy",
        "redis": redis_status
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
