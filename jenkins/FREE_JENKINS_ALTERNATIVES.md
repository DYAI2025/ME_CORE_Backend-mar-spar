# Kostenlose Jenkins Alternativen für ME_CORE Backend

## 🆓 Option 1: Jenkins Lokal (Komplett Kostenlos!)

### Docker auf deinem Rechner:
```bash
# Jenkins kostenlos lokal starten
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts

# Initial-Passwort abrufen
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

**Vorteile:**
- ✅ 100% kostenlos
- ✅ Volle Kontrolle
- ✅ Funktioniert sofort mit deinem Dashboard
- ✅ Keine Limits

**Nachteile:**
- ❌ Läuft nur wenn dein Rechner an ist
- ❌ Kein externer Zugriff

## 🐙 Option 2: GitHub Actions (Kostenlos für Public Repos)

### Kostenlose Limits:
- **Public Repos**: Unbegrenzt kostenlos!
- **Private Repos**: 2,000 Minuten/Monat kostenlos

### Beispiel `.github/workflows/ci.yml`:
```yaml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
```

### Dashboard Anpassung für GitHub Actions:
```python
# backend/app/routers/github_actions.py
@router.get("/api/github/actions")
async def get_github_actions_status():
    # GitHub API für Workflow-Runs
    response = await client.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions/runs",
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )
    return response.json()
```

## 🚀 Option 3: Render's Build Hooks (Bereits dabei!)

Render hat CI/CD bereits integriert:
- **Automatische Builds** bei jedem Push
- **Kostenlos** im Free Tier
- **Webhook URLs** für Status

### Dashboard Integration:
```javascript
// Render Build Status abrufen
const response = await fetch('/api/render/deploys');
```

## 🦊 Option 4: GitLab CI (Kostenlos)

### Kostenlose Limits:
- 400 CI/CD Minuten/Monat
- Unbegrenzt für public projects

### `.gitlab-ci.yml`:
```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - cd backend && pytest
```

## 📊 Kostenvergleich:

| Service | Kostenlos | Limits | Dashboard-Support |
|---------|-----------|--------|-------------------|
| Jenkins Lokal | ✅ Unbegrenzt | Nur lokal | ✅ Vollständig |
| GitHub Actions | ✅ 2000 Min/Monat | Private Repos | 🔧 Anpassbar |
| Render CI/CD | ✅ Inklusive | Free Tier Limits | 🔧 Anpassbar |
| GitLab CI | ✅ 400 Min/Monat | Private Repos | 🔧 Anpassbar |
| Bitbucket | ✅ 50 Min/Monat | Sehr begrenzt | 🔧 Anpassbar |

## 🎯 Empfehlung für Testen:

### 1. **Sofort starten: Jenkins Lokal mit Docker**
```bash
# In 2 Minuten bereit:
docker run -d -p 8080:8080 jenkins/jenkins:lts
```
- Dashboard funktioniert sofort
- Keine Kosten
- Perfekt zum Entwickeln

### 2. **Für Deployment: Nutze Render's eingebautes CI/CD**
- Schon in deinem `render.yaml` konfiguriert
- Automatische Builds
- Deployment Hooks verfügbar

### 3. **Langfristig: GitHub Actions**
- Wenn Repository public → komplett kostenlos
- Sehr gute Integration
- Modern und zukunftssicher

## 🔧 Mock Jenkins API für Development

Für reines Dashboard-Testing ohne echten Jenkins:

```python
# backend/app/routers/mock_jenkins.py
from fastapi import APIRouter
from datetime import datetime
import random

router = APIRouter(prefix="/jenkins", tags=["jenkins"])

@router.get("/api/json")
async def mock_jenkins_status():
    return {
        "mode": "NORMAL",
        "nodeDescription": "Mock Jenkins",
        "numExecutors": 2,
        "jobs": [
            {
                "name": "ME_CORE_Backend",
                "color": random.choice(["blue", "red", "yellow"]),
                "lastBuild": {
                    "number": random.randint(1, 100),
                    "result": random.choice(["SUCCESS", "FAILURE", "UNSTABLE"]),
                    "timestamp": datetime.now().timestamp() * 1000
                }
            }
        ],
        "quietingDown": False
    }

@router.get("/view/all/api/json")
async def mock_jenkins_jobs():
    return {
        "jobs": [
            {
                "name": f"test-job-{i}",
                "lastBuild": {
                    "result": random.choice(["SUCCESS", "FAILURE"]),
                    "displayName": f"#{random.randint(1, 50)}",
                    "timestamp": datetime.now().timestamp() * 1000
                }
            }
            for i in range(5)
        ]
    }
```

## 📝 Nächste Schritte:

1. **Für sofortiges Testen**: Starte Jenkins lokal mit Docker
2. **Für Production**: Nutze GitHub Actions (kostenlos für public repos)
3. **Für Deployment**: Render's CI/CD ist bereits inklusive

Keine 67€/Monat nötig! 🎉