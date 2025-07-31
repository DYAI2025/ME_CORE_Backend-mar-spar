#!/bin/bash
# Render Deployment Script - ME_CORE_Backend-mar-spar
# This script helps you deploy to Render without sharing sensitive credentials

echo "🚀 ME_CORE_Backend-mar-spar Render Deployment Script"
echo "================================================"
echo ""
echo "⚠️  WICHTIG: Dieses Script fragt nach deinen Credentials,"
echo "   speichert sie aber NUR lokal in .env.local (wird nicht committed)"
echo ""

# Check if .env.local exists
if [ -f .env.local ]; then
    echo "📁 .env.local gefunden. Lade existierende Werte..."
    source .env.local
fi

# Function to prompt for value with default
prompt_with_default() {
    local prompt=$1
    local default=$2
    local var_name=$3
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value=${value:-$default}
    else
        read -p "$prompt: " value
    fi
    
    eval "$var_name='$value'"
}

echo "📝 Bitte gib die folgenden Informationen ein:"
echo ""

# Prompt for Render API Key
prompt_with_default "Render API Key (von https://dashboard.render.com/account/api-keys)" "$RENDER_API_KEY" RENDER_API_KEY

# Prompt for AWS Credentials
echo ""
echo "🔑 AWS Credentials (aus der .csv Datei):"
prompt_with_default "AWS Access Key ID" "$AWS_ACCESS_KEY_ID" AWS_ACCESS_KEY_ID
prompt_with_default "AWS Secret Access Key" "$AWS_SECRET_ACCESS_KEY" AWS_SECRET_ACCESS_KEY

# S3 Bucket name
echo ""
prompt_with_default "S3 Bucket Name" "${S3_BUCKET:-me-core-backups}" S3_BUCKET

# Save to .env.local
cat > .env.local << EOF
# Render Deployment Credentials - DO NOT COMMIT!
RENDER_API_KEY=$RENDER_API_KEY
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
S3_BUCKET=$S3_BUCKET
EOF

echo ""
echo "✅ Credentials gespeichert in .env.local"
echo ""

# Ask if user wants to proceed with deployment
read -p "🚀 Möchtest du jetzt mit dem Deployment fortfahren? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment abgebrochen."
    exit 0
fi

echo ""
echo "📦 Starte Render Deployment..."
echo ""

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI nicht gefunden!"
    echo ""
    echo "Installiere es mit:"
    echo "  Mac: brew install render/render/render"
    echo "  Linux: curl -sSL https://render.com/install.sh | sh"
    echo ""
    echo "Alternative: Nutze das Render Dashboard direkt:"
    echo "1. Gehe zu: https://dashboard.render.com/blueprints"
    echo "2. Klicke 'New Blueprint'"
    echo "3. Wähle dieses Repository"
    echo "4. Füge die Environment Variables aus .env.local hinzu"
    exit 1
fi

# Login to Render
echo "🔐 Logge in Render ein..."
render login

# Deploy blueprint
echo "🚀 Deploye Blueprint..."
render blueprint:deploy \
    --set AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --set AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    --set S3_BUCKET="$S3_BUCKET"

echo ""
echo "✅ Deployment gestartet!"
echo ""
echo "📊 Nächste Schritte:"
echo "1. Überprüfe den Status in: https://dashboard.render.com"
echo "2. Warte bis alle Services grün sind (~10-15 Minuten)"
echo "3. Dashboard URL: https://me-core-dashboard.onrender.com"
echo "4. API URL: https://me-core-backend.onrender.com"
echo ""
echo "🔒 Sicherheit: Lösche .env.local nach erfolgreichem Deployment!"