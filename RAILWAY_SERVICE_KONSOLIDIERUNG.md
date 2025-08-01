# 🚄 Railway Service Konsolidierung

## 🚨 Problem
Railway erlaubt maximal 5 Services pro Projekt. Aktuell haben wir:
1. Mecore Backend Production
2. Mecore Dashboard  
3. Mecore Spark
4. Mecore Redis
5. Mecore E2E Test
6. MongoDB (implizit als Database Service)

## ✅ Lösung: Service-Reduktion auf 5

### Finale Service-Struktur:
1. **Backend API** (Hauptservice)
2. **MongoDB** (Datenbank)
3. **Redis** (Cache - optional)
4. **Dashboard** (Frontend - optional)
5. **Frei für Zukunft**

### 🔄 Konsolidierungs-Maßnahmen:

#### 1. **E2E Tests entfernen** ✅
- **Warum:** Tests sollten nicht als permanenter Service laufen
- **Alternative:** 
  - GitHub Actions für CI/CD
  - Lokale Tests vor Deployment
  - Scheduled Jobs statt permanenter Service

#### 2. **Spark Service deaktivieren** ✅
- **Warum:** Nicht für Basis-Deployment notwendig
- **Alternative:**
  - Als separates Projekt deployen wenn benötigt
  - Oder in Backend integrieren mit `SPARK_NLP_ENABLED=false`
  - Später als eigenständiges Railway-Projekt

#### 3. **Dashboard optional machen** 💡
- Kann initial weggelassen werden
- Später hinzufügen wenn Slots frei

## 📋 Deployment-Strategie

### Phase 1: Minimale Konfiguration (3 Services)
```
1. Backend API
2. MongoDB  
3. Redis
```

### Phase 2: Mit Dashboard (4 Services)
```
1. Backend API
2. MongoDB
3. Redis  
4. Dashboard
```

### Phase 3: Vollständig (5 Services)
```
1. Backend API
2. MongoDB
3. Redis
4. Dashboard
5. Monitoring/Metrics Service
```

## 🛠️ Implementierung

### 1. Verwende `railway-consolidated.json`:
```bash
mv railway-consolidated.json railway.json
```

### 2. Deploy nur Backend + Datenbanken:
```bash
railway up
```

### 3. Services manuell hinzufügen:
```bash
# MongoDB
railway add mongodb

# Redis (optional)
railway add redis
```

## 📝 Angepasste Environment Variables

### Backend Service:
```env
DATABASE_URL=${{MongoDB.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
SPARK_NLP_ENABLED=false  # Spark deaktiviert
ENVIRONMENT=production
```

## 🚀 Deployment-Befehle

```bash
# Alten Railway-Projekt löschen (wenn nötig)
railway delete

# Neues Projekt mit weniger Services
railway init --name me-core-minimal
railway add mongodb
railway add redis
railway up
```

## ⚡ Alternativen für entfernte Services

### E2E Tests:
- GitHub Actions Workflow erstellen
- Playwright lokal ausführen
- Separates Test-Environment

### Spark NLP:
- Als Lambda/Serverless Function
- Separates Railway-Projekt
- On-Demand statt permanent

## 💡 Empfehlung

**Start mit 3 Services:**
1. Backend (Hauptanwendung)
2. MongoDB (Pflicht)
3. Redis (Cache)

**Später hinzufügen:**
- Dashboard (wenn UI benötigt)
- Monitoring (wenn Metriken wichtig)

Diese Konfiguration hält 2 Slots für zukünftige Erweiterungen frei!