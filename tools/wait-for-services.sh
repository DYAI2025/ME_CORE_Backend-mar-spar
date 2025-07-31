#!/bin/bash
# Wait for all services to be ready

set -e

echo "Waiting for services to be ready..."

# Function to check if a service is ready
check_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Checking $name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo " ✓ Ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo " ✗ Failed!"
    return 1
}

# Check MongoDB
check_mongodb() {
    local max_attempts=30
    local attempt=1
    
    echo -n "Checking MongoDB..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec me-core-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo " ✓ Ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo " ✗ Failed!"
    return 1
}

# Check Redis
check_redis() {
    local max_attempts=30
    local attempt=1
    
    echo -n "Checking Redis..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec me-core-redis redis-cli ping > /dev/null 2>&1; then
            echo " ✓ Ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo " ✗ Failed!"
    return 1
}

# Check all services
check_mongodb || exit 1
check_redis || exit 1
check_service "Backend API" "http://localhost:8000/api/health/live" || exit 1
check_service "Frontend" "http://localhost:3000" || exit 1

# Optional: Check Spark if enabled
if [ "${SPARK_NLP_ENABLED}" = "true" ]; then
    check_service "Spark NLP" "http://localhost:8090/health" || exit 1
fi

echo ""
echo "All services are ready! 🎉"