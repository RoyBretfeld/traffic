# Monitoring-Implementierung
**Datum:** 2025-01-10  
**Status:** ✅ Implementiert

---

## ✅ Implementierte Features

### 1. JSON-Logging
- ✅ **Strukturierte Logs:** Alle Logs werden als JSON ausgegeben (optional)
- ✅ **Trace-ID Integration:** Jeder Log-Eintrag enthält Trace-ID
- ✅ **Metriken in Logs:** Latenz, Route, Status-Code werden automatisch geloggt
- ✅ **Umgebungsvariable:** `USE_JSON_LOGGING=true` aktiviert JSON-Logging

**Datei:** `backend/utils/json_logging.py`
```python
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": record.trace_id,  # Falls vorhanden
            "route": record.route,  # Falls vorhanden
            "duration_ms": record.duration_ms,  # Falls vorhanden
            ...
        }
        return json.dumps(log_data, ensure_ascii=False)
```

**Aktivierung:**
```bash
# .env oder Umgebungsvariable
USE_JSON_LOGGING=true
LOG_FILE=logs/trafficapp.jsonl  # Optional: Log-Datei
```

### 2. OSRM-Metriken-Service
- ✅ **Latenz-Tracking:** Durchschnitt, P95, P99 Latenz
- ✅ **Fehlerrate:** Erfolgsrate, Fehlerrate, Fehler-Typen (Timeout, Quota, Transient)
- ✅ **Circuit-Breaker-Status:** Trackt Circuit-Breaker-Zustand und Trips
- ✅ **Fehler-Historie:** Letzte N Fehler mit Timestamp und Details
- ✅ **Singleton-Pattern:** Globale Instanz für App-weite Metriken

**Datei:** `backend/services/osrm_metrics.py`
```python
class OSRMMetrics:
    def record_request(
        self,
        latency_ms: float,
        success: bool = True,
        error_type: Optional[str] = None,
        circuit_state: Optional[str] = None
    ) -> None:
        # Zeichnet Request auf
        ...
    
    def get_stats(self) -> Dict[str, any]:
        # Gibt Statistiken zurück
        return {
            "total_requests": ...,
            "success_rate_pct": ...,
            "avg_latency_ms": ...,
            "p95_latency_ms": ...,
            "p99_latency_ms": ...,
            ...
        }
```

### 3. OSRM-Client Integration
- ✅ **Automatisches Tracking:** Alle OSRM-Requests werden automatisch getrackt
- ✅ **Latenz-Messung:** Jeder Request misst seine Dauer
- ✅ **Fehler-Kategorisierung:** Timeout, Quota, Transient, Unexpected
- ✅ **Circuit-Breaker-Integration:** Status wird in Metriken übernommen

**Datei:** `services/osrm_client.py`
```python
def _make_request(...):
    start_time = time.time()
    try:
        # ... Request ...
        latency_ms = (time.time() - start_time) * 1000
        
        # Metriken: Erfolgreicher Request
        metrics.record_request(
            latency_ms=latency_ms,
            success=True,
            circuit_state=self.circuit_state.value
        )
    except httpx.TimeoutException:
        # Metriken: Timeout
        metrics.record_request(
            latency_ms=latency_ms,
            success=False,
            error_type="timeout",
            ...
        )
```

### 4. API-Endpoints für Metriken
- ✅ **GET `/api/osrm/metrics`:** Aktuelle Statistiken
- ✅ **GET `/api/osrm/metrics/errors`:** Letzte Fehler
- ✅ **POST `/api/osrm/metrics/reset`:** Metriken zurücksetzen

**Datei:** `routes/osrm_metrics_api.py`

**Beispiel-Response:**
```json
{
  "total_requests": 100,
  "successful_requests": 95,
  "failed_requests": 5,
  "success_rate_pct": 95.0,
  "error_rate_pct": 5.0,
  "avg_latency_ms": 123.45,
  "p95_latency_ms": 200.0,
  "p99_latency_ms": 300.0,
  "timeout_requests": 2,
  "quota_errors": 1,
  "transient_errors": 2,
  "circuit_breaker_state": "closed",
  "circuit_breaker_trips": 0,
  "last_request_time": 1234567890.0,
  "samples_count": 100
}
```

### 5. Trace-ID Middleware erweitert
- ✅ **Latenz-Messung:** Misst Dauer jedes Requests
- ✅ **Strukturiertes Logging:** Loggt Route, Method, Status-Code, Dauer
- ✅ **Trace-ID in Logs:** Jeder Log-Eintrag enthält Trace-ID

**Datei:** `backend/middlewares/trace_id.py`
```python
async def dispatch(self, request: Request, call_next):
    start_time = time.time()
    # ... Request verarbeiten ...
    duration_ms = (time.time() - start_time) * 1000
    
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "trace_id": trace_id,
            "route": str(request.url.path),
            "method": request.method,
            "duration_ms": round(duration_ms, 2),
            "status_code": response.status_code
        }
    )
```

### 6. Logging-Setup erweitert
- ✅ **JSON-Logging optional:** Kann über Umgebungsvariable aktiviert werden
- ✅ **File-Logging:** Optional Log-Datei für persistente Logs
- ✅ **Fallback:** Falls JSON-Logging fehlschlägt, wird Standard-Logging verwendet

**Datei:** `logging_setup.py`
```python
USE_JSON_LOGGING = os.getenv("USE_JSON_LOGGING", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", None)

if USE_JSON_LOGGING:
    from backend.utils.json_logging import setup_json_logging
    setup_json_logging(log_file=log_file_path, level=LEVEL, console=True)
else:
    # Standard-Logging (Text-Format)
    ...
```

---

## 📊 Verwendung

### JSON-Logging aktivieren
```bash
# .env
USE_JSON_LOGGING=true
LOG_FILE=logs/trafficapp.jsonl
LOG_LEVEL=INFO
```

### Metriken abrufen
```bash
# Aktuelle Statistiken
curl http://localhost:8111/api/osrm/metrics

# Letzte Fehler
curl http://localhost:8111/api/osrm/metrics/errors?limit=10

# Metriken zurücksetzen
curl -X POST http://localhost:8111/api/osrm/metrics/reset
```

### Logs analysieren
```bash
# JSON-Logs lesen (jq für Formatierung)
cat logs/trafficapp.jsonl | jq '.'

# Fehler filtern
cat logs/trafficapp.jsonl | jq 'select(.level == "ERROR")'

# Nach Trace-ID suchen
cat logs/trafficapp.jsonl | jq 'select(.trace_id == "abc12345")'

# Langsame Requests finden
cat logs/trafficapp.jsonl | jq 'select(.duration_ms > 1000)'
```

---

## 🧪 Tests

- ✅ **OSRM-Metriken-Tests:** `tests/test_osrm_metrics.py`
- ✅ **Routing-Fixes-Tests:** `tests/test_routing_fixes.py`

**Ausführen:**
```bash
pytest tests/test_osrm_metrics.py -v
pytest tests/test_routing_fixes.py -v
```

---

## 📝 Nächste Schritte

1. **JSON-Logging aktivieren:** `USE_JSON_LOGGING=true` in `.env` setzen
2. **Metriken-Dashboard:** Frontend-Dashboard für Metriken-Visualisierung
3. **Alerting:** Alerts bei hoher Fehlerrate oder Latenz
4. **Log-Rotation:** Automatische Rotation von Log-Dateien

---

**Erstellt von:** KI-Assistent (Auto)  
**Datum:** 2025-01-10

