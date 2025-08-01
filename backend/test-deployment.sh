#!/bin/bash

# =============================================================================
# Comprehensive Deployment Testing Script for ME_CORE Backend
# Tests Docker builds, configuration validation, and deployment readiness
# =============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILURES=()

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((TESTS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((TESTS_FAILED++))
    FAILURES+=("$1")
}

log_header() {
    echo -e "\n${BOLD}=== $1 ===${NC}"
}

# Test functions
test_docker_available() {
    log_header "Checking Docker Availability"
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    log_success "Docker is available and running"
    docker --version
}

test_file_structure() {
    log_header "Validating File Structure"
    
    local required_files=(
        "Dockerfile.fly"
        "fly.toml"
        "requirements-base.txt"
        "minimal_app.py"
        "simple_health.py"
        "config.py"
        "main.py"
        "app.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Found required file: $file"
        else
            log_error "Missing required file: $file"
        fi
    done
    
    # Check for problematic files that might cause issues
    if [[ -f "requirements-spark.txt" ]]; then
        log_warning "Found requirements-spark.txt - ensure Spark dependencies are disabled"
    fi
}

test_dockerfile_configuration() {
    log_header "Validating Dockerfile.fly Configuration"
    
    # Check if Dockerfile.fly exists and has correct base image
    if [[ ! -f "Dockerfile.fly" ]]; then
        log_error "Dockerfile.fly not found"
        return 1
    fi
    
    # Check base image
    if grep -q "FROM python:3.10-slim" Dockerfile.fly; then
        log_success "Using correct Python base image (3.10-slim)"
    else
        log_error "Dockerfile.fly does not use python:3.10-slim base image"
    fi
    
    # Check for Java/OpenJDK (should not be present)
    if grep -qi "openjdk\|java" Dockerfile.fly; then
        log_error "Dockerfile.fly contains Java/OpenJDK dependencies - this will cause deployment failures"
    else
        log_success "No Java/OpenJDK dependencies found in Dockerfile.fly"
    fi
    
    # Check if it uses requirements-base.txt
    if grep -q "requirements-base.txt" Dockerfile.fly; then
        log_success "Using requirements-base.txt (Python-only dependencies)"
    else
        log_error "Dockerfile.fly does not use requirements-base.txt"
    fi
    
    # Check for minimal_app.py as CMD
    if grep -q "minimal_app.py" Dockerfile.fly; then
        log_success "Using minimal_app.py as entry point"
    else
        log_warning "Not using minimal_app.py - may have dependency issues"
    fi
    
    # Check SPARK_NLP_ENABLED=false
    if grep -q "SPARK_NLP_ENABLED=false" Dockerfile.fly; then
        log_success "Spark NLP disabled in Dockerfile.fly"
    else
        log_error "Spark NLP not explicitly disabled in Dockerfile.fly"
    fi
}

test_fly_configuration() {
    log_header "Validating fly.toml Configuration"
    
    if [[ ! -f "fly.toml" ]]; then
        log_error "fly.toml not found"
        return 1
    fi
    
    # Check dockerfile reference
    if grep -q 'dockerfile = "Dockerfile.fly"' fly.toml; then
        log_success "fly.toml correctly references Dockerfile.fly"
    else
        log_error "fly.toml does not reference Dockerfile.fly correctly"
    fi
    
    # Check port configuration
    if grep -q "internal_port = 8000" fly.toml; then
        log_success "Correct internal port configuration (8000)"
    else
        log_error "Internal port not set to 8000 in fly.toml"
    fi
    
    # Check health check path
    if grep -q 'path = "/health"' fly.toml; then
        log_success "Health check path configured correctly"
    else
        log_error "Health check path not configured in fly.toml"
    fi
    
    # Check environment variables
    if grep -q 'SPARK_NLP_ENABLED = "false"' fly.toml; then
        log_success "Spark NLP disabled in fly.toml"
    else
        log_error "Spark NLP not disabled in fly.toml environment"
    fi
}

test_requirements_files() {
    log_header "Validating Requirements Files"
    
    if [[ ! -f "requirements-base.txt" ]]; then
        log_error "requirements-base.txt not found"
        return 1
    fi
    
    # Check for problematic dependencies
    if grep -qi "pyspark\|spark-nlp\|java" requirements-base.txt; then
        log_error "requirements-base.txt contains Java/Spark dependencies"
    else
        log_success "requirements-base.txt contains only Python dependencies"
    fi
    
    # Check for essential dependencies
    local essential_deps=("fastapi" "uvicorn" "pydantic")
    for dep in "${essential_deps[@]}"; do
        if grep -qi "$dep" requirements-base.txt; then
            log_success "Found essential dependency: $dep"
        else
            log_error "Missing essential dependency: $dep"
        fi
    done
}

test_python_imports() {
    log_header "Testing Python Import Dependencies"
    
    # Test if minimal_app.py can import without Java dependencies
    log_info "Testing minimal_app.py imports..."
    
    if python3 -c "
import sys
import os
sys.path.insert(0, '.')

# Set environment to disable Spark
os.environ['SPARK_NLP_ENABLED'] = 'false'

try:
    from minimal_app import app
    print('✓ minimal_app.py imports successfully')
except ImportError as e:
    print(f'✗ Import error in minimal_app.py: {e}')
    sys.exit(1)
except Exception as e:
    print(f'✗ Error in minimal_app.py: {e}')
    sys.exit(1)
"; then
        log_success "minimal_app.py imports successfully"
    else
        log_error "minimal_app.py has import errors"
    fi
}

test_docker_build() {
    log_header "Testing Docker Build"
    
    local image_name="markerengine-test"
    
    log_info "Building Docker image using Dockerfile.fly..."
    
    if docker build -f Dockerfile.fly -t "$image_name" . &> docker_build.log; then
        log_success "Docker build completed successfully"
        
        # Check image size
        local image_size=$(docker images "$image_name" --format "table {{.Size}}" | tail -n 1)
        log_info "Image size: $image_size"
        
        # Quick test that image can start
        log_info "Testing container startup..."
        
        # Start container in background
        local container_id=$(docker run -d -p 8001:8000 "$image_name")
        
        # Wait for startup
        sleep 10
        
        # Test health endpoint
        if curl -f http://localhost:8001/health &> /dev/null; then
            log_success "Container started and health check passed"
        else
            log_error "Container health check failed"
            docker logs "$container_id" | tail -20
        fi
        
        # Cleanup
        docker stop "$container_id" &> /dev/null
        docker rm "$container_id" &> /dev/null
        
    else
        log_error "Docker build failed"
        echo "Build log:"
        tail -20 docker_build.log
        return 1
    fi
}

test_configuration_loading() {
    log_header "Testing Configuration Loading"
    
    # Test configuration with minimal environment
    log_info "Testing configuration with minimal environment..."
    
    if SPARK_NLP_ENABLED=false python3 -c "
import sys
import os
sys.path.insert(0, '.')

# Set minimal environment
os.environ['SPARK_NLP_ENABLED'] = 'false'
os.environ['ENVIRONMENT'] = 'production'

try:
    from config import settings
    print(f'✓ Configuration loaded successfully')
    print(f'  - API Host: {settings.API_HOST}')
    print(f'  - API Port: {settings.API_PORT}')
    print(f'  - Spark NLP: {settings.SPARK_NLP_ENABLED}')
    print(f'  - Environment: {settings.ENVIRONMENT}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    sys.exit(1)
"; then
        log_success "Configuration loads correctly"
    else
        log_error "Configuration has issues"
    fi
}

test_security_configuration() {
    log_header "Security Configuration Review"
    
    # Check for non-root user in Dockerfile
    if grep -q "useradd" Dockerfile.fly && grep -q "USER appuser" Dockerfile.fly; then
        log_success "Container runs as non-root user"
    else
        log_error "Container may be running as root user"
    fi
    
    # Check for HTTPS enforcement
    if grep -q "force_https = true" fly.toml; then
        log_success "HTTPS enforced in fly.toml"
    else
        log_warning "HTTPS not enforced - consider enabling for production"
    fi
    
    # Check for exposed secrets
    if grep -qi "password\|secret\|key.*=" Dockerfile.fly; then
        log_error "Potential secrets exposed in Dockerfile.fly"
    else
        log_success "No obvious secrets in Dockerfile.fly"
    fi
}

cleanup() {
    log_header "Cleanup"
    
    # Remove test Docker images
    if docker images | grep -q "markerengine-test"; then
        docker rmi markerengine-test &> /dev/null || true
        log_info "Cleaned up test Docker images"
    fi
    
    # Remove build logs
    rm -f docker_build.log
}

print_summary() {
    log_header "Test Summary"
    
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "\n${RED}${BOLD}FAILURES:${NC}"
        for failure in "${FAILURES[@]}"; do
            echo -e "  ${RED}✗${NC} $failure"
        done
        echo -e "\n${RED}${BOLD}DEPLOYMENT NOT RECOMMENDED${NC}"
        return 1
    else
        echo -e "\n${GREEN}${BOLD}✅ ALL TESTS PASSED - READY FOR DEPLOYMENT${NC}"
        return 0
    fi
}

# Main execution
main() {
    echo -e "${BOLD}🚀 ME_CORE Backend Deployment Test Suite${NC}"
    echo "Testing deployment readiness for Fly.io..."
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Run all tests
    test_docker_available
    test_file_structure
    test_dockerfile_configuration
    test_fly_configuration
    test_requirements_files
    test_python_imports
    test_configuration_loading
    test_security_configuration
    
    # Docker build test (optional - can be skipped with --skip-build)
    if [[ "$1" != "--skip-build" ]]; then
        test_docker_build
    else
        log_warning "Skipping Docker build test (--skip-build flag used)"
    fi
    
    # Print summary and exit with appropriate code
    print_summary
}

# Handle command line arguments
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [--skip-build] [--help]"
    echo ""
    echo "Options:"
    echo "  --skip-build    Skip the Docker build test (faster execution)"
    echo "  --help, -h      Show this help message"
    exit 0
fi

# Run main function
main "$@"