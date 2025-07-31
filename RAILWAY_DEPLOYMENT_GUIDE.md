# Railway Deployment Guide für ME_CORE Backend

## 🚄 Warum Railway?

### Vorteile gegenüber Render:
- **MongoDB inklusive** - Railway bietet MongoDB als Service!
- **Transparente Preise** - Pay-as-you-go, keine festen Tiers
- **$5 Credit** zum Start (kostenlos testen)
- **Einfachere Konfiguration** - Alles in einem Projekt
- **Bessere Entwickler-Experience**

## 📋 Deployment Schritte

### 1. Railway Account erstellen
```bash
# Railway CLI installieren (optional)
npm install -g @railway/cli

# Oder direkt über railway.app
```

### 2. Neues Projekt erstellen

#### Option A: Via GitHub (Empfohlen)
1. Gehe zu [railway.app/new](https://railway.app/new)
2. "Deploy from GitHub repo"
3. Wähle: `DYAI2025/ME_CORE_Backend-mar-spar`
4. Railway erkennt die Services automatisch

#### Option B: Via CLI
```bash
railway login
railway init
railway link [project-id]
```

### 3. Services hinzufügen

In Railway Dashboard:
1. **"+ New Service"** → **MongoDB**
   - Automatisch konfiguriert
   - Connection String wird als `DATABASE_URL` verfügbar

2. **"+ New Service"** → **Redis**
   - Ebenfalls automatisch
   - Als `REDIS_URL` verfügbar

3. **Backend Service**:
   - Source: GitHub Repo
   - Root Directory: `/backend`
   - Start Command: Auto-detected

4. **Dashboard Service**:
   - Source: GitHub Repo  
   - Root Directory: `/dashboard`
   - Build Command: `npm run build`

### 4. Environment Variables

Railway macht das elegant mit Service-Referenzen:

```bash
# Backend erhält automatisch:
DATABASE_URL=${{MongoDB.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Dashboard erhält:
NEXT_PUBLIC_API_URL=${{Backend.RAILWAY_PUBLIC_DOMAIN}}
```

### 5. Deployment

```bash
# Automatisch bei Git Push
git push origin main

# Oder manuell
railway up
```

## 💰 Kostenvergleich

### Railway Pricing (Pay-as-you-go):
- **Backend**: ~$5-10/Monat
- **Dashboard**: ~$3-5/Monat  
- **MongoDB**: ~$5-10/Monat
- **Redis**: ~$5/Monat
- **Total**: ~$18-30/Monat

### Vs Render:
- Render: $67/Monat (fixed)
- Railway: $18-30/Monat (usage-based)
- **Ersparnis**: 50-70%!

## 🚀 Quick Deploy Script

```bash
#!/bin/bash
# deploy-to-railway.sh

echo "🚄 Deploying to Railway..."

# Environment check
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login and deploy
railway login
railway init --name "me-core-backend"

# Add services
railway add mongodb
railway add redis

# Deploy
railway up

echo "✅ Deployment complete!"
echo "🌐 Visit your dashboard at: $(railway open)"
```

## 🔧 railway.json Configuration

Die `railway.json` im Projekt-Root konfiguriert:
- Service-Abhängigkeiten
- Health Checks
- Auto-Scaling
- Environment Variables

## ⚡ MongoDB auf Railway

Railway's MongoDB Service:
- **Automatisches Backup** täglich
- **Persistent Storage** inklusive
- **Connection Pooling** vorkonfiguriert
- **Monitoring** im Dashboard

Connection String Format:
```
mongodb://mongo:[password]@containers-us-west-123.railway.app:7891
```

## 🎯 Nächste Schritte

1. **Railway Account** erstellen
2. **GitHub Repo** verbinden
3. **Services** hinzufügen (MongoDB, Redis)
4. **Deploy** triggern
5. **Custom Domain** hinzufügen (optional)

## 📊 Monitoring

Railway Dashboard zeigt:
- CPU/Memory Usage
- Request Metrics
- Database Connections
- Logs in Echtzeit
- Kosten-Übersicht

## 🆘 Troubleshooting

### Port Binding
```javascript
// Railway setzt PORT automatisch
const port = process.env.PORT || 8000
```

### MongoDB Connection
```python
# Railway URL Format beachten
MONGODB_URI = os.getenv("DATABASE_URL")
# Nicht MONGODB_URI verwenden!
```

### Build Fehler
- Überprüfe `nixpacks.toml` oder `Dockerfile`
- Railway baut mit Nixpacks by default

---

Railway ist perfekt für dein Projekt - günstiger, einfacher und mit MongoDB inklusive! 🚄