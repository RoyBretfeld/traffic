# Standard-Audit-Checkliste

**Projekt:** FAMO TrafficApp 3.0  
**Version:** 1.0  
**Datum:** 2025-11-14

---

## Verwendung

Diese Checkliste ist für **jeden** Code-Audit verbindlich. Cursor soll alle Punkte systematisch abarbeiten und im Audit-Dokument abhaken.

---

## 1. Kontext klären

**Zu beantworten:**

- [ ] Welches Feature ist betroffen?
  - Beispiel: Sub-Routen-Generator, OSRM-Routing, Tour-Upload, Adress-Matching
  
- [ ] Welche Endpoints, Pfade oder UI-Elemente sind beteiligt?
  - Backend-Routes (z.B. `/api/tour/optimize`)
  - Frontend-Dateien (z.B. `frontend/index.html`)
  
- [ ] Welche Fehlermeldungen sind bekannt?
  - HTTP-Status-Codes (500, 404, 402, etc.)
  - Python-Stacktraces
  - Browser-Konsole-Fehler (TypeError, ReferenceError, etc.)
  - Laufzeitfehler (Timeouts, Deadlocks)

### ⚠️ PFLICHT: Multi-Layer-Kontext

**Jeder Audit MUSS mindestens eine Datei aus jedem betroffenen Layer im Kontext haben:**

- [ ] **Backend:** Mindestens 1 relevante `routes/*.py` oder `backend/routes/*.py` oder `services/*.py`
- [ ] **Frontend:** Mindestens 1 relevante `frontend/*.js` oder `frontend/*.html`
- [ ] **Datenbank (falls beteiligt):** `db/schema.py` oder `docs/database_schema.sql`
- [ ] **Infrastruktur (falls beteiligt):** `services/osrm_client.py` oder ENV-Variablen

**Regel:** Wenn Bug im UI sichtbar ist → Backend + Frontend sind PFLICHT!

**Warum?** Verhindert: "KI fixt nur Python, lässt JS kaputt"

**Dokumentation:**

```md
## Kontext

- **Feature:** [Name]
- **Endpoints:** [Liste]
- **UI-Elemente:** [Buttons, Formulare, Panels]
- **Fehlermeldungen:**
  - Server: [HTTP 500, Stacktrace]
  - Browser: [TypeError in console]
```

---

## 2. Backend prüfen (Python/FastAPI)

### 2.1 Routen identifizieren

- [ ] Relevante FastAPI-Routen finden
  - `routes/*.py`
  - `backend/routes/*.py`
  - `backend/app.py` (Route-Registrierung)

- [ ] Request-Handler analysieren
  - Welche HTTP-Methode? (GET, POST, PUT, DELETE)
  - Welche Query-Parameter / Body-Parameter?
  - Welches Pydantic-Schema wird verwendet?

**Dokumentation:**

```python
# Beispiel: Route-Signatur
@router.post("/api/tour/optimize")
async def optimize_tours(payload: TourOptimizationRequest):
    # Request-Schema: TourOptimizationRequest
    # Response-Schema: TourOptimizationResponse
    pass
```

### 2.2 Services und Business Logic

- [ ] Relevante Service-Funktionen finden
  - `services/*.py`
  - `backend/services/*.py`

- [ ] Fehlerbehandlung prüfen
  - Sind `try-except` Blöcke vorhanden?
  - Werden Exceptions geloggt?
  - Werden sinnvolle HTTP-Status-Codes zurückgegeben?

- [ ] Input-Validierung prüfen
  - Pydantic-Modelle vorhanden?
  - Manuelle Validierung (z.B. `if not data: raise ValueError`)

**Dokumentation:**

```md
### Services

- `backend/services/tour_optimizer.py`
  - Funktion: `optimize_tour_routes()`
  - Fehlerbehandlung: ✅ (try-except + logging)
  - Input-Validierung: ⚠️ (fehlt Null-Check)
```

### 2.3 Logging und Debugging

- [ ] Sind relevante Logs vorhanden?
  - `logger.info()` / `logger.error()` / `logger.debug()`
  - Logs in `logs/*.log` Dateien

- [ ] Enthalten Logs ausreichend Kontext?
  - Request-ID, User-ID, Tour-Key, etc.
  - Keine sensiblen Daten (Passwörter, API-Keys)

