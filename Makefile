# TransRapport Desktop MVP Makefile
# Provides convenient commands for running the application

.PHONY: help run dev test clean install deps audio-capture list-devices

# Default target
help:
	@echo "TransRapport Desktop MVP"
	@echo "======================="
	@echo ""
	@echo "Available commands:"
	@echo "  make run           - Start the server on http://127.0.0.1:8710/"
	@echo "  make dev           - Start in development mode with auto-reload"
	@echo "  make audio-capture - Start audio capture tool"
	@echo "  make list-devices  - List available audio devices"
	@echo "  make test          - Run tests"
	@echo "  make install       - Install dependencies"
	@echo "  make deps          - Install Python dependencies"
	@echo "  make clean         - Clean up generated files"
	@echo ""

# Main run command - starts server on port 8710
run:
	@echo "Starting TransRapport Desktop MVP on http://127.0.0.1:8710/"
	@echo "Loading configuration from config/app.yaml"
	@cd backend && python -c "import sys; sys.path.insert(0, '.'); from main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8710, log_level='info')" || python -c "import sys; sys.path.insert(0, 'backend'); from minimal_app import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8710, log_level='info')"

# Development mode with auto-reload
dev:
	@echo "Starting TransRapport Desktop MVP in development mode"
	@cd backend && python -c "import sys; sys.path.insert(0, '.'); import uvicorn; from main import app; uvicorn.run(app, host='127.0.0.1', port=8710, reload=True, log_level='debug')" || python -c "import sys; sys.path.insert(0, 'backend'); import uvicorn; from minimal_app import app; uvicorn.run(app, host='127.0.0.1', port=8710, reload=True, log_level='debug')"

# Audio capture tool
audio-capture:
	@echo "Starting audio capture tool..."
	@python tools/mic_ws_sender.py

# List audio devices
list-devices:
	@echo "Available audio devices:"
	@python tools/mic_ws_sender.py --list-devices

# Install all dependencies
install: deps
	@echo "Installing Node.js dependencies..."
	@npm install
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

# Install Python dependencies
deps:
	@echo "Installing Python dependencies..."
	@pip install --user fastapi uvicorn pydantic python-dotenv pyyaml httpx aiofiles websockets
	@echo "Installing optional audio dependencies..."
	@pip install --user sounddevice || echo "sounddevice installation failed - will try pyaudio as fallback"
	@pip install --user pyaudio || echo "pyaudio installation failed - will use available audio library"
	@pip install --user numpy || echo "numpy installation failed"

# Run tests
test:
	@echo "Running backend tests..."
	@cd backend && python -m pytest tests/ || echo "Backend tests not available"
	@echo "Running frontend tests..."
	@cd frontend && npm test || echo "Frontend tests not available"

# Clean up
clean:
	@echo "Cleaning up generated files..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf logs/*.log 2>/dev/null || true
	@rm -rf sessions/* 2>/dev/null || true
	@echo "Cleanup complete"

# Quick start command
start: run

# Alternative run commands for different modes
run-minimal:
	@echo "Starting in minimal mode..."
	@cd backend && python minimal_app.py

run-full:
	@echo "Starting with full configuration..."
	@cd backend && python main.py

# Development utilities
setup-dirs:
	@echo "Creating necessary directories..."
	@mkdir -p config bundles logs sessions models/whisper recordings
	@echo "Directories created"

# Check system requirements
check-system:
	@echo "Checking system requirements..."
	@python --version
	@python -c "import fastapi; print('FastAPI:', fastapi.__version__)" 2>/dev/null || echo "FastAPI: Not installed"
	@python -c "import uvicorn; print('Uvicorn:', uvicorn.__version__)" 2>/dev/null || echo "Uvicorn: Not installed"
	@python -c "import sounddevice; print('sounddevice: Available')" 2>/dev/null || echo "sounddevice: Not available"
	@python -c "import pyaudio; print('PyAudio: Available')" 2>/dev/null || echo "PyAudio: Not available"
	@node --version 2>/dev/null || echo "Node.js: Not installed"

# Quick setup for new installations
quick-setup: setup-dirs deps
	@echo "Quick setup complete!"
	@echo "Run 'make run' to start the server"

# Documentation
docs:
	@echo "TransRapport Desktop MVP Documentation"
	@echo "====================================="
	@echo ""
	@echo "Configuration:"
	@echo "  config/app.yaml - Main application configuration"
	@echo "  bundles/SerapiCore_1.0.yaml - Marker bundle configuration"
	@echo ""
	@echo "Audio Capture:"
	@echo "  tools/mic_ws_sender.py - Audio capture and WebSocket streaming"
	@echo ""
	@echo "WebSocket Endpoints:"
	@echo "  /ws/events - Real-time marker events"
	@echo "  /ws/audio - Audio streaming"
	@echo "  /ws - General dashboard WebSocket"
	@echo ""
	@echo "API Endpoints:"
	@echo "  http://127.0.0.1:8710/ - Main UI"
	@echo "  http://127.0.0.1:8710/docs - API documentation"
	@echo "  http://127.0.0.1:8710/health - Health check"