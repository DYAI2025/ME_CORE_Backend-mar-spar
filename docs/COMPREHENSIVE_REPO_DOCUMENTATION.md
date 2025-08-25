# MarkerEngine Core Monorepo – Comprehensive Documentation

## Overview

MarkerEngine Core is a monorepo combining a FastAPI backend, a Next.js frontend, and a Spark NLP service. It provides a multi-phase text analysis pipeline that detects semantic markers, enriches context with NLP, and generates human-readable interpretations via an LLM bridge. The repository also includes deployment configurations (Docker, Render, Railway, Fly.io), monitoring, and CI/CD scaffolding.

Primary components:
- Backend (FastAPI): API endpoints, orchestration pipeline, detection and scoring engines, data models, metrics, health checks
- Frontend (Next.js): UX for text input, schema selection, results visualization (risk gauge, marker chips, highlighting)
- Spark NLP: Optional enrichment for tokenization, tagging, and advanced NLP annotations
- Tools/Scripts/Monitoring: Schema sync utilities, deployment scripts, Prometheus config

---

## Repository Structure

Top-level directories and key files:
- `backend/` – FastAPI application and services
  - `api/` – API routers: analyze v1/v2, dashboard, markers, health, metrics
  - `services/` – Marker detection, orchestration (with and without DI), NLP abstraction, LLM bridge, health
  - `detect/` – Detector registry and detection modules (DETECT_*), fuzzy/aggregation engines
  - `calculate/` – Baseline calculators and time series aggregator
  - `schemata/` – JSON schemas for markers and analyses
  - `models/` – Pydantic models (e.g., `AnalysisContext`, `Marker`)
  - `core/` – Logging, DI container, interfaces, exceptions
  - `infrastructure/` – Metrics integration (Prometheus)
  - `repositories/` – Data repositories (e.g., `marker_repository.py`)
  - `main.py`, `minimal_app.py`, `config.py`, `database.py`
- `frontend/` – Next.js 14 app with Tailwind and shadcn/ui
  - `src/app/` – App Router pages (`page.tsx`, `analysis/page.tsx`)
  - `src/components/` – `input-card`, `result-display`, `risk-gauge`, `marker-highlight`, `marker-chip`
  - `src/types/` – Shared types for analysis requests/responses
  - `docs/`, `Dockerfile`, `tailwind.config.js`
- `spark-nlp/` – Spark NLP stubs and tests; optional enrichment service
- `tools/` – Utilities (e.g., `sync-schema-version.js`), schema detector JSON
- `scripts/` – Deployment validation scripts
- `monitoring/` – `prometheus.yml`
- `docs/` – Architecture and deployment docs; this file
- Deployment configs at repo root: Render, Railway, Fly.io, Docker Compose

---

## Backend Architecture

### Application startup
- `backend/main.py` initializes structured logging, loads `config.py` (`Settings` via Pydantic), initializes the DI container, and mounts routers.
- If configuration fails, falls back to `minimal_app.py` with health endpoints, avoiding a hard crash.
- CORS is enabled (wide-open by default; tighten for production).
- Middleware tracks active requests and latency via Prometheus metrics.

Key routers (mounted in `main.py`):
- `api/health.py` – Health endpoints
- `api/markers.py` – Marker CRUD (subset)
- `api/analyze.py` – Basic analysis with LLM interpretation
- `api/analyze_v2.py` – 3-phase analysis with orchestration + metrics + LLM
- `api/analyze_v2_di.py` – DI-based v2 (enhanced, parallel batch, cache hooks)
- `api/metrics.py` – Prometheus metrics (if enabled)
- `api/dashboard.py` – Stats, registry management, websocket live updates

### Configuration (`config.py`)
- Environment-driven settings with validation:
  - Database: `DATABASE_URL`, `MONGO_DB_NAME`
  - API: `API_HOST`, `API_PORT` (overridden by `PORT` in Railway)
  - NLP: `SPARK_NLP_ENABLED`
  - Cache: `CACHE_TYPE` (memory/redis), `REDIS_URL`, `CACHE_DEFAULT_TTL`
  - Monitoring: `ENABLE_METRICS`, `METRICS_PORT`
  - LLM: `KIMI_API_KEY` / `MOONSHOT_API_KEY`, `OPENAI_API_KEY`
  - Limits: `MAX_TEXT_LENGTH`, `REQUEST_TIMEOUT`
- `DETECTOR_PATH` is resolved to a writable resources directory; if missing, it is created.