- [ ] Sind Exceptions vollständig geloggt?
  - `logger.exception()` statt nur `logger.error()`

**Dokumentation:**

```md
### Logging-Status

- ✅ Strukturiertes Logging vorhanden
- ⚠️ Request-ID fehlt in einigen Logs
- ❌ Exception-Stacktraces nicht vollständig geloggt
```

### 2.4 Konfiguration

- [ ] Relevante ENV-Variablen prüfen
  - `config.env`
  - `backend/config.py`
  - Defaults bei fehlenden Variablen?

- [ ] Feature-Flags prüfen
  - Ist das Feature aktiviert?
  - Gibt es Debug-Modi?

**Dokumentation:**

```md
### Konfiguration

- `OSRM_URL`: http://localhost:5000 ✅
- `OSRM_TIMEOUT`: 30s ✅
- `ENABLE_SUBROUTES`: true ✅
```

---

## 3. Frontend prüfen (HTML/CSS/JavaScript)

### 3.1 UI-Elemente identifizieren

- [ ] Welche HTML-Datei enthält das betroffene Feature?
  - `frontend/index.html`
  - `frontend/panel-*.html`
  - `frontend/admin/*.html`

- [ ] Welche Buttons / Formulare sind beteiligt?
  - Button-ID, onclick-Handler
  - Form-ID, submit-Handler

**Dokumentation:**

```html
<!-- Beispiel: Betroffener Button -->
<button id="optimize-tours-btn" onclick="optimizeTours()">
  Routen optimieren
</button>
```

### 3.2 API-Calls analysieren

- [ ] Alle `fetch()` / AJAX-Calls finden
  - URL stimmt mit Backend-Route überein?
  - HTTP-Methode korrekt? (GET/POST/PUT/DELETE)
  - Headers korrekt? (Content-Type: application/json)

- [ ] Request-Body prüfen
  - JSON-Struktur entspricht Backend-Schema?
  - Pflichtfelder vorhanden?

- [ ] Response-Verarbeitung prüfen
  - Wird das Response-Schema korrekt geparst?
  - Fehlerbehandlung vorhanden? (catch-Block)
  - UI-Feedback bei Fehler?

**Dokumentation:**

```javascript
// Beispiel: API-Call
async function optimizeTours() {
    try {
        const response = await fetch('/api/tour/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tours: [...] })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        // ⚠️ Hier fehlt Validierung: ist data.sub_routes ein Array?
        data.sub_routes.forEach(route => { ... });
    } catch (e) {
        console.error('Fehler:', e);
        alert('Fehler beim Optimieren!'); // ✅ User-Feedback
    }
}
```

### 3.3 Defensive Programmierung

- [ ] Null-Checks vorhanden?
  - `if (data && data.sub_routes) { ... }`
  - `if (Array.isArray(data.sub_routes)) { ... }`

- [ ] Type-Checks vor Iterationen?
  - `data.sub_routes.forEach()` → Ist `sub_routes` ein Array?

- [ ] Error-Boundaries?
  - Try-Catch um kritische Operationen

**Checkliste:**

```md
### Defensive Checks

- [ ] Null-Check für `data`
- [ ] Array-Check für `data.sub_routes`
- [ ] Error-Handler für `fetch()`
- [ ] UI-Feedback bei Fehler
```

### 3.4 Browser-Konsole prüfen

- [ ] Logs sammeln (DevTools → Console)
  - Errors (rot)
  - Warnings (gelb)
  - Network-Errors (Netzwerk-Tab)

- [ ] Häufige Fehler identifizieren
  - `TypeError: Cannot read property 'X' of undefined`
  - `ReferenceError: X is not defined`
  - `SyntaxError: Unexpected token`

**Dokumentation:**

```md
### Browser-Fehler

- `TypeError: Cannot read properties of undefined (reading 'sub_routes')`
  - Datei: `index.html` Zeile 1234
  - Ursache: `data.sub_routes` ist undefined
```

---

## 4. Datenbank & Schema

### 4.1 Schema-Konsistenz

- [ ] Nutzt der Code Tabellen/Spalten, die im aktuellen Schema existieren?
  - Vergleich: `db/schema.py` ↔ `data/traffic.db`
  - Tools: `sqlite3 data/traffic.db ".schema"`

