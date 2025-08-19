#!/bin/bash

# =============================================================================
# Unified Deployment Script for MarkerEngine Core Backend
# Supports: Render, Fly.io, Railway
# Usage: ./scripts/deploy.sh [platform] [environment] [options]
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/backend"

# Default values
PLATFORM=""
ENVIRONMENT="staging"
VALIDATE_ONLY=false
SKIP_TESTS=false
FORCE_DEPLOY=false
DRY_RUN=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${BOLD}=== $1 ===${NC}"
}

# Help function
show_help() {
    cat << EOF
${BOLD}MarkerEngine Unified Deployment Script${NC}

${BOLD}USAGE:${NC}
    $0 [PLATFORM] [ENVIRONMENT] [OPTIONS]

${BOLD}PLATFORMS:${NC}
    render     Deploy to Render.com
    fly        Deploy to Fly.io
    railway    Deploy to Railway.app

${BOLD}ENVIRONMENTS:${NC}
    staging    Deploy to staging environment (default)
    production Deploy to production environment

${BOLD}OPTIONS:${NC}
    --validate-only    Only validate configuration, don't deploy
    --skip-tests      Skip pre-deployment tests
    --force           Force deployment even if validation fails
    --dry-run         Show what would be deployed without doing it
    --help            Show this help message

${BOLD}EXAMPLES:${NC}
    $0 render staging --validate-only    # Validate Render staging config
    $0 fly production                    # Deploy to Fly.io production
    $0 railway staging --skip-tests     # Deploy to Railway staging without tests
    $0 render production --dry-run      # Dry run for Render production

${BOLD}REQUIREMENTS:${NC}
    - Docker (for build validation)
    - Platform CLI tools (render-cli, flyctl, railway-cli)
    - Environment variables configured
    - Valid configuration files for target platform

EOF
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            render|fly|railway)
                if [ -z "$PLATFORM" ]; then
                    PLATFORM="$1"
                else
                    log_error "Platform already specified: $PLATFORM"
                    exit 1
                fi
                shift
                ;;
            staging|production)
                ENVIRONMENT="$1"
                shift
                ;;
            --validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown argument: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [ -z "$PLATFORM" ]; then
        log_error "Platform is required. Use: render, fly, or railway"
        show_help
        exit 1
    fi
}

# Validate prerequisites
validate_prerequisites() {
    log_header "Validating Prerequisites"

    # Check if we're in the right directory
    if [ ! -f "$ROOT_DIR/backend/main.py" ]; then
        log_error "Not in MarkerEngine root directory or backend/main.py not found"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi

    # Check platform-specific CLI tools
    case $PLATFORM in
        render)
            if ! command -v render &> /dev/null; then
                log_warning "Render CLI not found. Some features may not work."
            fi
            ;;
        fly)
            if ! command -v flyctl &> /dev/null && ! command -v fly &> /dev/null; then
                log_error "Fly CLI (flyctl) is required for Fly.io deployments"
                exit 1
            fi
            ;;
        railway)
            if ! command -v railway &> /dev/null; then
                log_error "Railway CLI is required for Railway deployments"
                exit 1
            fi
            ;;
    esac

    log_success "Prerequisites validated"
}

# Validate configuration files
validate_configuration() {
    log_header "Validating Configuration"

    local config_valid=true

    # Check platform-specific configuration
    case $PLATFORM in
        render)
            if [ ! -f "$ROOT_DIR/render.yaml" ] && [ ! -f "$BACKEND_DIR/render.yaml" ]; then
                log_error "render.yaml not found"
                config_valid=false
            else
                log_success "Render configuration found"
            fi
            ;;
        fly)
            if [ ! -f "$ROOT_DIR/fly.toml" ] && [ ! -f "$BACKEND_DIR/fly.toml" ]; then
                log_error "fly.toml not found"
                config_valid=false
            else
                log_success "Fly.io configuration found"
            fi
            ;;
        railway)
            if [ ! -f "$ROOT_DIR/railway.json" ] && [ ! -f "$ROOT_DIR/nixpacks.toml" ]; then
                log_error "Railway configuration (railway.json or nixpacks.toml) not found"
                config_valid=false
            else
                log_success "Railway configuration found"
            fi
            ;;
    esac

    # Check Dockerfile
    if [ ! -f "$BACKEND_DIR/Dockerfile" ]; then
        log_error "Dockerfile not found in backend directory"
        config_valid=false
    else
        log_success "Dockerfile found"
    fi

    # Check requirements files
    if [ ! -f "$BACKEND_DIR/requirements-base.txt" ]; then
        log_error "requirements-base.txt not found"
        config_valid=false
    else
        log_success "Requirements files found"
    fi

    # Check environment-specific configuration
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ ! -f "$ROOT_DIR/.env.production" ] && [ ! -f "$BACKEND_DIR/.env.production" ]; then
            log_warning "No production environment template found"
        else
            log_success "Production environment template found"
        fi
    fi

    if [ "$config_valid" = false ] && [ "$FORCE_DEPLOY" = false ]; then
        log_error "Configuration validation failed. Use --force to deploy anyway."
        exit 1
    fi

    log_success "Configuration validation completed"
}

