#!/bin/bash

# Deployment validation script for MarkerEngine Core API
# This script validates that the Docker setup is production-ready

set -e

echo "🔍 MarkerEngine Deployment Validation"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0

# Function to print status
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        ((ERRORS++))
    fi
}

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        print_status "File exists: $1" 0
    else
        print_status "File missing: $1" 1
    fi
}

echo -e "${BLUE}Checking required files...${NC}"
check_file "Dockerfile"
check_file "requirements-base.txt"
check_file "minimal_app.py"
check_file "simple_health.py"
check_file ".dockerignore"
# Check for fly.toml in parent directory (root)
if [ -f "../fly.toml" ]; then
    print_status "File exists: ../fly.toml" 0
else
    print_status "File missing: ../fly.toml" 1
fi

echo
echo -e "${BLUE}Validating Dockerfile configuration...${NC}"

# Check if Dockerfile.fly exists and is properly configured for fly.io
if [ -f "Dockerfile.fly" ]; then
    print_status "Dockerfile.fly exists" 0
    
    # Check if it uses Python 3.10 slim (as specified in Dockerfile.fly)
    if grep -q "FROM python:3.10-slim" Dockerfile.fly; then
        print_status "Dockerfile.fly uses Python 3.10-slim" 0
    else
        print_status "Dockerfile.fly should use Python 3.10-slim" 1
    fi
else
    print_status "Dockerfile.fly missing for fly.io deployment" 1
fi

# Also check regular Dockerfile for base stage (for other deployments)
if grep -q "FROM python:3.11-slim as base" Dockerfile; then
    print_status "Dockerfile has base stage" 0
else
    print_status "Dockerfile missing base stage" 1
fi

# Check if health check uses curl (not Python)
if grep -q "curl -f.*health" Dockerfile; then
    print_status "Health check uses curl" 0
else
    print_status "Health check not using curl" 1
fi

# Check if SPARK_NLP_ENABLED is false by default
if grep -q "ENV SPARK_NLP_ENABLED=false" Dockerfile; then
    print_status "Spark NLP disabled by default" 0
else
    print_status "Spark NLP not properly disabled" 1
fi

echo
echo -e "${BLUE}Testing Docker build...${NC}"

# Build the production image
if docker build --target base -t markerengine-validation:test . > /dev/null 2>&1; then
    print_status "Docker build successful (base stage)" 0
    
    # Check image size (should be reasonable for production)
    IMAGE_SIZE=$(docker images markerengine-validation:test --format "table {{.Size}}" | tail -n 1)
    echo -e "${YELLOW}ℹ️  Image size: ${IMAGE_SIZE}${NC}"
    
    # Start container for testing
    echo -e "${BLUE}Testing container startup...${NC}"
    CONTAINER_ID=$(docker run -d -p 8002:8000 markerengine-validation:test 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_status "Container started successfully" 0
        
        # Wait for application to start
        sleep 8
        
        # Test health endpoint
        if curl -s -f http://localhost:8002/health > /dev/null 2>&1; then
            print_status "Health endpoint responding" 0
        else
            print_status "Health endpoint not responding" 1
        fi
        
        # Test root endpoint
        if curl -s -f http://localhost:8002/ > /dev/null 2>&1; then
            print_status "Root endpoint responding" 0
        else
            print_status "Root endpoint not responding" 1
        fi
        
        # Check that Java is NOT installed (production requirement)
        if docker exec "$CONTAINER_ID" java -version > /dev/null 2>&1; then
            print_status "Java not found (production requirement)" 1
        else
            print_status "Java not found (production requirement)" 0
        fi
        
        # Check application logs for errors
        LOGS=$(docker logs "$CONTAINER_ID" 2>&1)
        if echo "$LOGS" | grep -q "ERROR\|CRITICAL\|Exception"; then
            print_status "No critical errors in logs" 1
            echo -e "${YELLOW}Warning: Found errors in logs:${NC}"
            echo "$LOGS" | grep "ERROR\|CRITICAL\|Exception" | head -5
        else
            print_status "No critical errors in logs" 0
        fi
        
        # Cleanup
        docker stop "$CONTAINER_ID" > /dev/null 2>&1
        docker rm "$CONTAINER_ID" > /dev/null 2>&1
        
    else
        print_status "Container failed to start" 1
    fi
    
    # Cleanup image
    docker rmi markerengine-validation:test > /dev/null 2>&1
    
else
    print_status "Docker build failed" 1
fi

echo
echo -e "${BLUE}Checking Fly.io configuration...${NC}"

# Check fly.toml dockerfile
if grep -q 'dockerfile = "backend/Dockerfile.fly"' ../fly.toml; then
    print_status "Fly.io uses Dockerfile.fly" 0
else
    print_status "Fly.io dockerfile path incorrect" 1
fi

# Check environment variables
if grep -q 'SPARK_NLP_ENABLED = "false"' ../fly.toml; then
    print_status "Fly.io disables Spark NLP" 0
else
    print_status "Fly.io Spark NLP setting incorrect" 1
fi

echo
echo "====================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All validations passed! Deployment is ready.${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Deploy to Fly.io:    flyctl deploy"
    echo "2. Or run locally:      docker build --target base -t markerengine . && docker run -p 8000:8000 markerengine"
    echo "3. Or use build script: ./docker-build.sh"
    echo
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS validation errors. Please fix before deploying.${NC}"
    exit 1
fi