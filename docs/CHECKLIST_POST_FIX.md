# Checkliste: Was noch gecheckt werden muss (nach 500er-Fix)

**Datum:** 2025-01-10  
**Status:** 🔍 Zu prüfen

---

## 🎯 Übersicht

Diese Checkliste listet alle Punkte auf, die nach dem 500er-Fix noch geprüft werden müssen.

---

## ✅ Backend-Checks

### 1. Middleware-Registrierung
- [ ] Server startet ohne Fehler
- [ ] Trace-ID Middleware wird geladen (Log: `[STARTUP] Trace-ID Middleware aktiviert`)
- [ ] Error Envelope Middleware wird geladen
- [ ] Middleware-Reihenfolge korrekt (Trace-ID vor Error Envelope)

**Prüfung:**
```bash
python start_server.py
# Prüfe Logs auf Middleware-Registrierung
```

---

### 2. Request Validation
- [ ] Pydantic-Modelle werden korrekt importiert
- [ ] Ungültige Requests geben 422 (nicht 500)
- [ ] Fehlermeldungen sind verständlich
- [ ] Trace-ID ist in 422-Responses vorhanden

**Test:**
```bash
curl -X POST http://localhost:8111/api/tour/optimize \
  -H "Content-Type: application/json" \
  -d '{"stops": []}'
# Erwartet: 422, {"error": "...", "trace_id": "..."}
```

---

### 3. Exception Handling
- [ ] Alle Exceptions werden abgefangen
- [ ] Keine "nackten" 500er mehr
- [ ] Trace-ID in allen Error-Responses
- [ ] SQLite-Fehler geben 503 (nicht 500)

**Test:**
```bash
# Simuliere Fehler (z.B. ungültige Koordinaten)
curl -X POST http://localhost:8111/api/tour/optimize \
  -H "Content-Type: application/json" \
  -d '{"tour_id": "TEST", "stops": [{"lat": 999, "lon": 999}]}'
# Erwartet: 422 oder 200 mit success:false
```

---

### 4. OSRM Health Check
- [ ] `/health/osrm` testet echte Route
- [ ] Timeout funktioniert (5s)
- [ ] Status-Meldungen sind klar (`ok`, `down`, `timeout`)
- [ ] Latenz wird gemessen

**Test:**
```bash
curl http://localhost:8111/health/osrm
# Erwartet: 200 oder 503, {"status": "...", "latency_ms": ...}
```

---

### 5. Fallback-Kette
- [ ] OSRM-Fehler → Fallback auf Haversine
- [ ] Haversine-Fehler → Fallback auf Nearest Neighbor
- [ ] NN-Fehler → Fallback auf Identität
- [ ] Alle Fallbacks liefern `success:true` oder `success:false` (nie 500)

**Test:**
```bash
# Teste mit gültigen Stops
curl -X POST http://localhost:8111/api/tour/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "tour_id": "TEST",
    "stops": [
      {"lat": 51.0504, "lon": 13.7373, "name": "Start"},
      {"lat": 51.0615, "lon": 13.7283, "name": "Ende"}
    ]
  }'
# Erwartet: 200, {"success": true, "trace_id": "...", ...}
```

---

## 🎨 Frontend-Checks

### 6. Fehleranzeige
- [ ] Trace-ID wird in Fehlermeldungen angezeigt
- [ ] Fehlerdetails sind verständlich
- [ ] Console-Log enthält Trace-ID
- [ ] Keine `errorDetail: null` mehr

**Prüfung:**
1. Öffne Browser-Console
2. Führe Optimierung mit Fehler aus
3. Prüfe: Trace-ID in Meldung und Console

---

### 7. Response-Handling
- [ ] `success:false` wird korrekt behandelt
- [ ] `trace_id` wird aus Response extrahiert
- [ ] `X-Request-ID` Header wird gelesen
- [ ] Fehlermeldungen zeigen Ursache (OSRM/DB/Validation)

**Prüfung:**
1. Öffne Network-Tab
2. Führe Optimierung aus
3. Prüfe Response-Header: `X-Request-ID`
4. Prüfe Response-Body: `trace_id`

---

### 8. UI-Feedback
- [ ] Fehlermeldungen sind benutzerfreundlich
- [ ] Trace-ID wird nicht zu technisch angezeigt
- [ ] Status-Updates sind klar
- [ ] Keine "500 Internal Server Error" ohne Kontext

**Prüfung:**
1. Führe Optimierung aus
2. Prüfe UI-Meldungen
3. Prüfe: Keine kryptischen Fehler mehr

---

## 🧪 Test-Checks

### 9. Unit Tests
- [ ] Alle Tests laufen durch: `pytest tests/test_subroutes_500_fix.py -v`
- [ ] Keine Mockups verwendet
- [ ] Tests decken alle Szenarien ab
- [ ] Tests sind reproduzierbar

**Prüfung:**
```bash
pytest tests/test_subroutes_500_fix.py -v
# Erwartet: Alle Tests grün
```

---

### 10. Integration Tests
- [ ] Echte Touren können optimiert werden
- [ ] Fallback funktioniert bei OSRM-Down
- [ ] Validation funktioniert bei ungültigen Requests
- [ ] Trace-ID ist immer vorhanden

**Prüfung:**
1. Lade echte CSV
2. Führe Optimierung aus
3. Prüfe: Keine 500er, Trace-ID vorhanden

---

## 🔍 Logging-Checks

