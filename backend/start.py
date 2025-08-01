#!/usr/bin/env python3
"""
Startup script for MarkerEngine Backend with proper path configuration.
This script ensures proper import path setup for the backend package.
"""
import sys
import os
from pathlib import Path

# Get the backend directory (where this script is located)
backend_dir = Path(__file__).parent.absolute()

# Add the parent directory to sys.path so that 'backend' becomes a proper package
parent_dir = backend_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Add the backend directory to sys.path for direct imports
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set environment for package discovery
os.environ['PYTHONPATH'] = str(backend_dir)

# Now import and run the application
if __name__ == "__main__":
    # Try to import with package structure first
    try:
        from backend.main import app
        import uvicorn
        
        # Get configuration
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8000"))
        
        print(f"Starting MarkerEngine Backend on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
        
    except ImportError as e:
        print(f"Package import failed: {e}")
        print("Trying direct import...")
        
        # Fallback to direct import
        try:
            import main
            import uvicorn
            
            host = os.getenv("API_HOST", "0.0.0.0")
            port = int(os.getenv("API_PORT", "8000"))
            
            print(f"Starting MarkerEngine Backend on {host}:{port}")
            uvicorn.run(main.app, host=host, port=port)
            
        except ImportError as e2:
            print(f"Direct import also failed: {e2}")
            print("Unable to start the application.")
            sys.exit(1)