- [ ] Gibt es Schema-Drifts?
  - Alte Spalten im Code referenziert, die nicht mehr existieren
  - Neue Spalten in DB, die im Code fehlen

**Dokumentation:**

```sql
-- Beispiel: Schema-Drift erkannt

-- Code erwartet:
SELECT next_attempt FROM geo_fail WHERE ...

-- Aber Schema hat:
CREATE TABLE geo_fail (
    id INTEGER PRIMARY KEY,
    -- next_attempt fehlt! ❌
);
```

### 4.2 Migrationen

- [ ] Sind Migrationen notwendig?
  - ALTER TABLE, CREATE INDEX, etc.
  - Migrationsskript vorhanden? (`db/migrations/*.sql`)

- [ ] Sind Migrationen sicher?
  - Keine Datenverluste
  - Abwärtskompatibel (oder explizit dokumentiert)

**Dokumentation:**

```sql
-- Beispiel: Benötigte Migration

-- Migration: 2025-11-14_add_next_attempt_to_geo_fail.sql
ALTER TABLE geo_fail ADD COLUMN next_attempt INTEGER DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_geo_fail_next_attempt 
  ON geo_fail(next_attempt);
```

### 4.3 Indizes und Performance

- [ ] Sind Indizes für häufige Queries vorhanden?
  - WHERE-Klauseln → Index auf Spalte
  - JOIN-Operationen → Index auf Foreign Keys

- [ ] Gibt es langsame Queries?
  - EXPLAIN QUERY PLAN verwenden
  - Logs auf Timeouts prüfen

**Dokumentation:**

```md
### Performance-Analyse

- Query: `SELECT * FROM tours WHERE tour_key = ?`
  - Index: ✅ `idx_tours_tour_key`
  - Dauer: <1ms ✅

- Query: `SELECT * FROM customers WHERE zip_code LIKE '%123%'`
  - Index: ❌ Fehlt!
  - Dauer: 500ms ⚠️
  - Empfehlung: CREATE INDEX idx_customers_zip_code
```

### 4.4 Datenkonsistenz

- [ ] Sind Constraints definiert?
  - PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL

- [ ] Gibt es Daten-Anomalien?
  - Orphaned Records (Foreign Key zeigt auf gelöschten Datensatz)
  - Duplikate trotz UNIQUE-Constraint

**Dokumentation:**

```md
### Datenkonsistenz

- ✅ PRIMARY KEYs vorhanden
- ⚠️ FOREIGN KEYs nicht definiert (SQLite-Compat-Modus)
- ❌ 23 Duplikate in `customers` Tabelle gefunden
```

---

## 5. Infrastruktur / Externe Dienste

### 5.1 OSRM-Status

- [ ] OSRM-Container läuft?
  - `docker ps | grep osrm`
  - Health-Endpoint: `http://localhost:5000/health` oder `/nearest/v1/...`

- [ ] OSRM erreichbar aus der App?
  - `curl http://localhost:5000/route/v1/driving/...`
  - Timeout-Konfiguration korrekt?

- [ ] OSRM-Logs prüfen?
  - `docker logs osrm-backend`
  - Fehler bei Routing-Requests?

**Dokumentation:**

```md
### OSRM-Status

- Container: ✅ Läuft
- Erreichbarkeit: ✅ (curl erfolgreich)
- Response-Zeit: 45ms ✅
- Fehler in Logs: ❌ Keine
```

### 5.2 LLM-APIs (falls genutzt)

- [ ] OpenAI / Ollama erreichbar?
  - API-Key korrekt? (OpenAI)
  - Ollama-Server läuft? (localhost:11434)

- [ ] Timeout-Konfiguration?
  - Default: 60s für LLM-Calls

- [ ] Fehlerbehandlung bei API-Ausfällen?
  - Retry-Logic?
  - Fallback-Strategie?

**Dokumentation:**

```md
### LLM-APIs

- OpenAI: ✅ API-Key valide
- Ollama: ❌ Nicht erreichbar (localhost:11434)
- Fallback: ✅ Regex-basierte Adress-Erkennung
```

### 5.3 Konfiguration (ENV-Variablen)

- [ ] Alle benötigten ENV-Variablen gesetzt?
  - `config.env` vollständig?
  - Defaults für fehlende Variablen?

- [ ] Ports korrekt?
  - Backend: 8000 (default)
  - OSRM: 5000 (default)
  - Ollama: 11434 (default)

