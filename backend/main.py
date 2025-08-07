from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api import health, markers, analyze, analyze_v2, metrics, dashboard
from core.logging import configure_logging, get_logger
from core.container import get_container
from core.exceptions import ConfigurationError, handle_markerengine_error, MarkerEngineError
from infrastructure.metrics import metrics as prom_metrics
import time
import sys

# Configure structured logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Try to load configuration and initialize container
try:
    from config import settings
    
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

# Include metrics router if enabled
if settings.ENABLE_METRICS:
    app.include_router(metrics.router, tags=["Metrics"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the MarkerEngine Core API"}


# Add startup message
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"Starting MarkerEngine API on {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL[:20]}...")  # Log partial URL for security
    logger.info(f"Metrics enabled: {settings.ENABLE_METRICS}")
    logger.info(f"Spark NLP enabled: {settings.SPARK_NLP_ENABLED}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development"
    )