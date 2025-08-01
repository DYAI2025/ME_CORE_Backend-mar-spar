#!/bin/bash
# Fly.io Deployment Validation Script

set -e

echo "🚀 MarkerEngine Fly.io Deployment Validation"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "fly.toml" ]; then
    echo "❌ fly.toml not found. Run this script from the repository root."
    exit 1
fi

echo "✅ Repository structure looks good"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Install it from: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

echo "✅ flyctl is installed"

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Run: flyctl auth login"
    exit 1
fi

echo "✅ Logged in to Fly.io"

# Validate backend structure
if [ ! -f "backend/minimal_app.py" ]; then
    echo "❌ backend/minimal_app.py not found. This is required for deployment."
    exit 1
fi

if [ ! -f "backend/requirements-base.txt" ]; then
    echo "❌ backend/requirements-base.txt not found."
    exit 1
fi

echo "✅ Backend application files present"

# Check for resources directory
if [ ! -d "resources" ]; then
    echo "⚠️  Creating missing resources directory..."
    mkdir -p resources/detectors resources/models resources/schemas
fi

echo "✅ Resources directory exists"

# Validate MongoDB connection
echo ""
echo "📋 Environment Validation"
echo "========================="
echo "⚠️  Please ensure you have set the following secrets:"
echo "   flyctl secrets set DATABASE_URL=\"mongodb+srv://username:password@cluster.mongodb.net/marker_engine\""
echo ""
echo "Optional secrets (can be added later):"
echo "   flyctl secrets set MOONSHOT_API_KEY=\"your_key\""
echo "   flyctl secrets set OPENAI_API_KEY=\"your_key\""
echo ""

# Check current secrets
echo "Current secrets:"
flyctl secrets list

echo ""
echo "🏗️  Ready to deploy!"
echo ""
echo "Next steps:"
echo "1. Set your MongoDB connection string:"
echo "   flyctl secrets set DATABASE_URL=\"your_mongodb_connection_string\""
echo ""
echo "2. Deploy the application:"
echo "   flyctl deploy"
echo ""
echo "3. Check deployment status:"
echo "   flyctl status"
echo ""
echo "4. View logs:"
echo "   flyctl logs"
echo ""
echo "5. Open the application:"
echo "   flyctl open"