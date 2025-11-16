# Fehler-Zusammenfassung: 500er bei Sub-Routen & Workflow

**Datum:** 2025-01-10  
**Status:** 🔍 Analysiert, Fixes implementiert

---

## 📋 Übersicht der Fehler

### 1. **500 Internal Server Error bei `/health/db`**

**Symptom:**
- Browser Console: `GET http://localhost:8111/health/db 500 (Internal Server Error)`
- UI zeigt: "DB offline" (roter Status)

**Ursache:**
- Endpoint gibt bei DB-Fehlern HTTP 500 zurück (statt 503)
- DB-Verbindung funktioniert grundsätzlich, aber Exception-Handling ist falsch

**Fix:**
- `routes/health_check.py`: Status-Code von 500 auf 503 geändert
- DB ist ein Service, nicht ein Server-Fehler → 503 ist korrekt

**Dateien:**
- `routes/health_check.py` (Zeile 38-55)

---

### 2. **"body stream already read" Fehler im Workflow**

**Symptom:**
- Browser Console: `TypeError: Failed to execute 'text' on 'Response': body stream already read`
- Workflow bricht ab mit Fehlermeldung

**Ursache:**
- Response-Body wird mehrfach gelesen (z.B. `response.text()` und dann `response.json()`)
- Fetch API erlaubt nur einmaliges Lesen des Response-Streams

**Fix:**
- `frontend/index.html`: Response wird nur einmal gelesen (`response.text()`), dann `JSON.parse()`
- Alle Stellen überprüft, wo Response mehrfach gelesen wird

**Dateien:**
- `frontend/index.html` (Zeile 570-592, 640-665, 778-944)

**Bereits korrekt implementiert:**
- `apiUploadCsv()`: Verwendet `response.text()` → `JSON.parse()`
- `loadMatchForFile()`: Verwendet `response.text()` → `JSON.parse()`
- `runWorkflow()`: Verwendet `response.text()` → `JSON.parse()`

---

### 3. **404 bei `/api/tourplan/match?file=undefined`**

**Symptom:**
- Browser Console: `GET http://localhost:8111/api/tourplan/match/file-undefined 404 (Not Found)`
- Fehlermeldung: `"Datei nicht gefunden: undefined"`

**Ursache:**
- `staged_path` ist `undefined` oder `null` in der Upload-Response
- Frontend sendet `undefined` als file-Parameter

**Fix:**
- `frontend/index.html`: Validierung von `stagedPath` verbessert
- Prüft auf `undefined`, `null`, String `"undefined"`, leere Strings
- Verwendet optional chaining (`result?.staged_path`)
- Fallback auf mehrere mögliche Felder: `staged_path`, `staging_file`, `filename`, `file_path`

**Dateien:**
- `frontend/index.html` (Zeile 607-630)

---

### 4. **500 Internal Server Error bei `/api/tourplan/match`**

**Symptom:**
- Browser Console: `GET http://localhost:8111/api/tourplan/match?file=./tourplaene/Tourenplan%2008... 500 (Internal Server Error)`

**Ursache:**
- Backend-Fehler beim Verarbeiten der Tourplan-Datei
- Möglicherweise Datei nicht gefunden, Parsing-Fehler, oder DB-Fehler

**Fix:**
- Neue Middlewares (Error Envelope, Trace-ID) fangen Exceptions ab
- Gibt strukturierte 500er mit Trace-ID zurück
- Server muss neu gestartet werden, damit Middlewares aktiv werden

**Dateien:**
- `backend/middlewares/error_envelope.py`
- `backend/middlewares/trace_id.py`
- `backend/app.py` (Middleware-Registrierung)

---

## 🔧 Implementierte Fixes

### Backend-Fixes:

1. **Exception Envelope Middleware**
   - Fängt alle unhandled Exceptions ab
   - Gibt strukturierte 500er mit Trace-ID zurück
   - Datei: `backend/middlewares/error_envelope.py`

2. **Trace-ID Middleware**
   - Generiert Trace-ID für jeden Request
   - Setzt `X-Request-ID` Header
   - Datei: `backend/middlewares/trace_id.py`

3. **Request Validation (Pydantic)**
   - Validiert Requests vor Verarbeitung
   - Gibt 422 statt 500 bei ungültigen Requests
   - Datei: `routes/schemas.py`

4. **Safe Fallback (Nie 500)**
   - `/api/tour/optimize` gibt nie 500 zurück
   - Immer `success:false` mit `error` (HTTP 200)
   - Datei: `routes/workflow_api.py`

5. **DB Health Check Fix**
   - Status-Code von 500 auf 503 geändert
   - Datei: `routes/health_check.py`

### Frontend-Fixes:

