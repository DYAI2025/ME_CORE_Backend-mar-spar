# DevOps Dashboard Setup Guide

## Übersicht

Das neue DevOps Dashboard bietet eine umfassende Übersicht über Jenkins-Projekte, CI-Pipelines, Commit-Metriken und Repository-Stabilität. Es integriert GitHub Actions, Jenkins und automatische Tests in einer zentralen Benutzeroberfläche.

## Features

### 🚀 CI/CD Overview Dashboard
- **Jenkins Integration**: Status von Jenkins-Servern, Build-Queue und aktuelle Builds
- **GitHub Actions**: Workflow-Status, Erfolgsraten und Build-Historie  
- **Repository Health Score**: Automatische Bewertung der Repository-Gesundheit
- **Test Results**: Übersicht über Unit-, Integration- und E2E-Tests
- **Real-time Updates**: WebSocket-basierte Live-Updates

### 📊 GitHub Metrics Dashboard
- **Repository Statistics**: Stars, Forks, Issues und Activity
- **Commit Activity**: Visualisierung der Entwicklungsaktivität
- **Pull Request Tracking**: Status und Historie von Pull Requests
- **Workflow Analytics**: Detaillierte GitHub Actions Metriken
- **Issue Management**: Offene Issues und Labels

### 🔧 Quick Actions
- **Deployment Triggers**: Direkte Auslösung von Deployments (Staging/Production)
- **Test Execution**: Manuelle Auslösung von E2E-Tests
- **Jenkins Jobs**: Triggern von Jenkins-Builds

## Installation und Setup

### 1. Abhängigkeiten installieren

```bash
cd dashboard
npm install
```

### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env.local` Datei im `dashboard` Verzeichnis:

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# GitHub API (optional, für erweiterte Funktionen)
NEXT_PUBLIC_GITHUB_TOKEN=your_github_token_here
GITHUB_TOKEN=your_github_token_here

# Repository Konfiguration
NEXT_PUBLIC_GITHUB_OWNER=DYAI2025
NEXT_PUBLIC_GITHUB_REPO=ME_CORE_Backend-mar-spar
```

### 3. Backend API Endpoints

Das Dashboard benötigt die folgenden Backend-Endpoints (bereits implementiert):

```
GET  /api/dashboard/overview           # Dashboard Übersicht
GET  /api/dashboard/jenkins/status     # Jenkins Status
GET  /api/dashboard/markers/stats      # Marker Statistiken
GET  /api/dashboard/activities         # Aktivitäts-Log
GET  /api/dashboard/metrics           # System Metriken
GET  /api/dashboard/tests/results     # Test Ergebnisse
POST /api/dashboard/deploy/{env}      # Deployment auslösen
POST /api/dashboard/tests/e2e/trigger # E2E Tests starten
WS   /api/dashboard/ws                # WebSocket Updates
```

### 4. Dashboard starten

```bash
# Entwicklungsmodus
npm run dev

# Production Build
npm run build
npm start
```

Das Dashboard ist dann unter `http://localhost:3001` verfügbar.

## Integration Options

### Option 1: GitHub Integration (Empfohlen)
- Direkte GitHub API Nutzung für Repository-Metriken
- Automatische Workflow-Status Updates
- Commit und Pull Request Tracking

**Setup:**
1. GitHub Token erstellen (Settings > Developer settings > Personal access tokens)
2. Token in Umgebungsvariablen setzen
3. Repository Owner/Name konfigurieren

### Option 2: Jenkins Integration
- Live Jenkins Server Status
- Build Queue und Executor Monitoring
- Job Triggering über Dashboard

**Setup:**
1. Jenkins API URL konfigurieren
2. Jenkins API Token einrichten
3. Backend Jenkins Client konfigurieren

### Option 3: Render Server Integration
- Als Alternative zu lokaler Installation
- Dashboard auf Render Server deployen
- Umgebungsvariablen in Render konfigurieren

## Monitoring und Grafana Integration

