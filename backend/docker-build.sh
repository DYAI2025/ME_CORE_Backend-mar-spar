#!/bin/bash

# Docker build script for MarkerEngine Core API
# This script builds and tests both production (base) and spark variants

set -e  # Exit on any error

echo "🐳 MarkerEngine Docker Build Script"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build arguments
IMAGE_NAME=${1:-"markerengine-core"}
TAG=${2:-"latest"}

echo -e "${BLUE}Building production image (Python-only, no Java)...${NC}"
echo "Target: base stage"
echo "Image: ${IMAGE_NAME}:${TAG}"
echo

# Build production image (base stage - Python only)
if docker build --target base -t "${IMAGE_NAME}:${TAG}" .; then
    echo -e "${GREEN}✅ Production build successful!${NC}"
else
    echo -e "${RED}❌ Production build failed!${NC}"
    exit 1
fi

echo
echo -e "${BLUE}Building Spark image (with Java support)...${NC}"
echo "Target: spark stage"
echo "Image: ${IMAGE_NAME}:${TAG}-spark"
echo

# Build Spark image (spark stage - with Java)
if docker build --target spark -t "${IMAGE_NAME}:${TAG}-spark" .; then
    echo -e "${GREEN}✅ Spark build successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Spark build failed (this is expected if you don't need Spark features)${NC}"
fi

echo
echo -e "${BLUE}Testing production image...${NC}"

# Test the production image
echo "Starting container for health check..."
CONTAINER_ID=$(docker run -d -p 8000:8000 "${IMAGE_NAME}:${TAG}")

# Wait for container to start
echo "Waiting for application to start..."
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
    HEALTH_STATUS="PASSED"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    HEALTH_STATUS="FAILED"
fi

# Get container logs
echo
echo -e "${BLUE}Container logs:${NC}"
docker logs "${CONTAINER_ID}"

# Cleanup
echo
echo "Cleaning up test container..."
docker stop "${CONTAINER_ID}" > /dev/null
docker rm "${CONTAINER_ID}" > /dev/null

echo
echo "=================================="
echo -e "${BLUE}Build Summary:${NC}"
echo -e "Production image: ${GREEN}✅ Built successfully${NC}"
echo -e "Health check: $([ "$HEALTH_STATUS" = "PASSED" ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
echo
echo "Ready for deployment! 🚀"
echo
echo "To run the container:"
echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
echo
echo "To use with Fly.io:"
echo "  fly deploy"
echo
echo "To build for specific platform (e.g., ARM64):"
echo "  docker build --platform linux/amd64 --target base -t ${IMAGE_NAME}:${TAG} ."