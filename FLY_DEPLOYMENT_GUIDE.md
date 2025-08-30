# 🚀 Fly.io Deployment Guide für ME_CORE Backend

## 📋 Schnellstart

```bash
# 1. Fly CLI installieren (falls noch nicht vorhanden)
curl -L https://fly.io/install.sh | sh

# 2. Deployment Script ausführen
./deploy-to-fly.sh
```

## 🔧 Was wurde vorbereitet?

### 1. **fly.toml** - Fly.io Konfiguration
- App Name: `me-core-backend`
- Region: `fra` (Frankfurt - optimal für Europa)
- Port: 8000 (intern)
- Health Check: `/api/health/live`
- Auto-Rollback aktiviert

### 2. **Dockerfile** optimiert
- Port 8000 fest konfiguriert
- Kompatibel mit Fly.io

### 3. **MongoDB Atlas** Setup
- Fly.io bietet kein MongoDB
- Nutze MongoDB Atlas (kostenlos): https://www.mongodb.com/cloud/atlas
- Connection String Format: `mongodb+srv://user:pass@cluster.mongodb.net/dbname`

## 📝 Manuelle Deployment-Schritte

### 1. MongoDB Atlas einrichten
```
1. Gehe zu https://www.mongodb.com/cloud/atlas
2. Erstelle kostenlosen Cluster (M0 Sandbox)
3. Erstelle Database User
4. Whitelist IP: 0.0.0.0/0 (für Fly.io)
5. Kopiere Connection String
```

### 2. Fly.io App erstellen
```bash
# Login
flyctl auth login

# App erstellen
flyctl launch --name me-core-backend --region fra --no-deploy

# Secrets setzen
flyctl secrets set DATABASE_URL="mongodb+srv://..."
```

### 3. Deployen
```bash
flyctl deploy
```

## 🔑 Environment Variables

### Pflicht:
```bash
flyctl secrets set DATABASE_URL="mongodb+srv://user:pass@cluster.mongodb.net/marker_engine"
```

### Optional:
```bash
flyctl secrets set MOONSHOT_API_KEY="your_key"
flyctl secrets set OPENAI_API_KEY="your_key"
```

## 🌍 Nach dem Deployment

### URLs:
- App URL: `https://me-core-backend.fly.dev`
- Health Check: `https://me-core-backend.fly.dev/api/health/live`
- API Docs: `https://me-core-backend.fly.dev/docs`

### Monitoring:
```bash
# Logs anzeigen
flyctl logs

# Status checken
flyctl status

# Metriken
flyctl dashboard
```

## 💰 Kosten

### Fly.io Free Tier:
- 3 shared-cpu-1x VMs
- 3GB persistent storage
- 160GB outbound transfer

### MongoDB Atlas Free Tier:
- 512MB Storage
- Shared RAM
- Für Development/Testing ausreichend

**Gesamtkosten: $0/Monat** für Basic Setup! 🎉

## 🚨 Troubleshooting

### MongoDB Connection Error:
- Prüfe IP Whitelist in Atlas
- Prüfe Username/Password
- Connection String Format beachten

### Port Binding Error:
- Fly.io nutzt intern Port 8000
- Bereits in Dockerfile konfiguriert

### Memory Issues:
```bash
# Upgrade auf größere VM wenn nötig
flyctl scale vm shared-cpu-1x --memory 512
```

## 🚨 Troubleshooting

### App hat keine IP-Adresse / App not running

**Problem**: Extension zeigt "keine IP-Adresse" oder App ist gestoppt.

**Lösungen**:
```bash
# 1. Status prüfen
flyctl status

# 2. App starten falls gestoppt
flyctl machines start

# 3. Logs prüfen für Fehler
flyctl logs

# 4. Health Check testen
curl https://me-core-backend.fly.dev/api/health/live

# 5. Machine scaling prüfen
flyctl scale show

# 6. Falls nötig: Neu deployen
flyctl deploy
```

**Ursachen**:
- `min_machines_running = 0` kann dazu führen, dass alle Maschinen gestoppt werden
- Health Check Failures können Maschinen als unhealthy markieren
- Deployment-Fehler können die App stoppen

**Fix**: Die fly.toml wurde aktualisiert mit `min_machines_running = 1` um sicherzustellen, dass immer mindestens eine Maschine läuft.

## 🎯 Nächste Schritte

1. **MongoDB Atlas Account** erstellen
2. **Deploy Script** ausführen: `./deploy-to-fly.sh`
3. **Health Check** testen
4. **Logs** überwachen

Das wars! Dein Backend läuft auf Fly.io! 🚀