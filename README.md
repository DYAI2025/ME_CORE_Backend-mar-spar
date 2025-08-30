# ME_CORE_Backend-mar-spar

**MarkerEngine Core Backend Monorepo** – Dieses Repository bündelt sämtliche Kernkomponenten der MarkerEngine.
Es vereint den Python/FastAPI‑Backend‑Dienst, ein Next.js/Node.js‑Frontend sowie eine Spark‑NLP‑Anbindung
für skalierbare Sprachverarbeitung. Das Monorepo stellt einen einheitlichen Build‑, Test‑ und
Deployment‑Prozess bereit und dient als zentrale Codebasis für das Gesamtsystem.

## 🧠 Wofür ist dieses Repository gedacht?

Die MarkerEngine übersetzt natürliche Sprache in strukturierte *Marker* und bietet damit die Grundlage für
intelligente Analysen. Dieses Repo enthält:

- **Backend** – FastAPI‑Service mit modularer Architektur (API‑Router, Service‑Layer, Repositories und Infrastruktur).
- **Frontend** – Next.js‑Dashboard zur Steuerung und Visualisierung der Analyse.
- **Spark‑NLP** – Python‑Module für rechenintensive NLP‑Jobs auf Apache Spark.

Alle Teile sind so aufgebaut, dass sie getrennt entwickelt werden können, aber nahtlos zusammenarbeiten.

## 🏗️ Monorepo-Struktur

```
/ME_CORE_Backend-mar-spar/
│
├─ .github/                # GitHub Actions / Issue-Vorlagen
├─ jenkins/                # Jenkins-Pipeline-Definitions
├─ docs/                   # Architektur-, API- und Deploy-Dokumentation
├─ tools/                  # Hilfsskripte (z.B. Schema-Generator)
│
├─ backend/                # Aus _1-_MEWT-backend
│   ├─ api/                # FastAPI-Router für Analyse & Schemas
│   ├─ detect/             # Detector-Registry & Module
│   ├─ scoring/            # Score-Engine & Profile
│   ├─ calculate/          # Baseline-Calculator
│   ├─ markers/            # Marker-Definitionen (yaml + json)
│   └─ schemata/           # JSON-Schemas (v2.1 + enhanced master)
│
├─ spark-nlp/              # Aus markerengine-spark-nlp
│   ├─ src/                # Spark-Jobs, UDF-Registrierung
│   ├─ docker/             # Docker-Definitionen
│   └─ tests/              # Integrationstests für Spark-Pipeline
│
└─ frontend/               # Aus markerengine_frontend
    ├─ src/                # Next.js-App
    ├─ public/             # Statische Assets
    └─ tests/              # UI- und API-Stubs-Tests
```

## 🧩 Funktionsüberblick

- **API & Services**: FastAPI-Router im Verzeichnis `backend/api/` liefern Endpunkte zur
  Analyse von Texten, zur Verwaltung von Markern und zum Monitoring. Die zugehörigen
  Services kapseln Geschäftslogik und greifen über Repositories auf MongoDB oder
  andere Infrastrukturkomponenten zu.
- **Frontend**: Das Next.js-Dashboard unter `frontend/` kommuniziert über die REST‑API
  mit dem Backend und bietet eine Benutzeroberfläche für Konfiguration und Monitoring.
- **Spark‑NLP**: Der Ordner `spark-nlp/` enthält verteilte NLP‑Jobs (z. B. Marker‑Erkennung),
  die bei Bedarf separat oder im Docker‑Verbund gestartet werden können.
- **End-to-End-Tests**: Unter `tests/e2e` liegt eine Playwright‑basierte Testumgebung, die
  Backend und Frontend gemeinsam in Docker startet.

## 🚀 Quick Start

### Voraussetzungen

- Python 3.10+
- Node.js 18+
- Java 11 (für Spark NLP)
- Docker & Docker Compose
- MongoDB

### Installation

