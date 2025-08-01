"""
Simple health check API for deployment.
This replaces the complex health system with a basic one for Fly.io deployment.
"""
from fastapi import APIRouter
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class SimpleHealthStatus(BaseModel):
    status: str
    timestamp: str
    service: str = "markerengine-core"

@router.get("/health")
@router.get("/api/health") 
@router.get("/api/health/live")
@router.get("/api/health/ready")
async def health_check():
    """Simple health check endpoint for deployment"""
    return SimpleHealthStatus(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@router.get("/healthz")
async def kubernetes_health():
    """Kubernetes-style health check"""
    return {"status": "ok"}