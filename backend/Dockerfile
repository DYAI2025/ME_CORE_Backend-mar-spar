# Multi-stage Dockerfile for MarkerEngine with optional Spark NLP support

# Base stage with core dependencies only
FROM python:3.10-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements-base.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements-base.txt

# Copy application code - structure it so backend is a module
COPY . ./backend/

# Create resources directory
RUN mkdir -p resources

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV PYTHONPATH=/app

# Default: Spark NLP disabled
ENV SPARK_NLP_ENABLED=false

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz')"

# Run the application using module execution from parent directory
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Spark stage with full NLP support
FROM python:3.10-slim as spark

WORKDIR /app

# Install system dependencies including Java for Spark
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    openjdk-11-jre-headless \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy Spark requirements
COPY requirements-spark.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements-spark.txt

# Download Spark NLP models during build (optional, for faster startup)
# RUN python -c "import sparknlp; sparknlp.start(); sparknlp.pretrained.PretrainedPipeline.from_disk('de')"

# Copy application code - structure it so backend is a module
COPY . ./backend/

# Create resources directory
RUN mkdir -p resources

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV SPARK_NLP_ENABLED=true
ENV PYTHONPATH=/app

# Spark configuration
ENV SPARK_HOME=/usr/local/lib/python3.10/dist-packages/pyspark
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz')"

# Run the application using module execution from parent directory
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]