Das System ist bereits für Integration mit Grafana/Prometheus vorbereitet:

```bash
# Monitoring Stack starten
docker-compose --profile monitoring up -d

# Grafana Dashboard: http://localhost:3001
# Prometheus Metrics: http://localhost:9090
```

## Verwendung

### 1. Hauptdashboard
- Übersicht über System-Gesundheit
- Schnellzugriff auf CI/CD Dashboard
- Jenkins Status im Überblick

### 2. CI/CD Dashboard
- **Tab 1 - CI/CD Overview**: Kombinierte Ansicht aller CI/CD Systeme
- **Tab 2 - GitHub Metrics**: Detaillierte GitHub Repository Analysen

### 3. Repository Health Score
Der Health Score wird automatisch basierend auf folgenden Faktoren berechnet:
- **CI Status (30%)**: Erfolgsrate der letzten Builds
- **Test Coverage (25%)**: Testabdeckung und Erfolgsrate
- **Commit Frequency (20%)**: Entwicklungsaktivität
- **Code Quality (15%)**: Code-Qualitäts-Metriken
- **Maintenance (10%)**: Issue Management

## Konfiguration für verschiedene Repositories

```typescript
// In src/app/ci/page.tsx anpassen
<CIDashboard owner="DYAI2025" repo="ME_CORE_Backend-mar-spar" />
<GitHubMetrics owner="DYAI2025" repo="ME_CORE_Backend-mar-spar" />
```

## Troubleshooting

### Häufige Probleme

1. **"Failed to load dashboard data"**
   - Backend API Server läuft nicht
   - Lösung: `cd backend && uvicorn main:app --reload`

2. **"Failed to fetch GitHub data"**
   - GitHub Token fehlt oder ungültig
   - Rate Limiting erreicht
   - Lösung: GitHub Token konfigurieren

3. **"Jenkins API not available"**
   - Jenkins Server nicht erreichbar
   - Das System funktioniert mit Mock-Daten als Fallback

### Performance Optimierung

- GitHub API Rate Limiting: Caching implementiert (5min für Repository-Daten)
- WebSocket Reconnection: Automatisch bei Verbindungsabbruch
- Error Boundaries: Graceful Fallbacks bei API-Fehlern

## Erweiterte Features

### Custom Dashboards
Das System unterstützt die Erweiterung um custom Dashboards:

```typescript
// Neues Dashboard in src/app/custom/page.tsx
import { CustomMetrics } from '@/components/CustomMetrics'

export default function CustomPage() {
  return <CustomMetrics />
}
```

### API Erweiterungen
Neue Backend-Endpoints können einfach hinzugefügt werden:

```python
# In backend/api/dashboard.py
@router.get("/custom/metrics")
async def get_custom_metrics():
    return {"custom": "data"}
```

### Webhook Integration
Für Real-time Updates können Webhooks konfiguriert werden:
- GitHub Webhooks für Push/PR Events
- Jenkins Webhooks für Build Status
- Custom Webhooks für externe Systeme

## Security Considerations

- GitHub Tokens sicher speichern (nie in Code committen)
- Backend API Authentication implementieren
- CORS richtig konfigurieren für Production
- Rate Limiting für API Calls einrichten

## Deployment

### Docker Deployment
```bash
# Dashboard mit Docker starten
docker-compose up dashboard

# Mit Monitoring
docker-compose --profile monitoring up
```

### Environment-spezifische Konfiguration
- Development: Live-Reload, Debug-Modus
- Staging: Production Build, Test-Daten
- Production: Optimierte Builds, echte APIs

## Support und Wartung

- **Logs**: Dashboard Logs in Browser DevTools
- **Monitoring**: Prometheus Metriken verfügbar
- **Updates**: Automatische Abhängigkeits-Updates via npm
- **Backup**: Repository-Konfiguration in Git versioniert

Das Dashboard ist vollständig funktionsfähig und bereit für den produktiven Einsatz!