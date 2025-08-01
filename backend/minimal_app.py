#!/usr/bin/env python3
"""
Minimal deployment entry point for MarkerEngine Core API.
This creates a simplified app that can start without all dependencies.
"""
import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import configuration safely
try:
    from config import settings
    config_loaded = True
except Exception as e:
    print(f"Warning: Could not load full config: {e}")
    config_loaded = False
    
    # Create minimal settings
    class MinimalSettings:
        API_HOST = os.getenv("API_HOST", "0.0.0.0")
        API_PORT = int(os.getenv("API_PORT", "8000"))
        ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
        
    settings = MinimalSettings()

# Create FastAPI app
app = FastAPI(
    title="MarkerEngine Core API",
    description="Minimal deployment version",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include simple health endpoints
from simple_health import router as health_router
app.include_router(health_router)

@app.get("/")
async def root():
    return {
        "message": "MarkerEngine Core API",
        "status": "running",
        "config_loaded": config_loaded
    }

if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting MarkerEngine API on {settings.API_HOST}:{settings.API_PORT}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Config loaded: {config_loaded}")
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )