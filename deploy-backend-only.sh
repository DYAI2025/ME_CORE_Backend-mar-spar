#!/bin/bash

# Deploy only the Python backend to fly.io

set -e

echo "🚀 Deploying ME_CORE Python Backend to fly.io"
echo "========================================="

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: backend/main.py not found. Are you in the ME_CORE_Backend-mar-spar root directory?"
    exit 1
fi

# Check fly CLI
if ! command -v fly &> /dev/null; then
    echo "Installing fly CLI..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Deploy
echo "🚀 Deploying to fly.io..."
echo "Note: This will deploy ONLY the Python backend from the backend/ directory"

# Launch or deploy
if fly status &> /dev/null; then
    echo "📦 App exists, deploying..."
    fly deploy
else
    echo "🆕 Creating new app..."
    fly launch --now --name me-core-backend --region sin
fi

# Set secrets if needed
echo ""
echo "📝 Don't forget to set your secrets:"
echo "fly secrets set MONGODB_URL='your-mongodb-url'"
echo "fly secrets set SECRET_KEY='your-secret-key'"

echo "✅ Deployment complete!"
echo "🌐 Your backend is at: https://me-core-backend.fly.dev"