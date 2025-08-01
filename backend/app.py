#!/usr/bin/env python3
"""
Deployment entry point for MarkerEngine Core API.
This file handles import path issues for containerized deployments.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set PYTHONPATH for consistent imports
os.environ['PYTHONPATH'] = str(backend_dir)

if __name__ == "__main__":
    import uvicorn
    from main import app
    from config import settings
    
    # Run the application
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )