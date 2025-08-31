#!/bin/bash

# Fly.io Deployment Fix Script
# Addresses common issues: no IP address, app not running, etc.

set -e

echo "🔧 Fly.io Deployment Fix Script"
echo "==============================="
echo ""

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

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Run: flyctl auth login"
    exit 1
fi

echo "✅ flyctl is installed and authenticated"
echo ""

# Get current app status
echo "📊 Current App Status:"
echo "====================="
flyctl status || echo "⚠️  App may not exist or be accessible"
echo ""

# Check if app has machines running
echo "🖥️  Machine Status:"
echo "=================="
flyctl machines list || echo "⚠️  No machines found or error accessing machines"
echo ""

# Check current scale
echo "📈 Current Scale Configuration:"
echo "=============================="
flyctl scale show || echo "⚠️  Could not retrieve scale information"
echo ""

echo "🔧 Applying Fixes..."
echo "===================="

# Fix 1: Ensure at least one machine is running
echo "1. Setting minimum machines to 1..."
flyctl scale count 1 || echo "⚠️  Could not scale machines"

# Fix 2: Start any stopped machines
echo "2. Starting any stopped machines..."
flyctl machines start || echo "ℹ️  No stopped machines to start or already running"

# Fix 3: Check health endpoints
echo "3. Testing health endpoints..."
APP_URL=$(flyctl info --json 2>/dev/null | grep -o '"hostname":"[^"]*' | cut -d'"' -f4 || echo "")
if [ -n "$APP_URL" ]; then
    echo "   Testing https://$APP_URL/health"
    curl --max-time 10 --connect-timeout 5 -f "https://$APP_URL/health" || echo "   ⚠️  Health check failed"
    echo ""
    echo "   Testing https://$APP_URL/api/health/live"
    curl --max-time 10 --connect-timeout 5 -f "https://$APP_URL/api/health/live" || echo "   ⚠️  Live health check failed" 
    echo ""
else
    echo "   ⚠️  Could not determine app URL"
fi

# Fix 4: Redeploy if needed
echo "4. Checking if redeploy is needed..."
read -p "   Do you want to redeploy the app? (y/n): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Redeploying..."
    flyctl deploy
    echo "   ✅ Redeploy completed"
else
    echo "   ℹ️  Skipping redeploy"
fi

echo ""
echo "🎯 Final Status Check:"
echo "====================="
flyctl status
echo ""

echo "✅ Fix script completed!"
echo ""
echo "📝 If the app still has issues:"
echo "1. Check logs: flyctl logs"
echo "2. Monitor machines: flyctl machines list"
echo "3. Test health: curl https://your-app.fly.dev/health"
echo "4. Check secrets: flyctl secrets list"