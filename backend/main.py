from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api import health, markers, analyze, analyze_v2, metrics, dashboard, api_schemas_routes
from .core.logging import configure_logging, get_logger
from .core.container import get_container
from .core.exceptions import ConfigurationError, handle_markerengine_error, MarkerEngineError
from .infrastructure.metrics import metrics as prom_metrics
import time
import sys

# Configure structured logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Try to load configuration and initialize container
try:
    from .config import settings
    
    # Initialize dependency injection container
    container = get_container()
    container.initialize()
    
    logger.info("Configuration loaded successfully")
    config_loaded = True
    
except ConfigurationError as e:
    logger.error(f"Configuration error: {e.message}")
    logger.error("Please check your environment configuration and try again.")
    logger.info("Falling back to minimal application mode")
    
    # Import and run minimal app instead of exiting
    try:
        from minimal_app import app
        logger.info("Using minimal application fallback")
    except ImportError:
        logger.error("Minimal app fallback not available")
        # Create a basic error app as last resort
        app = FastAPI(
            title="MarkerEngine Core API - Configuration Error",
            description="Service is not properly configured.",
            version="1.0.0"
        )
        
        @app.get("/")
        @app.get("/api/health/live")
        @app.get("/api/health/ready")
        async def configuration_error():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "CONFIGURATION_ERROR",
                    "message": e.message,
                    "details": e.details
                }
            )
        
        # Don't exit - let the app run with error endpoint
        config_loaded = False

except Exception as e:
    logger.error(f"Unexpected error during initialization: {e}")
    logger.info("Attempting to fall back to minimal application")
    
    try:
        from minimal_app import app
        logger.info("Using minimal application fallback")
        config_loaded = False
    except ImportError:
        logger.error("No fallback available, exiting")
        sys.exit(1)

# If configuration is valid, create the full app
if 'config_loaded' not in locals() or config_loaded:
    app = FastAPI(
        title="MarkerEngine Core API",
        description="Zentrales Nervensystem der MarkerEngine zur Übersetzung von Sprache in strukturierte Marker.",
        version="1.0.0"
    )

# Only configure full app if configuration was loaded successfully
if 'config_loaded' not in locals() or config_loaded:
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics."""
    start_time = time.time()
    
    # Track active requests
    prom_metrics.increment_active_requests()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Track request metrics
        prom_metrics.track_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
        
        # Add request ID header
        response.headers["X-Request-Duration"] = str(duration)
        
        return response
    
    finally:
        prom_metrics.decrement_active_requests()

# Add exception handler for MarkerEngine errors
@app.exception_handler(MarkerEngineError)
async def markerengine_exception_handler(request: Request, exc: MarkerEngineError):
    return JSONResponse(
        status_code=handle_markerengine_error(exc).status_code,
        content=exc.to_dict()
    )

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(markers.router, prefix="/markers", tags=["Markers"])
app.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])
app.include_router(analyze_v2.router, prefix="/analyze/v2", tags=["Analysis v2"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(api_schemas_routes.router, tags=["Schemas"])

# Include metrics router if enabled
if settings.ENABLE_METRICS:
    app.include_router(metrics.router, tags=["Metrics"])


@app.get("/", tags=["Root"])
async def read_root():
    # Try to get TransRapport config
    try:
        from .app_config import app_config
        title = app_config.get('server.title', 'TransRapport Desktop MVP')
        environment = app_config.get('server.environment', 'desktop')
        return {
            "message": f"Welcome to {title}",
            "environment": environment,
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "dashboard": "/api/dashboard",
                "markers": "/markers",
                "analyze": "/analyze",
                "websockets": {
                    "events": "/api/dashboard/ws/events",
                    "audio": "/api/dashboard/ws/audio",
                    "dashboard": "/api/dashboard/ws"
                }
            }
        }
    except:
        return {"message": "Welcome to the MarkerEngine Core API"}


# Add startup message
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    try:
        from .app_config import app_config
        server_config = app_config.get_server_config()
        host = server_config.get("host", "127.0.0.1")
        port = server_config.get("port", 8710)
        title = server_config.get("title", "TransRapport Desktop MVP")
        
        logger.info(f"Starting {title}")
        logger.info(f"Server: {host}:{port}")
        logger.info(f"Environment: {server_config.get('environment', 'desktop')}")
        logger.info(f"UI available at: http://{host}:{port}/")
        logger.info(f"API docs: http://{host}:{port}/docs")
        logger.info(f"WebSocket events: ws://{host}:{port}/api/dashboard/ws/events")
        logger.info(f"WebSocket audio: ws://{host}:{port}/api/dashboard/ws/audio")
        
        # Log marker configuration
        marker_config = app_config.get_marker_config()
        logger.info(f"Marker directories: {marker_config.get('directories', [])}")
        logger.info(f"Real-time processing: {marker_config.get('realtime', {}).get('enabled', False)}")
        
        # Log offline mode
        if app_config.is_offline_mode():
            logger.info("Running in OFFLINE mode - no external API calls")
            
    except Exception as e:
        logger.warning(f"Could not load TransRapport config: {e}")
        logger.info(f"Starting MarkerEngine API on {settings.API_HOST}:{settings.API_PORT}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        
    if 'settings' in locals():
        logger.info(f"Database URL: {settings.DATABASE_URL[:20] if hasattr(settings, 'DATABASE_URL') else 'N/A'}...")
        logger.info(f"Metrics enabled: {getattr(settings, 'ENABLE_METRICS', False)}")
        logger.info(f"Spark NLP enabled: {getattr(settings, 'SPARK_NLP_ENABLED', False)}")


if __name__ == "__main__":
    import uvicorn
    
    # Try to load TransRapport Desktop configuration
    try:
        from .app_config import app_config
        server_config = app_config.get_server_config()
        host = server_config.get("host", "127.0.0.1")
        port = server_config.get("port", 8710)
        title = server_config.get("title", "TransRapport Desktop MVP")
        
        print(f"Starting {title}")
        print(f"Server configuration: {host}:{port}")
        print(f"Environment: {server_config.get('environment', 'desktop')}")
        print(f"UI available at: http://{host}:{port}/")
        print("Use 'make run' to start with configuration")
        
    except Exception as e:
        print(f"Could not load app config: {e}")
        host = getattr(settings, 'API_HOST', '127.0.0.1') if 'settings' in locals() else "127.0.0.1"
        port = getattr(settings, 'API_PORT', 8710) if 'settings' in locals() else 8710
        title = "TransRapport Desktop MVP"
    
    print(f"Config loaded: {config_loaded if 'config_loaded' in locals() else False}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False
    )