**Dokumentation:**

```md
### ENV-Variablen

- `OSRM_URL`: http://localhost:5000 ✅
- `OPENAI_API_KEY`: sk-... ✅
- `DATABASE_PATH`: data/traffic.db ✅
- `LOG_LEVEL`: INFO ✅
```

### 5.4 Health-Checks

- [ ] Health-Endpoints funktionieren?
  - `/health` → Backend-Status
  - `/health/osrm` → OSRM-Status
  - `/health/db` → Datenbank-Status

- [ ] Monitoring / Metriken?
  - `/api/osrm/metrics` → OSRM-Statistiken
  - `/api/metrics` → App-Statistiken

**Dokumentation:**

```md
### Health-Check-Status

- `/health`: ✅ { "status": "healthy" }
- `/health/osrm`: ✅ { "osrm_reachable": true }
- `/health/db`: ✅ { "db_connected": true }
```

---

## 6. Tests

### 6.1 Existierende Tests

- [ ] Gibt es bereits Tests für das betroffene Feature?
  - `tests/*.py`
  - `tests/integration/*.py`
  - `tests/unit/*.py`

- [ ] Schlagen Tests fehl?
  - `pytest` ausführen
  - Fehlerbild mit echtem Bug abgleichen

**Dokumentation:**

```md
### Test-Status

- Existierende Tests: ✅ `tests/test_tour_optimizer.py`
- Test-Ergebnis: ❌ 2 Tests fehlgeschlagen
  - `test_optimize_w_tours` → AssertionError
  - `test_subroutes_generation` → TypeError
```

### 6.2 Neue Tests schreiben

- [ ] Mindestens einen Regressionstest definieren
  - Test soll den konkreten Bug abdecken
  - Test soll nach dem Fix erfolgreich sein

- [ ] Test-Struktur
  - Arrange: Setup (Testdaten vorbereiten)
  - Act: Aktion (Funktion aufrufen)
  - Assert: Validierung (Erwartetes Ergebnis prüfen)

**Beispiel:**

```python
def test_subroutes_generator_regression():
    """
    Regression-Test für Bug #123:
    Sub-Routen-Generator wirft TypeError bei W-Touren mit >4 Kunden
    """
    # Arrange
    payload = {
        "tours": [
            {"key": "W07", "customers": ["K1", "K2", "K3", "K4", "K5"]}
        ]
    }
    
    # Act
    response = client.post("/api/tour/optimize", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "sub_routes" in data
    assert isinstance(data["sub_routes"], list)
    assert len(data["sub_routes"]) > 0
```

### 6.3 Manuelle Tests

- [ ] UI durchklicken
  - Button klicken
  - Formulare ausfüllen
  - Response im UI prüfen

- [ ] API-Calls testen
  - Postman / curl
  - Verschiedene Payloads testen (happy path, edge cases)

**Dokumentation:**

```md
### Manuelle Tests

1. UI-Test: Button "Routen optimieren" klicken
   - ✅ Keine Fehler in Browser-Konsole
   - ✅ Sub-Routen werden angezeigt
   - ✅ Karte wird aktualisiert

2. API-Test (curl):
   ```bash
   curl -X POST http://localhost:8000/api/tour/optimize \
     -H "Content-Type: application/json" \
     -d '{"tours": [...]}'
   ```
   - ✅ HTTP 200
   - ✅ Response enthält `sub_routes`
```

---

## 7. Ergebnis-Dokumentation

### 7.1 Root Cause

- [ ] Root Cause identifiziert (nicht nur Symptom!)
  - Was war die eigentliche Ursache?
  - Wo im Code liegt der Fehler?

**Format:**

```md
### Root Cause

**Problem:** TypeError in `data.sub_routes.forEach()`

**Ursache:**
- Backend sendet `{"subRoutes": [...]}` (camelCase)
- Frontend erwartet `{"sub_routes": [...]}` (snake_case)
- Wenn Backend-Response nicht passt, ist `data.sub_routes` undefined
- `undefined.forEach()` wirft TypeError

**Datei:** `frontend/index.html` Zeile 1234
```

### 7.2 Konkreter Fix

- [ ] Alle geänderten Dateien auflisten
  - Dateiname, Zeilen, Funktionen

