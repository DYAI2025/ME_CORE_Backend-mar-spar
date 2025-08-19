# Multi-stage Dockerfile for MarkerEngine with optional Spark NLP support

# Base stage with core dependencies only (Production default)
FROM python:3.10-slim as base

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements-base.txt ./
RUN pip install --no-cache-dir -r requirements-base.txt

# Copy application code
COPY . ./

# Create resources directory for detector path validation
RUN mkdir -p /app/resources

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONPATH=/app/backend

# Default: Spark NLP disabled for lightweight deployment
ENV SPARK_NLP_ENABLED=false

# Expose port
EXPOSE 8000

# Health check - use curl instead of httpx to avoid import issues
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the minimal application for stable deployment
CMD ["python", "minimal_app.py"]


# Test stage for running tests
FROM base as test

# Install test dependencies
COPY requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt

# Override command to run tests
CMD ["pytest", "tests/", "-v", "--cov=.", "--cov-report=xml"]


# Spark stage with full NLP support (optional - not used by default)
FROM python:3.10-slim as spark

WORKDIR /app/backend

# Install system dependencies including Java for Spark
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    openjdk-11-jre-headless \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy Spark requirements
COPY requirements-spark.txt ./
RUN pip install --no-cache-dir -r requirements-spark.txt

# Copy application code
COPY . ./

# Create resources directory
RUN mkdir -p /app/resources

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONPATH=/app/backend
ENV SPARK_NLP_ENABLED=true

# Spark configuration
ENV SPARK_HOME=/usr/local/lib/python3.10/dist-packages/pyspark
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the minimal application
CMD ["python", "minimal_app.py"]

# Default to base stage for production (no Java dependencies)
FROM base as production