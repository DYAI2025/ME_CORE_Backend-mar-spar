# 🧹 Railway Service Cleanup Guide

## ⚠️ Problem: Zu viele Services im Railway Projekt

Railway zeigt noch alte Services an, die gelöscht werden müssen.

## 🗑️ Services die GELÖSCHT werden müssen:

1. **Mecore Spark** - LÖSCHEN
2. **Mecore E2E Test** - LÖSCHEN  
3. **Mecore Dashboard** - LÖSCHEN (vorerst)

## ✅ Services die BLEIBEN:

1. **Mecore Backend Production** - BEHALTEN
2. **MongoDB** - BEHALTEN
3. **Mecore Redis** - BEHALTEN (optional)

## 📋 Cleanup Anleitung:

### Option 1: Railway Dashboard (Empfohlen)

1. Gehe zu [railway.app/dashboard](https://railway.app/dashboard)
2. Wähle dein Projekt
3. Klicke auf jeden Service der gelöscht werden soll:
   - Mecore Spark → Settings → Delete Service
   - Mecore E2E Test → Settings → Delete Service
   - Mecore Dashboard → Settings → Delete Service

### Option 2: Railway CLI

```bash
# Liste alle Services
railway status

# Lösche Services einzeln
railway remove spark
railway remove e2e-test
railway remove dashboard
```

### Option 3: Kompletter Neustart (Nuclear Option)

```bash
# WARNUNG: Löscht ALLES!
railway delete

# Neu erstellen mit nur 3 Services
railway init --name me-core-backend-minimal
railway add mongodb
railway add redis
railway up
```

## 🎯 Finale Struktur (nur 3 Services):

```
Railway Project: me-core-backend
├── Backend Service (from GitHub)
├── MongoDB (Database Plugin)
└── Redis (Cache Plugin)
```

## ⚡ Wichtig nach dem Cleanup:

1. **Environment Variables prüfen:**
   ```bash
   railway variables
   ```

2. **Sicherstellen dass Backend läuft:**
   ```bash
   railway logs
   ```

3. **Health Check testen:**
   ```bash
   curl https://[your-app].up.railway.app/api/health/live
   ```

## 🚨 Falls immer noch mehr als 5 Services:

Prüfe ob du mehrere Railway Projekte hast:
```bash
railway list
```

Möglicherweise zählt Railway Services aus verschiedenen Projekten zusammen!