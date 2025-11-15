# HTTP Statuscode-Policy

**Ziel:** Konsistente Fehlerbehandlung mit korrekten HTTP-Status-Codes.

---

## Statuscode-Mapping

### Client-Fehler (4xx)

| Code | Verwendung | Beispiel |
|------|------------|----------|
| **400** | Bad Request - Ungültige Anfrage | Fehlende Parameter, ungültiges Format |
| **422** | Unprocessable Entity - Validierungsfehler | Pydantic-Validierung fehlgeschlagen |
| **404** | Not Found - Ressource nicht gefunden | Datei/Route nicht vorhanden |
| **429** | Too Many Requests - Rate-Limit | OSRM Quota überschritten |

### Server-Fehler (5xx)

| Code | Verwendung | Beispiel |
|------|------------|----------|
| **500** | Internal Server Error - Uncaught Exception | Unerwarteter Fehler, mit Trace-ID |
| **503** | Service Unavailable - Externer Service nicht verfügbar | OSRM nicht erreichbar, Timeout |
| **504** | Gateway Timeout - Timeout bei externem Service | OSRM Timeout (>8s) |

---

## Statuscode-Policy

### ✅ Erlaubte Codes

- **400/422**: Validation/Userfehler
- **404**: Ressource nicht gefunden
- **429**: Rate-Limit/Quota überschritten
- **500**: Uncaught Exception (mit Trace-ID)
- **503**: Service Unavailable (OSRM nicht erreichbar)
- **504**: Gateway Timeout (OSRM Timeout)

### ❌ Nicht erlaubte Codes

- **402**: Payment Required → wird zu **400** gemappt (siehe `backend/core/error_handlers.py`)

---

## Implementierung

### Error Handler

**Datei:** `backend/core/error_handlers.py`

```python
async def http_exception_handler(request: Request, exc):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    status = getattr(exc, "status_code", 500)
    # 402 → 400
    if status == 402:
        status = 400
    return JSONResponse({
        "error": type(exc).__name__,
        "detail": getattr(exc, "detail", str(exc)),
        "request_id": rid
    }, status_code=status)
```

### Error Envelope Middleware

**Datei:** `backend/middlewares/error_envelope.py`

- **402 (Quota)** → **429** (Too Many Requests)
- **502/503/504 (Transient)** → **503** (Service Unavailable)

---

## Beispiele

### Validation-Fehler (422)
```python
from fastapi import HTTPException

raise HTTPException(status_code=422, detail="Ungültige Koordinaten")
```

### OSRM Timeout (504)
```python
from fastapi import HTTPException

raise HTTPException(status_code=504, detail="OSRM Timeout nach 8s")
```

### Uncaught Exception (500)
```python
# Wird automatisch von Error-Envelope-Middleware behandelt
# Trace-ID wird automatisch hinzugefügt
```

---

## Metriken

Alle Status-Codes werden von `error_tally` Middleware gezählt:
- **4xx**: `METRICS["http_4xx"]`
- **5xx**: `METRICS["http_5xx"]`

Abrufbar über: `GET /metrics/simple`

---

**Letzte Aktualisierung:** 2025-11-13

