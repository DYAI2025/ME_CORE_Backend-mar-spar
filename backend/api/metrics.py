"""
Metrics endpoints for MarkerEngine.
Provides Prometheus metrics and health checks.
"""
from fastapi import APIRouter, Response
from app.infrastructure.metrics import metrics
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/", response_class=Response)
async def get_metrics():
    """
    Get Prometheus metrics.
    
    Returns metrics in Prometheus text format.
    """
    try:
        metrics_data = metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type=metrics.get_content_type()
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            status_code=500,
            media_type="text/plain"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status information
    """
    import psutil
    import asyncio
    from datetime import datetime
    from app.services.orchestration_service_di import create_orchestration_service
    
    try:
        # Get service status
        orchestration = create_orchestration_service()
        service_status = orchestration.get_service_status()
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Test database connection
        db_healthy = True
        try:
            from app.repositories.marker_repository import marker_repository
            await asyncio.wait_for(
                marker_repository.db.list_collection_names(), 
                timeout=2.0
            )
        except Exception as e:
            db_healthy = False
            logger.warning(f"Database health check failed: {e}")
        
        health_status = {
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "message": "Connected" if db_healthy else "Connection failed"
                },
                "services": service_status,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / (1024 * 1024)
                }
            }
        }
        
        # Update memory usage metrics
        metrics.set_memory_usage('system', memory.used)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if the application is ready to serve requests.
    
    Returns:
        dict: Readiness status
    """
    from app.services.orchestration_service_di import create_orchestration_service
    
    try:
        # Check if all services are initialized
        orchestration = create_orchestration_service()
        service_status = orchestration.get_service_status()
        
        # Check marker service
        marker_ready = service_status.get('marker_service') == 'active'
        
        # Check NLP service (optional)
        nlp_info = service_status.get('nlp_service', {})
        nlp_ready = nlp_info.get('available', False) or not nlp_info.get('spark_nlp_enabled', False)
        
        # Overall readiness
        is_ready = marker_ready
        
        return {
            "ready": is_ready,
            "checks": {
                "marker_service": marker_ready,
                "nlp_service": nlp_ready,
                "cache_service": service_status.get('cache_service', {}).get('available', False)
            }
        }
        
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return {
            "ready": False,
            "error": str(e)
        }


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Simple check to verify the application is running.
    
    Returns:
        dict: Liveness status
    """
    return {"status": "alive"}