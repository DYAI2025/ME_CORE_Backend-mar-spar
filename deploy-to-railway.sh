#!/bin/bash

# Railway Deployment Script for ME_CORE Backend
# This script helps deploy the backend to Railway with proper configuration

set -e

echo "🚄 ME_CORE Backend - Railway Deployment Script"
echo "=============================================="

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed!"
    echo "Please install it with: npm install -g @railway/cli"
    echo "Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

# Function to print colored output
print_info() {
    echo -e "\n\033[34m$1\033[0m"
}

print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

# Step 1: Login to Railway
print_info "Step 1: Logging in to Railway..."
railway login
print_success "Logged in successfully!"

# Step 2: Check if we're in a Railway project
if ! railway status &> /dev/null; then
    print_info "Step 2: Creating new Railway project..."
    echo "Enter a name for your Railway project (e.g., me-core-backend):"
    read -r PROJECT_NAME
    railway init --name "$PROJECT_NAME"
    print_success "Project created!"
else
    print_info "Step 2: Using existing Railway project"
    railway status
fi

# Step 3: Add required services (Max 5 services total!)
print_info "Step 3: Adding database services..."
print_warning "Railway erlaubt maximal 5 Services pro Projekt!"
echo "Aktuelle Konfiguration: Backend + MongoDB + Redis = 3 Services"
echo ""

# Check if MongoDB already exists
if railway variables | grep -q "MONGO_URL"; then
    print_warning "MongoDB service already exists"
else
    print_info "Adding MongoDB service..."
    railway add --plugin mongodb
    print_success "MongoDB added!"
fi

# Check if Redis already exists
if railway variables | grep -q "REDIS_URL"; then
    print_warning "Redis service already exists"
else
    print_info "Adding Redis service (optional)..."
    echo "Do you want to add Redis for caching? (y/n)"
    read -r ADD_REDIS
    if [[ "$ADD_REDIS" == "y" ]]; then
        railway add --plugin redis
        print_success "Redis added!"
    else
        print_info "Redis skipped - you can add it later if needed"
    fi
fi

# Step 4: Set environment variables
print_info "Step 4: Setting environment variables..."

# Core variables
railway variables set ENVIRONMENT=production
railway variables set PYTHON_ENV=production
railway variables set MONGO_DB_NAME=marker_engine
railway variables set ENABLE_METRICS=true
railway variables set SPARK_NLP_ENABLED=false
railway variables set CACHE_TYPE=redis
railway variables set CACHE_DEFAULT_TTL=3600

print_success "Environment variables set!"

# Optional API keys
print_info "Step 5: Configure optional API keys..."
echo "Do you have a Moonshot/Kimi API key? (y/n)"
read -r HAS_MOONSHOT
if [[ "$HAS_MOONSHOT" == "y" ]]; then
    echo "Enter your Moonshot API key:"
    read -r -s MOONSHOT_KEY
    railway variables set MOONSHOT_API_KEY="$MOONSHOT_KEY"
    print_success "Moonshot API key set!"
fi

echo "Do you have an OpenAI API key? (y/n)"
read -r HAS_OPENAI
if [[ "$HAS_OPENAI" == "y" ]]; then
    echo "Enter your OpenAI API key:"
    read -r -s OPENAI_KEY
    railway variables set OPENAI_API_KEY="$OPENAI_KEY"
    print_success "OpenAI API key set!"
fi

# Step 6: Deploy
print_info "Step 6: Deploying to Railway..."
echo "Ready to deploy. This will:"
echo "  - Build the backend service"
echo "  - Set up MongoDB connection"
echo "  - Configure health checks"
echo "  - Start the service"
echo ""
echo "Continue? (y/n)"
read -r CONTINUE_DEPLOY

if [[ "$CONTINUE_DEPLOY" == "y" ]]; then
    # Deploy with the simple configuration
    railway up
    
    print_success "Deployment initiated!"
    
    # Get deployment URL
    print_info "Getting deployment information..."
    railway open
    
    print_success "Deployment complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Check the Railway dashboard for deployment status"
    echo "2. Once deployed, test the health endpoint: https://[your-app].up.railway.app/api/health/live"
    echo "3. Configure custom domain if needed"
    echo "4. Monitor logs in Railway dashboard"
else
    print_warning "Deployment cancelled"
fi

print_info "Deployment Summary:"
echo "===================="
railway status
echo ""
echo "Environment variables:"
railway variables

print_success "Script completed!"