### Data Layer (`database.py`, `repositories/`)
- MongoDB via Motor async client; global `db` is lazily initialized from `settings`.
- `repositories/marker_repository.py` and `services/marker_service.py` load marker documents for detection.
- Ensure the database is accessible or supply a mock/fixture for tests.

### Core Services

- Orchestration
  - `services/orchestration_service.py` – Three phases: initial scan, NLP enrichment, contextual rescan; returns markers + phase timings + metadata
  - `services/orchestration_service_di.py` – Adds DI, cache hooks, metrics, parallel batch processing; integrates `ICacheProvider`, `IMetricsCollector`

- Marker Detection
  - `services/marker_service.py` – Phase 1 loads A_/S_ markers, pattern/example matching; Phase 2 activates C_/MM_ markers via `ActivationRulesEngine` using `AnalysisContext`
  - `detect/DETECT_*` modules – Pattern models, fuzzy engine, chunking, scoring, logging configuration; `detector_registry.py` and JSON registry

- NLP Abstraction
  - `services/nlp_service.py` – Abstract base with `DummyNlpService` (always available) and `SparkNlpService` (bridges to `services/spark_nlp_service.py` if present). Adds tokens/sentences and NLP metadata to `AnalysisContext`.

- LLM Bridge
  - `services/llm_bridge.py` – Builds a domain-specific prompt from detected markers and calls Moonshot Kimi (primary) with GPT‑4 fallback; returns model used and processing time.

- Health & Metrics
  - `services/health_service.py` – Aggregated health checks
  - `infrastructure/metrics` – Prometheus counters/histograms used by middleware and orchestration

### Data Models
- `models/analysis_context.py` – In‑pipeline state container: input data, NLP enrichments (tokens, sentences, entities, dependencies), detected markers, metadata
- `models/marker.py` – Marker structure (frame, scoring, examples, activation rules, composed_of)

---

## API Surface

Base path: backend service root. Notable endpoints (actual prefixes per router include):

- Health
  - `GET /api/health/live`, `GET /api/health/ready`, `GET /api/health` – liveness/readiness/overall

- Analysis v1
  - `POST /analyze/` – Body: `{ text, schema_id? }` → markers, interpretation, counts, timing

- Analysis v2 (orchestrated)
  - `POST /analyze/v2/` – Body: `{ text, schema_id?, session_id?, enable_nlp?, enable_contextual? }` → full phase breakdown, `nlp_enriched`, metrics, interpretation
  - `POST /analyze/v2/batch` – Body: `[text, ...]` with optional `schema_id`, `session_id` → list of v2 responses
  - `GET /analyze/v2/status` – service readiness and configuration snapshot

- DI-based v2
  - `POST /analyze/v2-di/text` – Similar to v2 with cache hinting
  - `POST /analyze/v2-di/batch` – Parallel batch processing; returns `results` + `summary`
  - `GET /analyze/v2-di/status` – service status including cache stats (if provider supports it)
  - `DELETE /analyze/v2-di/cache` – clear cache (pattern-based clearing TODO)

- Markers
  - `POST /markers/` – Create a marker (subset)

- Dashboard
  - `GET /api/dashboard/overview` – aggregate counts, system metadata
  - `GET /api/dashboard/markers/stats` – marker distribution and recent updates
  - `WS /api/dashboard/ws` – live logs / status updates broadcast
  - `POST /api/dashboard/registry` – validate and persist detector registry

- Metrics
  - `GET /metrics` – Prometheus exposition (if enabled)

OpenAPI: FastAPI auto-generates docs at `/docs` and JSON at `/openapi.json` when the app is running.

---

## Analysis Pipeline – Component Interaction

End‑to‑end flow for a typical analysis request:

1) Frontend submits `AnalysisRequest` to Backend:
   - `POST /analyze/v2/` with `{ text, schema_id?, session_id? }`

2) Backend `orchestration_service` executes 3 phases:
   - Phase 1 (Initial scan): `MarkerService.initial_scan()` loads A_/S_ markers from MongoDB, runs example/pattern/signal matching, emits preliminary markers.
   - Phase 2 (NLP enrichment): `NlpService.enrich()` populates tokens/sentences/entities (dummy or Spark NLP), annotates `AnalysisContext`.
   - Phase 3 (Contextual rescan): `MarkerService.contextual_rescan()` evaluates composed markers (C_/MM_) using `ActivationRulesEngine`, detected components, and NLP metadata; merges results.

3) Scoring and interpretation:
   - Total score computed from marker scoring × confidence.
   - `llm_bridge.generate_interpretation()` builds a narrative interpretation using Kimi (with GPT‑4 fallback) if markers were found.

