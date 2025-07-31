"""
Health Check and Monitoring Endpoints
Provides system status and sub-component health checks
"""
from fastapi import APIRouter, Response
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import psutil
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])


class HealthStatus(BaseModel):
    """Health check response model"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    version: str = "1.0.0"
    checks: Dict[str, Dict[str, Any]]
    metrics: Optional[Dict[str, Any]] = None


class ComponentHealth(BaseModel):
    """Individual component health"""
    name: str
    status: str  # healthy, unhealthy
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


async def check_database_health() -> ComponentHealth:
    """Check MongoDB connectivity and performance"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from ..config import settings
        
        client = AsyncIOMotorClient(settings.DATABASE_URL)
        db = client[settings.MONGO_DB_NAME]
        
        # Ping database
        await db.command('ping')
        
        # Check collections
        collections = await db.list_collection_names()
        
        latency = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ComponentHealth(
            name="mongodb",
            status="healthy",
            latency_ms=latency,
            message="Connected",
            metadata={
                "collections": len(collections),
                "database": settings.MONGO_DB_NAME
            }
        )
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            name="mongodb",
            status="unhealthy",
            message=str(e)
        )


async def check_redis_health() -> ComponentHealth:
    """Check Redis connectivity if enabled"""
    try:
        from ..config import settings
        
        if settings.CACHE_TYPE != "redis":
            return ComponentHealth(
                name="redis",
                status="healthy",
                message="Not configured (using memory cache)"
            )
        
        import aioredis
        start_time = asyncio.get_event_loop().time()
        
        redis = await aioredis.from_url(settings.REDIS_URL)
        await redis.ping()
        info = await redis.info()
        await redis.close()
        
        latency = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ComponentHealth(
            name="redis",
            status="healthy",
            latency_ms=latency,
            message="Connected",
            metadata={
                "version": info.get('redis_version'),
                "used_memory_human": info.get('used_memory_human')
            }
        )
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return ComponentHealth(
            name="redis",
            status="unhealthy",
            message=str(e)
        )


async def check_spark_health() -> ComponentHealth:
    """Check Spark NLP service availability"""
    try:
        from ..config import settings
        
        if not settings.SPARK_NLP_ENABLED:
            return ComponentHealth(
                name="spark-nlp",
                status="healthy",
                message="Disabled (using dummy NLP)"
            )
        
        import httpx
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient() as client:
            # Assuming Spark service has health endpoint
            response = await client.get(
                "http://spark-nlp:8090/health",
                timeout=5.0
            )
            response.raise_for_status()
            
        latency = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return ComponentHealth(
            name="spark-nlp",
            status="healthy",
            latency_ms=latency,
            message="Service available"
        )
        
    except Exception as e:
        logger.error(f"Spark health check failed: {e}")
        return ComponentHealth(
            name="spark-nlp",
            status="unhealthy",
            message=str(e)
        )


async def check_schema_health() -> ComponentHealth:
    """Check schema validation system"""
    try:
        import os
        import json
        
        schema_dir = "/app/backend/schemata"
        if not os.path.exists(schema_dir):
            return ComponentHealth(
                name="schema-validator",
                status="unhealthy",
                message="Schema directory not found"
            )
        
        # Count and validate schemas
        schema_files = [f for f in os.listdir(schema_dir) if f.endswith('.json')]
        valid_schemas = 0
        
        for schema_file in schema_files:
            try:
                with open(os.path.join(schema_dir, schema_file), 'r') as f:
                    json.load(f)
                valid_schemas += 1
            except:
                pass
        
        return ComponentHealth(
            name="schema-validator",
            status="healthy" if valid_schemas > 0 else "degraded",
            message=f"{valid_schemas}/{len(schema_files)} schemas valid",
            metadata={
                "total_schemas": len(schema_files),
                "valid_schemas": valid_schemas
            }
        )
        
    except Exception as e:
        logger.error(f"Schema health check failed: {e}")
        return ComponentHealth(
            name="schema-validator",
            status="unhealthy",
            message=str(e)
        )


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu": {
            "usage_percent": cpu_percent,
            "count": psutil.cpu_count()
        },
        "memory": {
            "total_mb": memory.total / (1024 * 1024),
            "available_mb": memory.available / (1024 * 1024),
            "used_percent": memory.percent
        },
        "disk": {
            "total_gb": disk.total / (1024 * 1024 * 1024),
            "free_gb": disk.free / (1024 * 1024 * 1024),
            "used_percent": disk.percent
        }
    }


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check with sub-component status
    
    Returns:
        HealthStatus with all component checks
    """
    # Run all health checks in parallel
    checks = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_spark_health(),
        check_schema_health(),
        return_exceptions=True
    )
    
    # Process results
    health_checks = {}
    overall_status = "healthy"
    
    for check in checks:
        if isinstance(check, Exception):
            logger.error(f"Health check exception: {check}")
            continue
        
        health_checks[check.name] = {
            "status": check.status,
            "latency_ms": check.latency_ms,
            "message": check.message,
            "metadata": check.metadata
        }
        
        if check.status == "unhealthy":
            overall_status = "unhealthy"
        elif check.status == "degraded" and overall_status == "healthy":
            overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        checks=health_checks,
        metrics=get_system_metrics()
    )


@router.get("/health/live")
async def liveness_check():
    """Simple liveness check for Kubernetes"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verify critical services are available"""
    # Check only critical components
    db_health = await check_database_health()
    
    if db_health.status == "unhealthy":
        return Response(
            content={"status": "not ready", "reason": "database unavailable"},
            status_code=503
        )
    
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint
    
    Returns metrics in Prometheus text format
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from ..metrics import metrics_collector
        
        metrics_data = generate_latest(metrics_collector.registry)
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            status_code=500,
            media_type="text/plain"
        )