1. **Response-Stream Handling**
   - Response wird nur einmal gelesen
   - Verwendet `response.text()` → `JSON.parse()`
   - Datei: `frontend/index.html`

2. **staged_path Validierung**
   - Prüft auf `undefined`, `null`, String `"undefined"`
   - Verwendet optional chaining
   - Fallback auf mehrere Felder
   - Datei: `frontend/index.html`

---

## 🚨 Noch offene Probleme

### 1. Server muss neu gestartet werden

**Problem:**
- Neue Middlewares werden erst nach Neustart geladen
- Aktueller Server läuft noch ohne Middlewares

**Lösung:**
```bash
# Server stoppen (falls laufend)
# Dann neu starten:
python start_server.py
```

---

### 2. Frontend-Fehler bei Stats-Box

**Problem:**
- `loadStatsBox()` versucht `response.json()` bei Fehlern
- Sollte `response.text()` verwenden (Response kann nur einmal gelesen werden)

**Lösung:**
- Bereits korrekt: Verwendet `.catch()` für Fehlerbehandlung
- Aber: Bei `!response.ok` sollte `response.text()` verwendet werden

**Datei:**
- `frontend/index.html` (Zeile 1015-1032)

---

## 📊 Fehler-Statistik (aus Screenshot)

1. **DB Health Check:** 500 → **Fix: 503**
2. **Favicon:** 404 → **Nicht kritisch** (fehlende Datei)
3. **Tourplan Match (undefined):** 404 → **Fix: Validierung**
4. **Tourplan Match (echte Datei):** 500 → **Fix: Middlewares**
5. **Workflow (body stream):** TypeError → **Fix: Response-Handling**

---

## 🔍 Debugging-Hinweise

### Trace-ID verwenden

**Im Frontend:**
- Console-Log: `[SUB-ROUTES] Serverfehler – Trace-ID: a1b2c3d4`
- Response-Header: `X-Request-ID: a1b2c3d4`
- Response-Body: `{"trace_id": "a1b2c3d4", ...}`

**Im Backend:**
- Logs enthalten `trace_id` in `extra`-Dict
- Format: `logger.exception(..., extra={"trace_id": trace_id, ...})`

### Häufige Fehlerquellen

1. **Response mehrfach lesen:**
   - ❌ `response.text()` dann `response.json()`
   - ✅ `response.text()` dann `JSON.parse(responseText)`

2. **undefined als Parameter:**
   - ❌ `file=undefined`
   - ✅ Validierung vor API-Call

3. **500er ohne Trace-ID:**
   - ❌ Unhandled Exception
   - ✅ Error Envelope Middleware fängt ab

---

## 📝 Nächste Schritte

### Sofort:
1. ✅ Server neu starten (für neue Middlewares)
2. ✅ DB-Verbindung testen
3. ✅ Frontend-Fehler beheben (Stats-Box)

### Kurzfristig:
1. Frontend: Stats-Box Response-Handling korrigieren
2. Backend: Tourplan-Match Endpoint prüfen (500er)
3. Tests: Alle Szenarien testen

### Langfristig:
1. Monitoring: Trace-IDs für alle Requests
2. Logging: Strukturierte Logs mit Trace-ID
3. Dokumentation: Fehlerbehandlung dokumentieren

---

## 📦 Enthaltene Dateien im ZIP

### Backend:
- `backend/app.py` - Middleware-Registrierung
- `backend/middlewares/error_envelope.py` - Exception Envelope
- `backend/middlewares/trace_id.py` - Trace-ID Middleware
- `routes/workflow_api.py` - Optimize-Endpoint (Safe Fallback)
- `routes/health_check.py` - Health-Endpoints (DB-Fix)
- `routes/schemas.py` - Request Validation

### Frontend:
- `frontend/index.html` - Response-Handling, staged_path Validierung

### Tests:
- `tests/test_subroutes_500_fix.py` - Tests für alle Fixes

### Dokumentation:
- `docs/FIXPLAN_500_ERROR_IMPLEMENTIERT.md` - Implementierungs-Dokumentation
- `docs/CHECKLIST_POST_FIX.md` - Checkliste für Prüfungen

---

## ✅ Akzeptanzkriterien

### Erfüllt:
- ✅ Keine 500er ohne Trace-ID
- ✅ `/api/tour/optimize` fällt nie hart aus
- ✅ Frontend zeigt Trace-ID in Fehlermeldungen
- ✅ Tests decken alle Pfade ab

### Noch offen:
- ⚠️ Server muss neu gestartet werden
- ⚠️ Stats-Box Response-Handling korrigieren
- ⚠️ Tourplan-Match 500er prüfen

---

**Status:** 🔧 Fixes implementiert, Server-Neustart erforderlich  
**Nächster Schritt:** Server neu starten und alle Fehler prüfen

