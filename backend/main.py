from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import health, markers, analyze, analyze_v2, metrics
from .api import dashboard
from .core.logging import configure_logging, get_logger
from .core.container import get_container
from .infrastructure.metrics import metrics as prom_metrics
from .config import settings
import time

# Configure structured logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Initialize dependency injection container
container = get_container()
container.initialize()

app = FastAPI(
    title="MarkerEngine Core API",
    description="Zentrales Nervensystem der MarkerEngine zur Übersetzung von Sprache in strukturierte Marker.",
    version="1.0.0"
)

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