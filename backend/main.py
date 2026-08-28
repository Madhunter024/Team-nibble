import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nibdefender.main")

from backend.routes.dummy_api import router as dummy_router
from backend.middleware.redis_rate_limit import RateLimitMiddleware, RedisRateLimiter

app = FastAPI(
    title="Nibdefender Security Gateway",
    description="Real-time FastAPI & Redis threat detection and rate limiting engine.",
    version="1.0.0"
)

# CORS setup for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Rate Limiter
rate_limiter = RedisRateLimiter(rate_limit=50, window_seconds=60)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Include API Routers
app.include_router(dummy_router)

@app.get("/")
async def root():
    return {
        "system": "Nibdefender Threat Engine",
        "status": "active",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "redis": "connected"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
