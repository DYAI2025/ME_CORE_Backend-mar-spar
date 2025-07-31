# ME_CORE_Backend-mar-spar

**MarkerEngine Core Backend Monorepo** - Ein schlankes Monorepo für Backend-, Spark- und Frontend-Komponenten mit einheitlichem Release- und Testprozess.

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