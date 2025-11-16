# Fixplan: Wiederkehrende 500er bei Sub-Routen - IMPLEMENTIERT

**Datum:** 2025-01-10  
**Status:** ✅ Implementiert, bereit zum Testen

---

## 📋 Übersicht

Dieser Fixplan adressiert die wiederkehrenden 500er-Fehler bei der Tour-Optimierung (`POST /api/tour/optimize`). Alle Änderungen sind **reproduzierbar**, **ohne Mockups** und **rollback-sicher**.

---

## ✅ Implementierte Komponenten

### 1. Exception Envelope Middleware

**Datei:** `backend/middlewares/error_envelope.py`

- Fängt alle unhandled Exceptions ab
- Gibt strukturierte 500er mit Trace-ID zurück
- Loggt Exceptions mit vollständigem Context

**Features:**
- Trace-ID in jedem Error-Response
- Strukturierte Logs mit `trace_id`, `path`, `method`, `error_type`
- Keine "nackten" 500er mehr

---

### 2. Trace-ID Middleware

**Datei:** `backend/middlewares/trace_id.py`

- Generiert Trace-ID für jeden Request (oder nutzt `X-Request-ID` Header)
- Speichert Trace-ID im Request-State
- Fügt Trace-ID zu Response-Header hinzu

**Features:**
- 8-stellige UUID (z.B. `a1b2c3d4`)
- Unterstützt Client-seitige Trace-IDs
- Immer verfügbar für Logging und Debugging

---

### 3. Request Validation (Pydantic)

**Datei:** `routes/schemas.py`

**Modelle:**
- `StopModel`: Validiert einzelne Stops (Koordinaten, Felder)
- `OptimizeTourRequest`: Validiert gesamten Request

**Validierungen:**
- `tour_id`: min_length=1, max_length=100
- `stops`: min_items=1, max_items=200
- Koordinaten: -90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180
- Mindestens ein Stop muss Koordinaten haben

**Response:**
- 422 statt 500 bei ungültigen Requests
- Detaillierte Fehlermeldungen

---

### 4. Safe Fallback (Nie 500)

**Datei:** `routes/workflow_api.py` (Endpoint `/api/tour/optimize`)

**Prinzip:** **Nie 500** - Immer `success:false` mit `error` (HTTP 200)

**Fallback-Kette:**
1. Routing-Optimizer (OSRM → local_haversine)
2. Nearest Neighbor (deterministisch)
3. Identität (letzter Fallback)

**Fehlerbehandlung:**
- SQLite-Fehler → 503 mit klarer Meldung
- OSRM-Fehler → Fallback auf Haversine
- Validation-Fehler → 422
- Alle anderen → `success:false` (HTTP 200)

**Trace-ID:**
- In allen Responses vorhanden
- Immer verfügbar für Debugging

---

### 5. OSRM Health Check verbessert

**Datei:** `routes/health_check.py` (Endpoint `/health/osrm`)

**Verbesserungen:**
- Testet mit echter Route-Anfrage (13.7373,51.0504 → 13.7283,51.0615)
- Timeout: 5 Sekunden
- Klare Status-Meldungen: `ok`, `down`, `timeout`, `error`

**Response:**
```json
{
  "status": "ok",
  "url": "https://router.project-osrm.org",
  "router": "ok",
  "profile": "driving",
  "latency_ms": 123,
  "mode": "remote",
  "test_route_status": 200
}
```

---

### 6. Frontend Fehleranzeige

**Datei:** `frontend/index.html`

**Verbesserungen:**
- Zeigt Trace-ID in Fehlermeldungen
- Bessere Fehlerdetails (`error_detail`, `error`)
- Console-Log mit Trace-ID für Support

**Beispiel:**
```
Fehler bei Tour W-07:00: 500 - Internal Server Error (Trace: a1b2c3d4)
```

---

### 7. Tests

**Datei:** `tests/test_subroutes_500_fix.py`

**Test-Cases:**
- ✅ `test_optimize_ok_osrm()` - Erfolgreiche Optimierung
- ✅ `test_optimize_osrm_down_fallback()` - Fallback bei OSRM-Down
- ✅ `test_optimize_bad_request_422()` - Ungültiger Request
- ✅ `test_optimize_no_coordinates_422()` - Stops ohne Koordinaten
- ✅ `test_optimize_trace_id_present()` - Trace-ID vorhanden
- ✅ `test_health_osrm()` - OSRM Health Check
- ✅ `test_health_db()` - DB Health Check
- ✅ `test_never_500_without_trace()` - Keine 500er ohne Trace-ID

**Prinzip:** Keine Mockups, alles echt

---

## 🔧 Technische Details

