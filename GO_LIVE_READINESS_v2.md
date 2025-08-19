# ME_CORE Backend – Go-Live Plan (v2)

## Event-/Change-Streams
- MongoDB Change Streams oder Queue (Celery/Kafka) beobachten neue Konversationen.
- Automatische Invalidierung/Reload von Markern und Detektoren.
- Live-Trigger der Analysejobs.
- Ergebnis: weniger manuelle Deploy-Rebuilds, konsistente Runtime-Caches.

## WebSocket-Event-Spec
```json
{
  "type": "marker_resonance",
  "conv": "<id>",
  "markers": [
    { "id": "SEM_*", "score": 1.23, "pos": [[s, e], ...] }
  ],
  "resonance": 3.9,
  "ts": "<iso8601>"
}
```
- Frontend kann damit deterministisch highlighten und die Gauge updaten.

## Robustheit & Retry
- Circuit-Breaker + Backoff für Detector- und LLM-Aufrufe.
- Fallback bei Ausfällen statt Request-Abbruch.
- Stabilere UX und höhere Zuverlässigkeit.

## Go-Live-Checkliste
- **DB-Seeding & Validierung** – Import-Skripte für Marker/Detektoren; Schema-Prüfung & versionierte Registry.
- **Response-Vertrag fixieren** – `/api/analyze_v2` liefert `markers[] {id, level, score, confidence, pos?}`, `resonance`, `logs`.
- **WebSocket-Endpoint** – Kanäle `logs` + `marker_resonance`; Session-IDs, Log-Level, Heartbeat.
- **Security** – JWT für API, Token-Gate für WS, Rate-Limit pro IP/User.
- **Caching** – Marker/Detector-Module im Prozess cachen; Cache-Bust via Change Stream.
- **NLP-Aktivierung** – Spark-NLP oder produktives NLP-Backend einschalten; Token/Offsets zurückgeben für exaktes Highlighting.
- **Scoring-Pfad** – Aggregat-Score („Resonanz“) berechnen und transportieren; Frontend-Gauge anbinden.
- **Tests grün kriegen** – fehlende Pakete nachziehen (z. B. sqlalchemy), CI-Matrix bauen (unit/integration/load/security).
- **Observability** – Prometheus-Metriken (Latenz, Fehlerquote, LLM-Quota), strukturierte Logs, Alerts.
- **Deploy-Konfig** – Env-Variablen (LLM-Keys, DETECTOR_PATH, Mongo-URL) dokumentieren, Secrets trennen, Smoke-Test-Route.
