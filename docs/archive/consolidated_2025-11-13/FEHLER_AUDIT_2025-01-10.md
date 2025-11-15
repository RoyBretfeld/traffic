# Fehler-Audit: Aktuelle Probleme
**Datum:** 2025-01-10  
**Status:** 🔍 In Prüfung

---

## 🔴 Kritische Fehler

### 1. `/health/osrm` gibt 404 zurück
**Symptom:**
- `curl http://localhost:8111/health/osrm` → `{"detail":"Not Found"}`
- Frontend kann OSRM-Status nicht prüfen
- Status-Indikator bleibt gelb/rot

**Ursache:**
- Router möglicherweise nicht korrekt registriert
- Endpoint existiert in `routes/health_check.py` (Zeile 52)
- Router wird in `backend/app.py` registriert (Zeile 104)

**Fix-Status:** ⚠️ Muss geprüft werden

---

### 2. `/api/ki-improvements/stats` gibt 404 zurück (bei curl)
**Symptom:**
- `curl http://localhost:8111/api/ki-improvements/stats` → `{"detail":"Not Found"}`
- **ABER:** Server-Logs zeigen 200 OK für Browser-Requests

**Ursache:**
- Router ist registriert (`backend/app.py` Zeile 115)
- Endpoint existiert (`routes/ki_improvements_api.py` Zeile 23)
- Möglicherweise CORS-Problem oder Router-Loading-Problem

**Fix-Status:** ⚠️ Inkonsistent - funktioniert im Browser, nicht bei curl

---

### 3. `/api/code-checker/status` gibt 404 zurück
**Symptom:**
- `curl http://localhost:8111/api/code-checker/status` → `{"detail":"Not Found"}`

**Ursache:**
- Router ist registriert (`backend/app.py` Zeile 116)
- Endpoint existiert (`routes/code_checker_api.py` Zeile 14)

**Fix-Status:** ⚠️ Muss geprüft werden

---

### 4. `/api/code-improvement-job/status` gibt 404 zurück
**Symptom:**
- `curl http://localhost:8111/api/code-improvement-job/status` → `{"detail":"Not Found"}`

**Ursache:**
- Router ist registriert (`backend/app.py` Zeile 117)
- Endpoint existiert (`routes/code_improvement_job_api.py` Zeile 11)

**Fix-Status:** ⚠️ Muss geprüft werden

---

## ✅ Funktionierende Endpoints

### 1. `/health/db` → 200 OK
- Datenbank-Health-Check funktioniert
- Gibt korrekte Status-Informationen zurück

### 2. `/api/workflow/status` → 200 OK
- Workflow-Status-Endpoint funktioniert
- Gibt vollständige System-Informationen zurück

### 3. `/api/upload/status` → 200 OK
- Upload-Status-Endpoint funktioniert
- Zeigt 150 Staging-Dateien (möglicherweise Cleanup nötig)

---

## 🔍 Mögliche Ursachen

### 1. Router-Registrierung
- Router werden in `backend/app.py` registriert
- Möglicherweise werden Router nicht korrekt geladen
- Server muss möglicherweise neu gestartet werden (ohne `--reload`)

### 2. Hot-Reload-Problem
- Uvicorn mit `--reload` kann Router-Registrierung beeinträchtigen
- Lösung: Server ohne `--reload` starten oder Router-Registrierung prüfen

### 3. Import-Fehler
- Möglicherweise fehlende Imports in `backend/app.py`
- Prüfe Zeile 48: `from routes.code_checker_api import router as code_checker_api_router`

---

## 📋 Nächste Schritte

1. **Router-Registrierung prüfen**
   - Prüfe ob alle Router korrekt importiert werden
   - Prüfe ob Router ohne Prefix registriert sind

2. **Server-Neustart ohne --reload**
   - Starte Server ohne Hot-Reload
   - Prüfe ob Endpoints dann funktionieren

3. **OpenAPI-Schema prüfen**
   - Öffne http://localhost:8111/docs
   - Prüfe ob Endpoints in der Dokumentation erscheinen

4. **Staging-Dateien aufräumen**
   - 150 Dateien im Staging-Verzeichnis
   - Cleanup durchführen: `POST /api/upload/cleanup`

---

## 🔧 Empfohlene Fixes

### Fix 1: Router-Registrierung prüfen
```python
# backend/app.py
# Prüfe ob alle Router korrekt importiert werden
from routes.health_check import router as health_check_router
from routes.ki_improvements_api import router as ki_improvements_api_router
from routes.code_checker_api import router as code_checker_api_router
from routes.code_improvement_job_api import router as code_improvement_job_api_router

# Prüfe ob Router ohne Prefix registriert sind
app.include_router(health_check_router)  # Kein prefix
app.include_router(ki_improvements_api_router)  # Kein prefix
app.include_router(code_checker_api_router)  # Kein prefix
app.include_router(code_improvement_job_api_router)  # Kein prefix
```

### Fix 2: Server-Neustart
```bash
# Stoppe Server (Ctrl+C)
# Starte ohne --reload
python start_server.py
```

### Fix 3: Staging-Cleanup
```bash
curl -X POST http://localhost:8111/api/upload/cleanup
```

---

## 📊 Fehler-Statistik

- **Kritische Fehler:** 4
- **Funktionierende Endpoints:** 3
- **Inkonsistente Endpoints:** 1 (`/api/ki-improvements/stats`)

---

## 🎯 Priorität

1. **Hoch:** `/health/osrm` Fix (wichtig für Frontend-Status)
2. **Hoch:** Code-Checker Endpoints Fix (wichtig für KI-Funktionalität)
3. **Mittel:** Staging-Cleanup (150 Dateien)
4. **Niedrig:** Inkonsistenz bei `/api/ki-improvements/stats` (funktioniert im Browser)

