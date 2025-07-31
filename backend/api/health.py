from fastapi import APIRouter, Depends, HTTPException
from ..services.health_service import check_health, HealthStatus

router = APIRouter()

@router.get("/healthz", response_model=HealthStatus)
async def health_check():
    health = await check_health()
    if not health.database_connected:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return health