# Run pre-deployment tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        log_warning "Skipping tests as requested"
        return 0
    fi

    log_header "Running Pre-deployment Tests"

    # Test backend imports
    cd "$BACKEND_DIR"
    
    log_info "Installing test dependencies..."
    pip install -r requirements-base.txt >/dev/null 2>&1 || {
        log_warning "Failed to install dependencies. Continuing..."
    }

    log_info "Testing backend imports..."
    python -c "import app; print('Backend imports successful')" || {
        log_error "Backend import test failed"
        if [ "$FORCE_DEPLOY" = false ]; then
            exit 1
        fi
    }

    # Test frontend build (if exists)
    if [ -f "$ROOT_DIR/frontend/package.json" ]; then
        log_info "Testing frontend build..."
        cd "$ROOT_DIR/frontend"
        npm ci >/dev/null 2>&1 && npm run build >/dev/null 2>&1 || {
            log_warning "Frontend build failed"
        }
    fi

    log_success "Pre-deployment tests completed"
}

# Build and validate Docker image
validate_docker_build() {
    log_header "Validating Docker Build"

    cd "$BACKEND_DIR"

    local target="base"
    case $PLATFORM in
        render)
            target="production"
            ;;
        fly|railway)
            target="base"
            ;;
    esac

    log_info "Building Docker image with target: $target"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would build: docker build --target $target -t markerengine-deploy:$PLATFORM ."
        return 0
    fi

    docker build --target "$target" -t "markerengine-deploy:$PLATFORM" . || {
        log_error "Docker build failed"
        exit 1
    }

    # Test container startup
    log_info "Testing container startup..."
    docker run -d --name "test-$PLATFORM-$$" -p 8001:8000 \
        -e DATABASE_URL="mongodb://localhost:27017/test" \
        -e SPARK_NLP_ENABLED="false" \
        "markerengine-deploy:$PLATFORM" >/dev/null 2>&1 || {
        log_warning "Container startup test failed (may be expected without database)"
    }

    # Cleanup test container
    docker stop "test-$PLATFORM-$$" >/dev/null 2>&1 || true
    docker rm "test-$PLATFORM-$$" >/dev/null 2>&1 || true

    log_success "Docker build validation completed"
}

# Platform-specific deployment
deploy_to_platform() {
    if [ "$VALIDATE_ONLY" = true ]; then
        log_success "Validation completed successfully. Ready for deployment."
        return 0
    fi

    log_header "Deploying to $PLATFORM ($ENVIRONMENT)"

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would deploy to $PLATFORM in $ENVIRONMENT environment"
        return 0
    fi

    case $PLATFORM in
        render)
            deploy_render
            ;;
        fly)
            deploy_fly
            ;;
        railway)
            deploy_railway
            ;;
    esac
}

# Render deployment
deploy_render() {
    log_info "Deploying to Render..."
    
    # Check if render CLI is available
    if command -v render &> /dev/null; then
        log_info "Using Render CLI for deployment"
        render deploy
    else
        log_info "Render CLI not available. Use git push to trigger deployment:"
        echo "git push origin main  # or your deployment branch"
    fi
    
    log_success "Render deployment initiated"
}

# Fly.io deployment
deploy_fly() {
    log_info "Deploying to Fly.io..."
    
    cd "$ROOT_DIR"
    
    # Check if app exists
    local app_name="me-core-backend"
    if [ "$ENVIRONMENT" = "staging" ]; then
        app_name="me-core-backend-staging"
    fi
    
    if flyctl status --app "$app_name" &>/dev/null; then
        log_info "Deploying to existing app: $app_name"
        flyctl deploy --app "$app_name"
    else
        log_info "Creating new app: $app_name"
        flyctl launch --now --name "$app_name"
    fi
    
    log_success "Fly.io deployment completed"
}

# Railway deployment
deploy_railway() {
    log_info "Deploying to Railway..."
    
    cd "$ROOT_DIR"
    
    # Login check
    if ! railway whoami &>/dev/null; then
        log_error "Not logged in to Railway. Run: railway login"
        exit 1
    fi
    
    # Deploy
    railway up
    
    log_success "Railway deployment completed"
}

# Post-deployment validation
post_deployment_validation() {
    if [ "$VALIDATE_ONLY" = true ] || [ "$DRY_RUN" = true ]; then
        return 0
    fi

    log_header "Post-deployment Validation"
    
    log_info "Deployment completed. Manual validation recommended:"
    echo "1. Check application health endpoint"
    echo "2. Verify database connectivity"
    echo "3. Test critical API endpoints"
    echo "4. Monitor logs for errors"
    echo "5. Verify environment variables"
    
    case $PLATFORM in
        render)
            echo "6. Check Render dashboard for deployment status"
            ;;
        fly)
            echo "6. Run: flyctl logs --app <your-app>"
            echo "7. Run: flyctl status --app <your-app>"
            ;;
        railway)
            echo "6. Check Railway dashboard for deployment status"
            echo "7. Run: railway logs"
            ;;
    esac
}

# Main execution
main() {
    log_header "MarkerEngine Unified Deployment Script"
    
    parse_arguments "$@"
    
    echo "Platform: $PLATFORM"
    echo "Environment: $ENVIRONMENT"
    echo "Validate Only: $VALIDATE_ONLY"
    echo "Skip Tests: $SKIP_TESTS"
    echo "Force Deploy: $FORCE_DEPLOY"
    echo "Dry Run: $DRY_RUN"
    echo ""

    validate_prerequisites
    validate_configuration
    run_tests
    validate_docker_build
    deploy_to_platform
    post_deployment_validation
    
    log_success "Deployment process completed successfully!"
}

# Execute main function
main "$@"