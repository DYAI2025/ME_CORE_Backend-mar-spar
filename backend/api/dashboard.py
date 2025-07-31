"""
Dashboard API endpoints for monitoring and management
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
from pydantic import BaseModel

from ..core.container import get_container
from ..core.interfaces import IMarkerService, ICacheService
from ..database import get_database
from ..config import get_settings
from ..detect.DETECT_registry import load_registry, save_registry, validate_registry_format

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
settings = get_settings()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Request/Response models
class RegistryUpdateRequest(BaseModel):
    registry: Dict[str, Any]

class MarkerStatsResponse(BaseModel):
    total: int
    active: int
    by_type: Dict[str, int]
    recently_updated: int

class ActivityLog(BaseModel):
    id: str
    timestamp: datetime
    type: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

# Dashboard overview endpoint
@router.get("/overview")
async def get_dashboard_overview(
    db = Depends(get_database),
    container = Depends(get_container)
):
    """Get comprehensive dashboard overview data"""
    try:
        # Get marker statistics
        markers_collection = db.markers
        total_markers = await markers_collection.count_documents({})
        active_markers = await markers_collection.count_documents({"active": True})
        
        # Count by type
        pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        type_counts = {}
        async for doc in markers_collection.aggregate(pipeline):
            type_counts[doc["_id"]] = doc["count"]
        
        # Recent updates (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_updates = await markers_collection.count_documents({
            "updated_at": {"$gte": yesterday}
        })
        
        return {
            "markers": {
                "total": total_markers,
                "active": active_markers,
                "by_type": type_counts,
                "recently_updated": recent_updates
            },
            "system": {
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "uptime": get_uptime()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Marker management endpoints
@router.get("/markers/stats")
async def get_marker_stats(
    db = Depends(get_database)
) -> MarkerStatsResponse:
    """Get marker statistics"""
    markers_collection = db.markers
    
    total = await markers_collection.count_documents({})
    active = await markers_collection.count_documents({"active": True})
    
    # Count by type
    pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    by_type = {}
    async for doc in markers_collection.aggregate(pipeline):
        by_type[doc["_id"]] = doc["count"]
    
    # Recent updates
    yesterday = datetime.utcnow() - timedelta(days=1)
    recently_updated = await markers_collection.count_documents({
        "updated_at": {"$gte": yesterday}
    })
    
    return MarkerStatsResponse(
        total=total,
        active=active,
        by_type=by_type,
        recently_updated=recently_updated
    )

# DETECT Registry management
@router.get("/detect/registry")
async def get_detect_registry():
    """Get current DETECT registry"""
    try:
        registry = load_registry()
        return registry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load registry: {str(e)}")

@router.post("/detect/registry/validate")
async def validate_detect_registry(request: RegistryUpdateRequest):
    """Validate DETECT registry format"""
    try:
        errors = validate_registry_format(request.registry)
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }

@router.put("/detect/registry")
async def update_detect_registry(
    request: RegistryUpdateRequest,
    db = Depends(get_database),
    container = Depends(get_container)
):
    """Update DETECT registry"""
    try:
        # Validate before saving
        errors = validate_registry_format(request.registry)
        if errors:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        # Save registry
        save_registry(request.registry)
        
        # Clear cache to force reload
        cache_service = container.get(ICacheService)
        await cache_service.clear()
        
        # Log activity
        await log_activity(db, "registry_update", "DETECT registry updated")
        
        # Broadcast update via WebSocket
        await manager.broadcast(json.dumps({
            "type": "registry_updated",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return {"success": True, "message": "Registry updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Schema management
@router.get("/schemas")
async def get_schemas(db = Depends(get_database)):
    """Get all active schemas"""
    schemas_collection = db.schemas
    schemas = []
    
    async for schema in schemas_collection.find({"active": True}):
        schemas.append({
            "id": schema["_id"],
            "name": schema["name"],
            "version": schema.get("version", "1.0.0"),
            "fields": len(schema.get("fields", [])),
            "updated_at": schema.get("updated_at")
        })
    
    return schemas

# Activity logging
@router.get("/activities")
async def get_recent_activities(
    limit: int = 10,
    db = Depends(get_database)
) -> List[ActivityLog]:
    """Get recent system activities"""
    activities_collection = db.activities
    
    activities = []
    cursor = activities_collection.find().sort("timestamp", -1).limit(limit)
    
    async for activity in cursor:
        activities.append(ActivityLog(
            id=str(activity["_id"]),
            timestamp=activity["timestamp"],
            type=activity["type"],
            message=activity["message"],
            metadata=activity.get("metadata")
        ))
    
    return activities

# System metrics
@router.get("/metrics")
async def get_system_metrics(container = Depends(get_container)):
    """Get system performance metrics"""
    try:
        # Get metrics from monitoring service if available
        metrics = {
            "cpu": get_cpu_usage(),
            "memory": get_memory_usage(),
            "disk": get_disk_usage(),
            "cache_hit_rate": await get_cache_hit_rate(container),
            "api_latency": get_api_latency(),
            "active_connections": len(manager.active_connections)
        }
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle different message types
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Deployment management
@router.post("/deploy/{environment}")
async def trigger_deployment(
    environment: str,
    db = Depends(get_database)
):
    """Trigger deployment to specified environment"""
    if environment not in ["staging", "production"]:
        raise HTTPException(status_code=400, detail="Invalid environment")
    
    try:
        # In real implementation, this would trigger actual deployment
        deployment_id = f"deploy-{datetime.utcnow().timestamp()}"
        
        await log_activity(
            db, 
            "deployment_triggered", 
            f"Deployment to {environment} triggered",
            {"deployment_id": deployment_id, "environment": environment}
        )
        
        return {
            "deployment_id": deployment_id,
            "environment": environment,
            "status": "initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# E2E test management
@router.post("/tests/e2e/trigger")
async def trigger_e2e_tests(db = Depends(get_database)):
    """Trigger end-to-end tests"""
    try:
        test_run_id = f"e2e-{datetime.utcnow().timestamp()}"
        
        await log_activity(
            db,
            "e2e_tests_triggered",
            "End-to-end tests triggered",
            {"test_run_id": test_run_id}
        )
        
        # In real implementation, this would trigger actual tests
        return {
            "test_run_id": test_run_id,
            "status": "running",
            "estimated_duration": "15 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/results")
async def get_test_results(
    limit: int = 10,
    db = Depends(get_database)
):
    """Get recent test results"""
    test_results_collection = db.test_results
    
    results = []
    cursor = test_results_collection.find().sort("timestamp", -1).limit(limit)
    
    async for result in cursor:
        results.append({
            "id": str(result["_id"]),
            "timestamp": result["timestamp"],
            "type": result["type"],
            "status": result["status"],
            "passed": result.get("passed", 0),
            "failed": result.get("failed", 0),
            "duration": result.get("duration", 0)
        })
    
    return results

# Helper functions
async def log_activity(db, activity_type: str, message: str, metadata: Dict = None):
    """Log system activity"""
    activities_collection = db.activities
    await activities_collection.insert_one({
        "timestamp": datetime.utcnow(),
        "type": activity_type,
        "message": message,
        "metadata": metadata or {}
    })

def get_uptime():
    """Get system uptime in seconds"""
    # In real implementation, track actual uptime
    return 3600  # 1 hour for demo

def get_cpu_usage():
    """Get current CPU usage percentage"""
    # In real implementation, use psutil or similar
    import random
    return round(random.uniform(20, 60), 1)

def get_memory_usage():
    """Get current memory usage percentage"""
    # In real implementation, use psutil or similar
    import random
    return round(random.uniform(40, 70), 1)

def get_disk_usage():
    """Get current disk usage percentage"""
    # In real implementation, use psutil or similar
    import random
    return round(random.uniform(30, 50), 1)

async def get_cache_hit_rate(container):
    """Get cache hit rate"""
    try:
        cache_service = container.get(ICacheService)
        # In real implementation, track actual hit rate
        return 0.85  # 85% hit rate for demo
    except:
        return 0.0

def get_api_latency():
    """Get average API latency in ms"""
    # In real implementation, track actual latency
    import random
    return round(random.uniform(50, 150), 1)