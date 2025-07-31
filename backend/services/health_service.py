"""
Health check service for MarkerEngine.
"""
from datetime import datetime
from pydantic import BaseModel
from backend.core.logging import get_logger
from backend.config import settings

logger = get_logger(__name__)


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    database_connected: bool
    timestamp: str
    details: dict = {}


async def check_health() -> HealthStatus:
    """Check application health status."""
    try:
        # Check if we're using mock service
        if settings.DATABASE_URL == "mongodb://localhost:27017/test":
            logger.info("Health check - running in mock mode")
            return HealthStatus(
                status="healthy",
                database_connected=True,  # Mock is always "connected"
                timestamp=datetime.utcnow().isoformat(),
                details={
                    "mode": "mock",
                    "message": "Running without MongoDB - using mock service"
                }
            )
        
        # Try to check real MongoDB
        try:
            from backend.repositories.marker_repository import marker_repository
            # Simple check - this will fail if MongoDB is not available
            await marker_repository.db.list_collection_names()
            
            return HealthStatus(
                status="healthy",
                database_connected=True,
                timestamp=datetime.utcnow().isoformat(),
                details={"mode": "production"}
            )
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            return HealthStatus(
                status="degraded",
                database_connected=False,
                timestamp=datetime.utcnow().isoformat(),
                details={
                    "mode": "fallback",
                    "error": str(e),
                    "message": "MongoDB not available - limited functionality"
                }
            )
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthStatus(
            status="unhealthy",
            database_connected=False,
            timestamp=datetime.utcnow().isoformat(),
            details={"error": str(e)}
        )