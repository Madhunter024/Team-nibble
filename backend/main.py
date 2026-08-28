import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Add project root and backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nibdefender.main")

try:
    from backend.routes.dummy_api import router as dummy_router
    from backend.middleware.redis_rate_limit import RateLimitMiddleware, tracker_instance
except ImportError:
    from routes.dummy_api import router as dummy_router
    from middleware.redis_rate_limit import RateLimitMiddleware, tracker_instance


app = FastAPI(
    title="AI-Powered API Threat Defender",
    description="Real-time FastAPI & Redis threat detection and rate limiting engine.",
    version="1.0.0"
)

# CORS setup for Frontend communication
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Threat Defense & Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, tracker=tracker_instance)

# Include API Routers
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
        "system": "AI-Powered API Threat Defender Engine",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "redis": "connected" if tracker_instance.redis else "in-memory-fallback"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