4) Metrics and response:
   - Prometheus metrics for latency, cache hits, NLP operations, active requests.
   - Response includes `markers`, `marker_count`, `total_score`, `phases{}`, `nlp_enriched`, `performance_metrics`, and `interpretation`.

5) Frontend presents results:
   - `result-display` renders risk gauge, marker chips, highlighted text, and interpretation.

Optional/related flows:
- Dashboard websocket broadcasts status/log messages to connected UI clients.
- Registry updates via `/api/dashboard/registry` persist new detector definitions after validation.

---

## Frontend Architecture

- Next.js 14 with App Router; Tailwind for styling; shadcn/ui components.
- Key components:
  - `InputCard` – text area with 4k character limit, schema selection, analyze/clear controls
  - `ResultDisplay` – aggregates `RiskGauge`, `MarkerChip` list, `MarkerHighlight`, and interpretation markdown
  - `hooks/use-toast` – toast messaging; `sonner` for notifications
- Types:
  - `AnalysisRequest`, `AnalysisResponse`, `DetectedMarker`, `AnalysisSchema` in `src/types`
- API integration:
  - Frontend imports `@/lib/api` (ensure `src/lib/api.ts` exists) to call backend endpoints based on `NEXT_PUBLIC_API_URL`.
- Real-time (optional):
  - Websocket support for live logs (documented in README; implement `useWebSocket` as needed).

---

## Spark NLP Service (Optional)

- `services/nlp_service.py` checks `SPARK_NLP_ENABLED` and attempts to load `SparkNlpServiceImpl` from `services/spark_nlp_service.py`.
- If not available, it gracefully falls back to dummy enrichment (tokens from whitespace split, single sentence).
- Full Spark NLP pipeline is intended to provide tokenization, POS tagging, NER, dependency parsing, and potential UDFs for marker detection.

---

## Monitoring & Health

- Health endpoints: `/api/health/live`, `/api/health/ready`, `/api/health`.
- Metrics endpoint: `/metrics` (Prometheus format) when `ENABLE_METRICS=true`.
- Middleware measures request durations and tracks active requests, recorded to `infrastructure.metrics`.
- `monitoring/prometheus.yml` provides a starting scraper configuration.

---

## Deployment

Supported targets and files:
- Docker Compose: `docker-compose.yml`, profiles for spark and monitoring; `docker-compose.test.yml` for integration tests
- Render: `backend/render.yaml`, root `render*.yaml`, `deploy-to-render.sh`, `RENDER_*` docs
- Railway: `railway*.json`, `deploy-to-railway.sh`, Railway docs and checklists
- Fly.io: `fly.toml`, `deploy-to-fly.sh`, `FLY_DEPLOYMENT_*` docs
- Nixpacks: `nixpacks.toml`
- Dockerfiles: `backend/Dockerfile`, `Dockerfile.optimized`, `Dockerfile.fly`; `frontend/Dockerfile`

Minimum runtime dependencies:
- Backend: Python 3.10+, FastAPI, Motor, Pydantic; MongoDB (unless running minimal app or mocks)
- Frontend: Node 18+
- Spark NLP: Java 11, pyspark and spark‑nlp when enabled

---

## Testing

- Backend: `pytest` (see `backend/pytest.ini`, `backend/tests`)
- Frontend: `npm test` (Jest/React Testing Library)
- E2E: `tests/e2e/` scaffolding
- Integration: `docker-compose.test.yml`

---

## Security

- CORS currently allows all origins; restrict in production.
- JWT authentication is planned in frontend docs; backend endpoints can be wrapped with auth dependencies.
- Rate limiting and request size enforcement should be enabled at the API gateway/reverse proxy and validated in the API (`MAX_TEXT_LENGTH`).
- Secrets are read from environment; avoid committing `.env`.

---

## Known Gaps and Recommendations (Improvements)

1) Unify Analyze API versions
- Merge `analyze_v2.py` and `analyze_v2_di.py`, keeping DI + caching + batch parallelization as standard. Expose one canonical path `/api/analyze/v2`.

2) Consistent import paths
- Some modules use `app.*` while others use relative imports. Normalize to a single package root (e.g., `app.*`) and ensure `backend/` is the package root in all deploy targets.

3) Database robustness
- `db` may be `None` during early init or tests. Guard access in `MarkerService` and add clear 503 errors when DB unavailable. Provide an in‑memory marker repository for dev/tests.

4) Production cache provider
- Implement `ICacheProvider` Redis adapter based on `REDIS_URL`; enable cache TTLs for common analysis keys (`analysis:{hash(text)}:{schema}`) and metrics for hit/miss.