- [ ] Vorher/Nachher zeigen
  - Code-Diff oder kommentierte Blöcke

**Format:**

```md
### Fix

**Datei:** `backend/routes/tour_routes.py` Zeile 45

**Vorher:**
```python
return {"subRoutes": routes}  # camelCase ❌
```

**Nachher:**
```python
return {"sub_routes": routes}  # snake_case ✅
```

**Grund:** Frontend erwartet snake_case (siehe API-Kontrakt)
```

### 7.3 Auswirkungen

- [ ] Welche anderen Teile des Systems sind betroffen?
  - Andere Endpoints?
  - Andere UI-Elemente?
  - Tests?

**Format:**

```md
### Auswirkungen

- ✅ Frontend funktioniert jetzt korrekt
- ⚠️ Alte API-Clients (falls vorhanden) müssen angepasst werden
- ✅ Tests wurden aktualisiert
```

### 7.4 Härtung / Verbesserungen

- [ ] Vorschläge für zusätzliche Checks
  - Defensive Programmierung
  - Logging
  - Tests

**Format:**

```md
### Verbesserungsvorschläge

1. **Defensive Checks im Frontend:**
   ```javascript
   if (data && data.sub_routes && Array.isArray(data.sub_routes)) {
       data.sub_routes.forEach(route => { ... });
   }
   ```

2. **API-Schema-Validierung:**
   - Pydantic-Response-Modell für `/api/tour/optimize`
   - Automatische Schema-Prüfung in Tests

3. **Logging:**
   - Backend soll Response-Format loggen (Debug-Level)
```

### 7.5 LESSONS_LOG Eintrag

- [ ] Eintrag für `docs/ki/LESSONS_LOG.md` vorbereiten
  - Falls es ein neuer Fehlertyp ist
  - Falls es eine generelle Lehre gibt

**Format:**

```md
## 2025-11-14 – API-Kontrakt: snake_case vs. camelCase

**Symptom:**
- Frontend wirft TypeError bei API-Response

**Ursache:**
- Backend nutzt camelCase (`subRoutes`)
- Frontend erwartet snake_case (`sub_routes`)

**Fix:**
- Backend auf snake_case umgestellt
- Frontend mit defensiven Checks gehärtet

**Was die KI künftig tun soll:**
- Immer API-Kontrakt prüfen (Backend ↔ Frontend)
- Konsistente Namenskonvention (snake_case für Python/JSON)
- Defensive Checks im Frontend bei allen API-Calls
```

---

## 8. Abschluss-Checkliste

**Vor Audit-Abschluss prüfen:**

- [ ] Alle Punkte 1-7 bearbeitet
- [ ] Root Cause identifiziert
- [ ] Fix implementiert und getestet
- [ ] Dokumentation erstellt
- [ ] ZIP-Archiv angelegt (falls größeres Audit)
- [ ] LESSONS_LOG aktualisiert (falls relevant)

**Qualitäts-Check:**

- [ ] Syntax-Check erfolgreich
- [ ] Linter-Errors behoben
- [ ] Keine neuen Fehler eingeführt
- [ ] Manuelle Tests erfolgreich
- [ ] Audit-Dokument vollständig

---

## 9. Audit-Completion-Report

**Am Ende jedes Audits:**

```md
## Audit-Completion-Report

**Datum:** 2025-11-14
**Dauer:** 2 Stunden
**Status:** ✅ Abgeschlossen

### Zusammenfassung

- Fehler gefunden: 5
- Fehler behoben: 5
- Tests hinzugefügt: 2
- Dateien geändert: 7

### Code-Qualität

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| Syntax-Fehler | 1 | 0 |
| Linter-Warnings | 12 | 3 |
| Test-Coverage | 45% | 62% |
| Defensive Checks | 3 | 15 |

### Empfehlungen

1. Performance-Optimierung: OSRM-Caching implementieren
2. Monitoring: Sentry für Frontend-Errors aktivieren
3. Dokumentation: API-Docs aktualisieren

### Nächste Schritte

- [ ] Performance-Tests durchführen
- [ ] E2E-Tests mit Playwright schreiben
- [ ] Deployment-Dokumentation aktualisieren
```

---

**Ende der Checkliste**  
**Nächste Schritte:** Audit durchführen, Ergebnisse dokumentieren, LESSONS_LOG aktualisieren

