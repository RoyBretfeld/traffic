# Test-Strategie für kritische Fixes (2025-01-10)

**Datum:** 2025-01-10  
**Status:** ✅ Tests erstellt

---

## 📋 Übersicht

Tests für alle kritischen Fixes vom 2025-01-10, um sicherzustellen, dass alles funktioniert.

---

## ✅ Erstellte Tests

### 1. `tests/test_pydantic_v2_fixes.py`
**Zweck:** Unit Tests für Pydantic V2 Kompatibilität

**Test-Cases:**
- ✅ `test_stop_model_direct_attribute_access()` - Direkter Attribut-Zugriff funktioniert
- ✅ `test_stop_model_model_dump()` - `model_dump()` funktioniert (Pydantic V2)
- ✅ `test_stop_model_no_mutation()` - Keine direkte Mutation von Pydantic-Modellen
- ✅ `test_optimize_request_validation()` - Request-Validierung funktioniert
- ✅ `test_optimize_request_no_coordinates_fails()` - Validierung schlägt bei fehlenden Koordinaten fehl
- ✅ `test_optimize_endpoint_pydantic_models()` - Endpoint akzeptiert Pydantic-Modelle
- ✅ `test_optimize_endpoint_encoding_normalization()` - Encoding-Normalisierung funktioniert
- ✅ `test_fill_missing_accepts_limit_not_batch_limit()` - `fill_missing()` Parameter korrekt
- ✅ `test_match_endpoint_post_variant()` - POST-Variante funktioniert

### 2. `tests/test_critical_fixes_2025_01_10.py`
**Zweck:** Integration Tests für alle kritischen Fixes

**Test-Cases:**
- ✅ `test_optimize_tour_never_500()` - Endpoint gibt nie 500 zurück
- ✅ `test_optimize_tour_trace_id_present()` - Trace-ID ist in Error-Responses vorhanden
- ✅ `test_stop_model_no_get_method()` - StopModel hat keine `.get()` Methode
- ✅ `test_stop_model_to_dict_via_model_dump()` - Konvertierung zu Dict funktioniert
- ✅ `test_optimize_request_handles_pydantic_models()` - Endpoint verarbeitet Pydantic-Modelle
- ✅ `test_error_envelope_middleware_catches_exceptions()` - Middleware fängt Exceptions ab
- ✅ `test_error_envelope_uses_getattr()` - Error Envelope verwendet `getattr()`

---

## 🚀 Tests ausführen

### Alle Tests:
```bash
pytest tests/test_pydantic_v2_fixes.py tests/test_critical_fixes_2025_01_10.py -v
```

### Einzelne Test-Datei:
```bash
# Pydantic V2 Tests
pytest tests/test_pydantic_v2_fixes.py -v

# Integration Tests
pytest tests/test_critical_fixes_2025_01_10.py -v
```

### Mit Coverage:
```bash
pytest tests/test_pydantic_v2_fixes.py tests/test_critical_fixes_2025_01_10.py --cov=routes --cov=backend --cov-report=html
```

---

## 📊 Test-Abdeckung

### Behobene Probleme:
- ✅ `fill_missing()` Parameter (`batch_limit` → `limit`)
- ✅ `StopModel.get()` → `StopModel.lat/lon` (direkter Zugriff)
- ✅ Pydantic Mutability (keine direkte Mutation)
- ✅ `model_dump()` statt `dict()` (Pydantic V2)
- ✅ `request.state.get()` → `getattr(request.state, ...)` (Error Envelope)
- ✅ Encoding-Normalisierung (NACH Konvertierung zu Dict)

### Getestete Endpunkte:
- ✅ `POST /api/tour/optimize` - Tour-Optimierung
- ✅ `POST /api/tourplan/match` - Match-Endpoint (POST-Variante)

### Getestete Komponenten:
- ✅ `routes/schemas.py` - Pydantic-Modelle
- ✅ `routes/workflow_api.py` - Optimize-Endpoint
- ✅ `routes/tourplan_match.py` - Match-Endpoint
- ✅ `backend/middlewares/error_envelope.py` - Error Envelope

---

## 🔍 KI-Code-Check (Geplant)

### AI-Test Orchestrator
**Dokumentation:** `docs/ai_test_orchestrator_konzept_implementierungsplan_vanilla_js_fast_api.md`

**Status:** ⏸️ Geplant (Phase 3.3 - Deployment & AI-Ops)

**Ziele:**
- Automatische Testausführung (Quick/Full)
- LLM-Auswertung der Testergebnisse
- Root-Cause-Hinweise, Priorisierung P0–P2
- Fix-Skizzen von der KI

**Test-Suites:**
- **A. Backend/API:** Routing-Endpoints, Health-Checks, SQLite-Integrität
- **B. Daten/Encoding:** Mojibake-Guard, CSV-Ingest
- **C. Routing/Geometrie:** OSRM-Roundtrip, Distanzplausibilität
- **D. Performance:** Latenz (P50/P90/P99), Speicher/Platz
- **E. Frontend:** UI-Verfügbarkeit, Polyline-Dekodierung

**API-Endpunkte (geplant):**
- `POST /api/ai-test/run` - Test ausführen
- `GET /api/ai-test/status?run_id=` - Status abfragen
- `GET /api/ai-test/result?run_id=` - Ergebnis abrufen
- `WS /ws/ai-test/stream?run_id=` - Live-Logs

**Nächste Schritte:**
1. Backend: Suite-Registry + Runner + Routes
2. Frontend: `ai-test.html` + `ai-test.js`
3. LLM-Integration für Auswertung

---

## ✅ Checkliste

### Tests:
- [x] Unit Tests für Pydantic V2 erstellt
- [x] Integration Tests für kritische Fixes erstellt
- [ ] Tests lokal ausgeführt und grün
- [ ] Tests in CI/CD integriert (wenn vorhanden)

### Dokumentation:
- [x] Test-Strategie dokumentiert
- [x] Test-Abdeckung dokumentiert
- [x] KI-Code-Check Plan referenziert

### Nächste Schritte:
- [ ] Tests ausführen: `pytest tests/test_pydantic_v2_fixes.py tests/test_critical_fixes_2025_01_10.py -v`
- [ ] Fehler beheben (falls vorhanden)
- [ ] AI-Test Orchestrator implementieren (Phase 3.3)

---

## 📝 Notizen

**Wichtige Erkenntnisse:**
- Pydantic V2 Modelle sind standardmäßig immutable
- Encoding-Normalisierung muss NACH `model_dump()` erfolgen
- `request.state` ist ein State-Objekt, kein Dict → `getattr()` verwenden
- `fill_missing()` akzeptiert `limit`, nicht `batch_limit`

**Bekannte Einschränkungen:**
- Einige Tests benötigen laufenden Server (Integration Tests)
- OSRM-Tests benötigen Netzwerk-Verbindung
- AI-Test Orchestrator ist noch nicht implementiert

---

**Status:** ✅ Tests erstellt, bereit zum Ausführen  
**Nächster Schritt:** Tests ausführen und Fehler beheben