5) Frontend API client
- Add `frontend/src/lib/api.ts` with typed wrappers for `/analyze/v2`, `/analyze/v2/batch`, `/api/dashboard/*`. Use `zod` for runtime validation if desired.

6) OpenAPI & typed clients
- Publish OpenAPI schema; generate typed clients for TS and Python. Integrate with frontend to reduce drift.

7) Observability
- Add OpenTelemetry tracing (FastAPI middleware, httpx instrumentation). Propagate `X-Request-ID` across services and logs.

8) Security hardening
- JWT auth middleware, role‑based access for dashboard endpoints, and rate limiting (e.g., `slowapi`). Tighten CORS to known origins.

9) Spark NLP integration
- Provide a reference `SparkNlpServiceImpl` and a docker‑compose profile including a Spark cluster. Add model download and warm‑up steps.

10) CI/CD
- Add GitHub Actions for backend/frontend test/build, docker build, and scanning. Validate `docs/openapi.yaml` on each change.

11) Data & Migrations
- Document marker schema migrations. Add MongoDB indices and a migration runner.

---

## Innovative Feature Proposal: Marker Graph Explorer with Active Learning

A rich, explainable analysis UI and feedback loop that evolves marker activation rules.

Problem
- Users need to understand why markers were triggered and how combinations lead to composed markers. They also want to refine detection quality over time.

Solution
- Build an interactive graph visualization of detected markers and their activation dependencies, with per‑edge explanations, NLP evidence, and confidence attributions.
- Add a feedback loop: users can confirm/reject markers and suggest corrections that are stored and influence future detections and scoring.

Core Capabilities
- Graph View: Nodes are markers (A_, S_, C_, MM_). Edges show `composed_of` and activation paths.
- Evidence Overlay: Click a node to see matched examples, regex hits, token spans, entities.
- Attribution: Display how each phase (initial, NLP, contextual) contributed to confidence.
- What‑If Mode: Toggle markers/NLP features to simulate activations and re‑score in real time.
- Feedback Capture: Per marker “confirm/reject” with optional notes.
- Learning Updates: Persist feedback and auto‑generate rule suggestions via LLM (e.g., new example phrases, pattern tweaks). Require human approval before applying.

Backend Changes
- Extend `AnalysisResponse` with provenance fields: `evidence`, `activation_rule`, `components`, `nlp_features_used`, `attribution`.
- Add `POST /markers/feedback` to persist feedback on a request/marker basis.
- New `services/rule_suggester.py`: uses `llm_bridge` to propose new examples/patterns or `activation` refinements based on aggregated feedback.
- Periodic job to produce a “proposed changes” registry; reviewed and merged via dashboard.

Frontend Changes
- New route `analysis/graph` with a graph library (e.g., `@xyflow/react` or Cytoscape.js) to render nodes/edges and overlays.
- Enhance `ResultDisplay` to link into the graph and display evidence.
- Feedback UI: buttons and forms attached to each marker; toasts and status banners.

Data & Governance
- Store feedback in MongoDB with user, time, text hash, marker id, decision, and notes.
- Dashboard section for proposed rule changes with diffs and approval workflow.

Milestones
- M1: Extend response with provenance; static graph rendering
- M2: Feedback capture + persistence; dashboard list
- M3: LLM‑generated suggestions; approval and registry merge flow
- M4: A/B validation and metrics (precision/recall proxy via feedback acceptance rates)

---

## Runbooks & Quick Reference

- Start locally: `docker-compose up` (backend+frontend). Add profiles for spark or monitoring as needed.
- Backend dev: `uvicorn main:app --reload` in `backend/`
- Frontend dev: `npm run dev` in `frontend/`
- Tests: `pytest` (backend), `npm test` (frontend)
- Health: `GET /api/health/*`
- Metrics: `GET /metrics`
- Config: `.env` for API keys, DB, cache, flags

---

## Appendix – Cross‑Component Contracts

- Frontend request type
  - `{ text: string; schema_id?: string; }`
- Backend v2 response (abridged)
  - `{ markers: Marker[], marker_count: number, total_score: number, phases: { ... }, nlp_enriched: boolean, performance_metrics: { ... }, interpretation?: string, model_used?: string }`
- Environment variables (selected)
  - `DATABASE_URL`, `MONGO_DB_NAME`, `API_HOST`, `API_PORT`, `SPARK_NLP_ENABLED`, `ENABLE_METRICS`, `KIMI_API_KEY`, `OPENAI_API_KEY`, `CACHE_TYPE`, `REDIS_URL`

This documentation complements `docs/ARCHITECTURE.md` and the root `README.md` and is intended as the single source for end‑to‑end understanding of the system and its evolution.