```bash
# Repository klonen
git clone https://github.com/DYAI2025/ME_CORE_Backend-mar-spar.git
cd ME_CORE_Backend-mar-spar

# Backend-Dependencies installieren
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend-Dependencies installieren
cd ../frontend
npm install

# Spark NLP Setup
cd ../spark-nlp
pip install -r requirements-spark.txt
```

### Entwicklungsumgebung starten

```bash
# Mit Docker Compose (empfohlen)
docker-compose up

# Oder manuell:
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Spark (optional)
cd spark-nlp && spark-submit src/main.py
```

## 🔧 Technische Schnittstellen

### REST API Endpoints

- `GET /api/schemas` - Alle Schemas abrufen
- `GET /api/schemas/{schema_id}` - Einzelnes Schema
- `POST /api/schemas` - Neues Schema erstellen
- `POST /api/analyze` - Text analysieren
- `GET /api/health` - Health Check

### Spark UDFs

```python
# In spark-nlp/src/udfs.py definiert:
detect_markers(text: String) -> Array[String]
score_markers(markers: Array[String]) -> Double
```

### Shared Types

TypeScript-Interfaces und Python-Modelle werden in `backend/src/shared/` und `frontend/src/shared/` geteilt.

## 🏭 CI/CD mit Jenkins

Jenkins-Pipelines unter `jenkins/`:

- `build-backend` - Backend Tests & Validation
- `build-spark` - Spark Integration Tests
- `build-frontend` - Frontend Build & Tests
- `deploy-staging` - Staging Deployment
- `deploy-production` - Production Deployment

### Pipeline-Status

Dashboard: [Jenkins Blue Ocean](http://jenkins.example.com/blue)

## 📊 Monitoring

- Health Check: `GET /api/health`
- Prometheus Metrics: `GET /api/metrics`
- Logging: Strukturierte JSON-Logs in `logs/`

## 🧪 Testing

```bash
# Backend Tests
cd backend && pytest

# Frontend Tests
cd frontend && npm test

# Spark Tests
cd spark-nlp && pytest tests/

# End-to-End Tests
npm run test:e2e
```

## 🚨 Troubleshooting

### Fly.io Deployment Issues

**Problem**: App läuft nicht / keine IP-Adresse

**Schnelle Lösung**:
```bash
# Automatischer Fix-Script
./fix-fly-deployment.sh

# Oder manuell:
flyctl status                    # Status prüfen
flyctl machines start           # Maschinen starten
flyctl scale count 1           # Mindestens 1 Maschine
flyctl deploy                   # Neu deployen falls nötig
```

**Weitere Deployment Guides**:
- [Fly.io Deployment Guide](FLY_DEPLOYMENT_GUIDE.md)
- [Deployment Fixes](FLY_DEPLOYMENT_FIXES.md)
- [Reliability Report](backend/DEPLOYMENT_RELIABILITY_REPORT.md)

## 📚 Dokumentation

- [Architektur-Übersicht](docs/ARCHITECTURE.md)
- [API Dokumentation](docs/openapi.yaml)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Entwickler-Handbuch](docs/DEVELOPER.md)

## 🔄 Release-Prozess

1. Feature-Branch erstellen: `feature/JIRA-123-description`
2. Code entwickeln und testen
3. Pull Request erstellen
4. Code Review & CI-Checks
5. Merge in `develop`
6. Release-Branch: `release/v1.0.0`
7. Deploy to Staging
8. Tests & Approval
9. Merge in `main` & Tag
10. Production Deploy

## 🤝 Contributing

1. Fork das Repository
2. Feature-Branch erstellen
3. Änderungen committen
4. Tests schreiben/anpassen
5. Pull Request öffnen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 👥 Team

- **Product Owner**: Chief Product Owner
- **Entwicklung**: Claude-Flow Team
- **DevOps**: Jenkins Integration Team

---

**Hinweis**: Dies ist ein Monorepo. Alle Komponenten müssen zusammen releast werden.