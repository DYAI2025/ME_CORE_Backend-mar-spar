#!/bin/bash

# Fly.io Deployment Script for ME_CORE Backend
# This script helps deploy the backend to Fly.io

set -e

echo "🚀 ME_CORE Backend - Fly.io Deployment Script"
echo "============================================"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly CLI (flyctl) is not installed!"
    echo ""
    echo "Please install it:"
    echo "  macOS/Linux: curl -L https://fly.io/install.sh | sh"
    echo "  Windows: powershell -Command \"iwr https://fly.io/install.ps1 -useb | iex\""
    echo ""
    echo "Or visit: https://fly.io/docs/hands-on/install-flyctl/"
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

# Step 1: Login to Fly.io
print_info "Step 1: Logging in to Fly.io..."
if ! flyctl auth whoami &> /dev/null; then
    flyctl auth login
else
    print_success "Already logged in as $(flyctl auth whoami)"
fi

# Step 2: Create or use existing app
print_info "Step 2: Setting up Fly.io app..."
if ! flyctl status &> /dev/null; then
    print_info "Creating new Fly.io app..."
    flyctl launch --name me-core-backend --region fra --no-deploy
    print_success "App created!"
else
    print_warning "Using existing app"
    flyctl status
fi

# Step 3: MongoDB Atlas setup reminder
print_info "Step 3: MongoDB Setup"
print_warning "Fly.io doesn't provide MongoDB. You need MongoDB Atlas (free tier available)"
echo ""
echo "1. Go to: https://www.mongodb.com/cloud/atlas"
echo "2. Create a free cluster"
echo "3. Get your connection string"
echo "4. It should look like: mongodb+srv://username:password@cluster.mongodb.net/dbname"
echo ""
echo "Do you have a MongoDB Atlas connection string ready? (y/n)"
read -r HAS_MONGODB

if [[ "$HAS_MONGODB" != "y" ]]; then
    print_warning "Please set up MongoDB Atlas first, then run this script again"
    echo "Guide: https://www.mongodb.com/docs/atlas/getting-started/"
    exit 1
fi

# Step 4: Set secrets
print_info "Step 4: Setting environment variables..."

echo "Enter your MongoDB Atlas connection string:"
read -r -s MONGODB_URL
flyctl secrets set DATABASE_URL="$MONGODB_URL"
print_success "MongoDB URL set!"

# Optional API keys
echo ""
echo "Do you have a Moonshot/Kimi API key? (y/n)"
read -r HAS_MOONSHOT
if [[ "$HAS_MOONSHOT" == "y" ]]; then
    echo "Enter your Moonshot API key:"
    read -r -s MOONSHOT_KEY
    flyctl secrets set MOONSHOT_API_KEY="$MOONSHOT_KEY"
    print_success "Moonshot API key set!"
fi

# Step 5: Deploy
print_info "Step 5: Deploying to Fly.io..."
echo "Ready to deploy. This will:"
echo "  - Build the backend Docker image"
echo "  - Deploy to Fly.io servers"
echo "  - Set up health checks"
echo "  - Provide a public URL"
echo ""
echo "Continue? (y/n)"
read -r CONTINUE_DEPLOY

if [[ "$CONTINUE_DEPLOY" == "y" ]]; then
    flyctl deploy
    
    print_success "Deployment complete!"
    
    # Get app info
    print_info "App Information:"
    flyctl info
    
    echo ""
    print_info "Your app is available at:"
    flyctl open --json | grep -o '"url":"[^"]*' | grep -o '[^"]*$'
    
    echo ""
    print_success "Backend deployed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Test health endpoint: https://me-core-backend.fly.dev/api/health/live"
    echo "2. View logs: flyctl logs"
    echo "3. Check status: flyctl status"
    echo "4. Scale if needed: flyctl scale vm shared-cpu-1x --count 1"
else
    print_warning "Deployment cancelled"
fi

print_success "Script completed!"