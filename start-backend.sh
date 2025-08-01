#!/bin/bash
# Production startup script for MarkerEngine Backend

set -e

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Set environment variables for production
export PYTHONUNBUFFERED=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Get port from environment or default to 8000
PORT=${PORT:-8000}

echo "Starting MarkerEngine Backend on port $PORT"
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# Start the application using module execution
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"