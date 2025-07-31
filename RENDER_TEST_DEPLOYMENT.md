# Render Test Deployment (ohne MongoDB)

## Übersicht
Diese Anleitung erklärt, wie du ME_CORE_Backend auf Render **ohne MongoDB** deployen kannst, um die API zu testen.

## Was funktioniert im Test-Modus?

### ✅ Funktioniert:
- **Health-Check Endpoints**: `/healthz`, `/api/health/live`, `/api/health/ready`
- **Mock Marker API**: 
  - `GET /markers/` - Liefert 5 vordefinierte Test-Marker
  - `GET /markers/{id}` - Einzelner Marker
  - `GET /markers/search?query=...` - Suche in Mock-Daten
- **Text-Analyse (Mock)**: 
  - `POST /analyze/` - Analysiert Text mit Mock-Markern
- **Monitoring Dashboard**: Zeigt API-Status und Mock-Daten
- **Metrics**: Prometheus-Metriken auf `/metrics`

### ❌ Eingeschränkt:
- Keine echte Datenpersistenz (alles in-memory)
- Keine benutzerdefinierten Marker
- Keine MongoDB-spezifischen Features

## Deployment-Schritte

### 1. Render Blueprint verwenden

1. Gehe zu [Render Dashboard](https://dashboard.render.com)
2. Klicke auf **New** → **Blueprint**
3. Wähle dein GitHub Repository: `DYAI2025/ME_CORE_Backend-mar-spar`
4. Nutze die Datei: `render-test.yaml`
5. Klicke **Apply**

### 2. Services werden erstellt

Render erstellt automatisch:
- `me-core-backend-test` - Backend API im Mock-Modus
- `me-core-dashboard-test` - Monitoring Dashboard

### 3. Warte auf Deployment (5-10 Minuten)

Die Services werden gebaut und gestartet. Du siehst den Status im Dashboard.

## Test-URLs

Nach erfolgreichem Deployment:

- **Backend API**: `https://me-core-backend-test.onrender.com`
- **Dashboard**: `https://me-core-dashboard-test.onrender.com`

## API testen

### Health Check:
```bash
curl https://me-core-backend-test.onrender.com/healthz
```

Erwartete Antwort:
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2025-07-31T20:00:00Z",
  "details": {
    "mode": "mock",
    "message": "Running without MongoDB - using mock service"
  }
}
```

### Mock Markers abrufen:
```bash
curl https://me-core-backend-test.onrender.com/markers/
```

### Text analysieren:
```bash
curl -X POST https://me-core-backend-test.onrender.com/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"text": "IF condition THEN action WITH parameters"}'
```

## Mock-Daten

Der Mock-Service enthält 5 vordefinierte Marker:
- **IF** - Conditional statement
- **THEN** - Action marker
- **WITH** - Context marker
- **FOR** - Loop marker
- **AND** - Logical conjunction

## Nächste Schritte

1. **API testen**: Verwende die Test-URLs um die API-Funktionalität zu prüfen
2. **Dashboard erkunden**: Schaue dir das Monitoring Dashboard an
3. **MongoDB hinzufügen**: Wenn Tests erfolgreich, MongoDB Atlas einrichten
4. **Production Deploy**: Mit `render.yaml` und echten MongoDB-Credentials

## Kosten

Mit dem `starter` Plan (free tier):
- Kostenlos für Test-Zwecke
- Services schlafen nach 15 Min Inaktivität
- Perfekt für Tests und Entwicklung

## Troubleshooting

### Service startet nicht?
- Check die Logs im Render Dashboard
- Stelle sicher, dass der `main` Branch aktuell ist

### API antwortet nicht?
- Warte bis Service vollständig gestartet ist (grüner Status)
- Services im Free Tier brauchen ~30s zum Aufwachen

### Dashboard zeigt keine Daten?
- API muss zuerst gestartet sein
- Refresh die Seite nach API-Start