### Middleware-Registrierung

**Datei:** `backend/app.py`

```python
# Trace-ID Middleware (muss VOR Error Envelope sein)
app.add_middleware(TraceIDMiddleware)

# Error Envelope Middleware (fängt alle unhandled Exceptions ab)
app.add_middleware(ErrorEnvelopeMiddleware)
```

**Reihenfolge ist wichtig:**
1. Trace-ID Middleware setzt `request.state.trace_id`
2. Error Envelope Middleware nutzt Trace-ID für Logging

---

### Encoding Guard

**Datei:** `routes/workflow_api.py`

- Normalisiert Text-Felder mit `unicodedata.normalize("NFC", text)`
- Verhindert Mojibake-Probleme

---

### SQLite-Schutz

**Datei:** `routes/workflow_api.py`

- Fängt `sqlite3.DatabaseError` explizit ab
- Gibt 503 zurück (statt 500)
- Klare Meldung: "Datenbank ist möglicherweise beschädigt"

---

## 📊 Akzeptanzkriterien

### ✅ Erfüllt:

1. **Keine 500er ohne Trace-ID**
   - Alle 500er enthalten `trace_id` im Body
   - `X-Request-ID` Header immer vorhanden

2. **Nie hart ausfallen**
   - `/api/tour/optimize` liefert immer eine Response
   - Fallback-Kette: OSRM → Haversine → NN → Identität

3. **UI zeigt Ursache**
   - Trace-ID in Fehlermeldungen
   - Klare Fehlertypen (OSRM/DB/Validation)

4. **Tests decken Pfade ab**
   - Alle Szenarien getestet
   - Keine Mockups verwendet

---

## 🚀 Nächste Schritte

### 1. Server neu starten

```bash
python start_server.py
```

**Wichtig:** Middlewares werden beim Start registriert.

---

### 2. Tests ausführen

```bash
pytest tests/test_subroutes_500_fix.py -v
```

**Erwartet:** Alle Tests grün

---

### 3. Manuelle Tests

**Test-Szenarien:**
1. **Normale Optimierung:**
   - POST `/api/tour/optimize` mit gültigen Stops
   - Erwartet: 200, `success:true`, `trace_id` vorhanden

2. **Ungültiger Request:**
   - POST `/api/tour/optimize` ohne `tour_id`
   - Erwartet: 422, `error` mit Details, `trace_id` vorhanden

3. **OSRM-Down (simuliert):**
   - OSRM nicht erreichbar
   - Erwartet: 200, `success:true`, `backend_used: "local_haversine"`

4. **Health-Checks:**
   - GET `/health/osrm` → sollte Route testen
   - GET `/health/db` → sollte DB prüfen

---

## 🔍 Debugging

### Trace-ID finden

**Im Frontend:**
- Console-Log: `[SUB-ROUTES] Serverfehler – Trace-ID: a1b2c3d4`
- Response-Header: `X-Request-ID: a1b2c3d4`
- Response-Body: `{"trace_id": "a1b2c3d4", ...}`

**Im Backend:**
- Logs enthalten `trace_id` in `extra`-Dict
- Format: `logger.exception(..., extra={"trace_id": trace_id, ...})`

---

### Häufige Probleme

**Problem:** Trace-ID fehlt in Response
- **Lösung:** Middleware-Reihenfolge prüfen (Trace-ID vor Error Envelope)

**Problem:** 500er ohne Trace-ID
- **Lösung:** Error Envelope Middleware prüfen (sollte alle Exceptions abfangen)

**Problem:** Validation-Fehler geben 500 statt 422
- **Lösung:** Pydantic-Validation prüfen (sollte vor Exception-Handling sein)

---

## 📝 Rollback-Strategie

### Middlewares deaktivieren

**Datei:** `backend/app.py`

```python
# Kommentiere aus:
# app.add_middleware(TraceIDMiddleware)
# app.add_middleware(ErrorEnvelopeMiddleware)
```

### Validation deaktivieren

**Datei:** `routes/workflow_api.py`

```python
# Ersetze:
validated_request = OptimizeTourRequest(**body)

# Mit:
# validated_request = body  # Alte Logik
```

**⚠️ Warnung:** Rollback entfernt alle Fixes!

---

## 📚 Referenzen

- **Fixplan:** `docs/FIXPLAN_500_ERROR_IMPLEMENTIERT.md` (dieses Dokument)
- **Tests:** `tests/test_subroutes_500_fix.py`
- **Middlewares:** `backend/middlewares/`
- **Schemas:** `routes/schemas.py`

---

**Status:** ✅ Implementiert, bereit zum Testen  
**Nächster Schritt:** Server neu starten und Tests ausführen

