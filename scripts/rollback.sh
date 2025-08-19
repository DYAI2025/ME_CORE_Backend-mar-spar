#!/bin/bash

# =============================================================================
# Rollback Script for MarkerEngine Core Backend
# Supports: Render, Fly.io, Railway
# Usage: ./scripts/rollback.sh [platform] [options]
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
PLATFORM=""
TARGET_VERSION=""
DRY_RUN=false
FORCE=false

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
${BOLD}MarkerEngine Rollback Script${NC}

${BOLD}USAGE:${NC}
    $0 [PLATFORM] [OPTIONS]

${BOLD}PLATFORMS:${NC}
    render     Rollback on Render.com
    fly        Rollback on Fly.io
    railway    Rollback on Railway.app

${BOLD}OPTIONS:${NC}
    --version=VERSION  Specific version to rollback to
    --dry-run         Show what would be rolled back
    --force           Force rollback without confirmation
    --help            Show this help message

${BOLD}EXAMPLES:${NC}
    $0 fly --version=v123              # Rollback Fly.io to specific version
    $0 render --dry-run               # Show Render rollback options
    $0 railway --force                # Force Railway rollback to previous version

EOF
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            render|fly|railway)
                PLATFORM="$1"
                shift
                ;;
            --version=*)
                TARGET_VERSION="${1#*=}"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
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

    if [ -z "$PLATFORM" ]; then
        log_error "Platform is required"
        show_help
        exit 1
    fi
}

# Confirm rollback
confirm_rollback() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    log_warning "Are you sure you want to rollback $PLATFORM?"
    if [ -n "$TARGET_VERSION" ]; then
        echo "Target version: $TARGET_VERSION"
    else
        echo "Target: Previous version"
    fi
    
    echo -n "Type 'yes' to confirm: "
    read -r confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
}

# Rollback on Render
rollback_render() {
    log_header "Rolling back on Render"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would rollback Render deployment"
        log_info "Manual steps:"
        log_info "1. Go to Render dashboard"
        log_info "2. Navigate to your service"
        log_info "3. Go to 'Deploys' tab"
        log_info "4. Click 'Rollback' on previous successful deployment"
        return 0
    fi

    log_info "Render rollback requires manual action through dashboard"
    log_info "Steps to rollback:"
    echo "1. Open https://dashboard.render.com"
    echo "2. Navigate to your MarkerEngine service"
    echo "3. Click on the 'Deploys' tab"
    echo "4. Find the previous successful deployment"
    echo "5. Click the 'Rollback' button"
    
    log_warning "Alternatively, you can redeploy a previous Git commit:"
    echo "git log --oneline -10  # Find the commit to rollback to"
    echo "git checkout <commit-hash>"
    echo "git push origin main --force  # Trigger new deployment"
}

# Rollback on Fly.io
rollback_fly() {
    log_header "Rolling back on Fly.io"
    
    # Check if flyctl is available
    if ! command -v flyctl &> /dev/null && ! command -v fly &> /dev/null; then
        log_error "Fly CLI not found. Please install flyctl"
        exit 1
    fi

    local fly_cmd="flyctl"
    if command -v fly &> /dev/null; then
        fly_cmd="fly"
    fi

    # Determine app name
    local app_name="me-core-backend"
    if [ -f "$ROOT_DIR/fly.toml" ]; then
        app_name=$(grep -E "^app = " "$ROOT_DIR/fly.toml" | cut -d'"' -f2 || echo "me-core-backend")
    fi

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would rollback Fly.io app: $app_name"
        log_info "Available versions:"
        $fly_cmd releases list --app "$app_name" || log_warning "Could not fetch releases"
        return 0
    fi

    log_info "Fetching available releases for app: $app_name"
    $fly_cmd releases list --app "$app_name"
    
    if [ -n "$TARGET_VERSION" ]; then
        log_info "Rolling back to version: $TARGET_VERSION"
        $fly_cmd releases rollback "$TARGET_VERSION" --app "$app_name"
    else
        log_info "Rolling back to previous version..."
        # Get the second most recent release (first is current)
        local prev_version
        prev_version=$($fly_cmd releases list --app "$app_name" --json | jq -r '.[1].version' 2>/dev/null || echo "")
        
        if [ -n "$prev_version" ] && [ "$prev_version" != "null" ]; then
            log_info "Rolling back to version: $prev_version"
            $fly_cmd releases rollback "$prev_version" --app "$app_name"
        else
            log_error "Could not determine previous version. Please specify --version=VERSION"
            exit 1
        fi
    fi
    
    log_success "Fly.io rollback completed"
}

# Rollback on Railway
rollback_railway() {
    log_header "Rolling back on Railway"
    
    # Check if railway CLI is available
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not found. Please install railway CLI"
        exit 1
    fi

    # Check if logged in
    if ! railway whoami &>/dev/null; then
        log_error "Not logged in to Railway. Run: railway login"
        exit 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would rollback Railway deployment"
        log_info "Available options:"
        log_info "1. Use Railway dashboard to rollback"
        log_info "2. Redeploy previous commit"
        return 0
    fi

    log_info "Railway rollback options:"
    echo "1. Using Railway CLI (if available):"
    echo "   railway rollback"
    echo ""
    echo "2. Using Railway dashboard:"
    echo "   - Go to https://railway.app/dashboard"
    echo "   - Select your project"
    echo "   - Go to deployments tab"
    echo "   - Click rollback on previous deployment"
    echo ""
    echo "3. Redeploy previous commit:"
    echo "   git log --oneline -10"
    echo "   git checkout <previous-commit>"
    echo "   railway up"

    # Try automatic rollback if railway supports it
    log_info "Attempting automatic rollback..."
    if railway rollback &>/dev/null; then
        log_success "Railway rollback completed"
    else
        log_warning "Automatic rollback not available. Use manual steps above."
    fi
}

# Post-rollback validation
post_rollback_validation() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    log_header "Post-rollback Validation"
    
    log_info "Rollback completed. Recommended validation steps:"
    echo "1. Check application health endpoint"
    echo "2. Verify core functionality works"
    echo "3. Monitor logs for errors"
    echo "4. Test critical user flows"
    echo "5. Check database connectivity"
    
    case $PLATFORM in
        render)
            echo "6. Monitor Render dashboard for deployment status"
            ;;
        fly)
            echo "6. Run: flyctl status --app <your-app>"
            echo "7. Run: flyctl logs --app <your-app>"
            ;;
        railway)
            echo "6. Check Railway dashboard"
            echo "7. Run: railway logs"
            ;;
    esac
    
    log_warning "Remember to:"
    echo "- Notify team of rollback"
    echo "- Document rollback reason"
    echo "- Plan fix for original issue"
    echo "- Schedule re-deployment after fix"
}

# Main execution
main() {
    log_header "MarkerEngine Rollback Script"
    
    parse_arguments "$@"
    
    echo "Platform: $PLATFORM"
    echo "Target Version: ${TARGET_VERSION:-"Previous version"}"
    echo "Dry Run: $DRY_RUN"
    echo "Force: $FORCE"
    echo ""

    confirm_rollback
    
    case $PLATFORM in
        render)
            rollback_render
            ;;
        fly)
            rollback_fly
            ;;
        railway)
            rollback_railway
            ;;
    esac
    
    post_rollback_validation
    
    log_success "Rollback process completed!"
}

# Execute main function
main "$@"