### 11. Strukturierte Logs
- [ ] Logs enthalten `trace_id`
- [ ] Logs enthalten `path`, `method`, `error_type`
- [ ] Logs sind lesbar
- [ ] Keine sensiblen Daten in Logs

**Prüfung:**
```bash
# Prüfe Server-Logs
# Suche nach: [TOUR-OPTIMIZE] ... trace_id: ...
```

---

### 12. Error-Tracking
- [ ] Alle Fehler werden geloggt
- [ ] Trace-ID kann für Support verwendet werden
- [ ] Logs sind durchsuchbar
- [ ] Keine Duplikate

**Prüfung:**
1. Führe Optimierung mit Fehler aus
2. Prüfe Logs: Trace-ID vorhanden
3. Suche nach Trace-ID: Sollte alle relevanten Logs finden

---

## 🚀 Performance-Checks

### 13. Middleware-Performance
- [ ] Trace-ID-Generierung ist schnell (<1ms)
- [ ] Error Envelope fügt keine merkliche Latenz hinzu
- [ ] Validation ist schnell (<10ms)
- [ ] Keine Performance-Regression

**Prüfung:**
```bash
# Benchmark vor/nach Fix
time curl -X POST http://localhost:8111/api/tour/optimize ...
```

---

### 14. OSRM Health Check Performance
- [ ] Health Check ist schnell (<5s)
- [ ] Timeout funktioniert korrekt
- [ ] Keine Blocking-Requests
- [ ] Health Check kann parallel ausgeführt werden

**Prüfung:**
```bash
time curl http://localhost:8111/health/osrm
# Erwartet: <5s
```

---

## 🔒 Sicherheits-Checks

### 15. Input Validation
- [ ] SQL-Injection-Schutz (Pydantic)
- [ ] XSS-Schutz (Encoding)
- [ ] Keine sensiblen Daten in Logs
- [ ] Trace-ID enthält keine sensiblen Daten

**Prüfung:**
1. Teste mit bösartigen Inputs
2. Prüfe: Keine SQL-Injection möglich
3. Prüfe: Keine XSS möglich

---

### 16. Error Information Disclosure
- [ ] Fehlermeldungen sind nicht zu detailliert
- [ ] Keine Stack-Traces im Frontend
- [ ] Trace-ID ist sicher (keine sensiblen Daten)
- [ ] Logs sind geschützt

**Prüfung:**
1. Führe Optimierung mit Fehler aus
2. Prüfe Response: Keine Stack-Traces
3. Prüfe: Fehlermeldungen sind benutzerfreundlich

---

## 📊 Monitoring-Checks

### 17. Health-Endpoints
- [ ] `/health/osrm` funktioniert
- [ ] `/health/db` funktioniert
- [ ] `/health/app` funktioniert
- [ ] Alle Health-Checks sind schnell

**Prüfung:**
```bash
curl http://localhost:8111/health/osrm
curl http://localhost:8111/health/db
curl http://localhost:8111/health/app
# Erwartet: Alle 200 oder 503 (nicht 500)
```

---

### 18. Metrics
- [ ] Trace-ID kann für Request-Tracking verwendet werden
- [ ] Fehlerrate kann gemessen werden
- [ ] Latenz kann gemessen werden
- [ ] Keine Metrics-Regression

**Prüfung:**
1. Führe mehrere Optimierungen aus
2. Prüfe: Trace-ID ist eindeutig
3. Prüfe: Keine Duplikate

---

## 🔄 Rollback-Checks

### 19. Rollback-Fähigkeit
- [ ] Middlewares können deaktiviert werden
- [ ] Validation kann deaktiviert werden
- [ ] Alte Logik funktioniert noch
- [ ] Rollback ist dokumentiert

**Prüfung:**
1. Deaktiviere Middlewares
2. Prüfe: Server startet noch
3. Prüfe: Alte Logik funktioniert

---

### 20. Kompatibilität
- [ ] Alte Clients funktionieren noch
- [ ] Neue Features sind abwärtskompatibel
- [ ] Keine Breaking Changes
- [ ] Migration ist einfach

**Prüfung:**
1. Teste mit altem Frontend
2. Prüfe: Keine Breaking Changes
3. Prüfe: Abwärtskompatibilität

---

## 📝 Dokumentation-Checks

### 21. Code-Dokumentation
- [ ] Middlewares sind dokumentiert
- [ ] Schemas sind dokumentiert
- [ ] Endpoints sind dokumentiert
- [ ] Tests sind dokumentiert

**Prüfung:**
1. Prüfe Code-Kommentare
2. Prüfe Docstrings
3. Prüfe README

---

### 22. User-Dokumentation
- [ ] Fehlermeldungen sind verständlich
- [ ] Trace-ID ist erklärt
- [ ] Support-Informationen sind verfügbar
- [ ] Troubleshooting-Guide existiert

**Prüfung:**
1. Prüfe UI-Meldungen
2. Prüfe: Benutzer verstehen Fehler
3. Prüfe: Support kann helfen

---

## ✅ Zusammenfassung

**Kritisch (muss vor Deployment):**
- [ ] Middleware-Registrierung
- [ ] Request Validation
- [ ] Exception Handling
- [ ] Tests laufen durch

**Wichtig (sollte vor Deployment):**
- [ ] Frontend Fehleranzeige
- [ ] OSRM Health Check
- [ ] Logging
- [ ] Performance

**Optional (kann nach Deployment):**
- [ ] Monitoring
- [ ] Dokumentation
- [ ] Rollback-Tests

---

**Status:** 🔍 Zu prüfen  
**Nächster Schritt:** Systematisch durch Checkliste gehen

