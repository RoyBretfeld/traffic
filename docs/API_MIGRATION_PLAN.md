# API-Migration Plan: /api/admin/* Bündelung

**Datum:** 2025-11-22  
**Status:** In Planung

---

## Problem

Die Admin-Router haben bereits eigene Prefixes:
- `/api/tourplan/batch-geocode`
- `/api/db/stats`
- `/api/backup/create`
- `/api/upload/csv`
- `/api/system/rules`

Wenn wir sie unter `/api/admin` bündeln, entstehen doppelte Prefixes:
- ❌ `/api/admin/api/tourplan/batch-geocode` (falsch)

---

## Lösung: Schrittweise Migration

### Phase 1: Backward Compatibility (JETZT)

**Strategie:** Router bleiben wie bisher, zusätzlich unter `/api/admin` registriert

**Implementierung:**
1. Router behalten ihre Prefixes
2. Zusätzliche Registrierung unter `/api/admin` mit angepassten Pfaden
3. Alte URLs funktionieren weiter
4. Neue URLs werden parallel unterstützt

**Beispiel:**
- Alt: `/api/tourplan/batch-geocode` ✅ (weiterhin funktional)
- Neu: `/api/admin/tourplan/batch-geocode` ✅ (neue Struktur)

### Phase 2: Frontend-Migration (Später)

1. Frontend-URLs schrittweise auf `/api/admin/*` umstellen
2. Alte URLs als Deprecated markieren
3. Nach vollständiger Migration: Alte URLs entfernen

---

## Betroffene Endpoints

### db_management_api.py
- `/api/tourplan/batch-geocode` → `/api/admin/tourplan/batch-geocode`
- `/api/tourplan/geocode-file` → `/api/admin/tourplan/geocode-file`
- `/api/db/stats` → `/api/admin/db/stats`
- `/api/db/info` → `/api/admin/db/info`
- `/api/db/tables` → `/api/admin/db/tables`
- `/api/db/table/{name}` → `/api/admin/db/table/{name}`
- `/api/db/list` → `/api/admin/db/list`

### backup_api.py
- `/api/backup/create` → `/api/admin/backup/create`

### upload_csv.py
- `/api/upload/csv` → `/api/admin/upload/csv`
- `/api/process-csv-direct` → `/api/admin/process-csv-direct`

### system_rules_api.py
- `/api/system/rules` → `/api/admin/system/rules`

### tour_filter_api.py
- `/api/tour-filter/*` → `/api/admin/tour-filter/*`

### tour_import_api.py
- `/api/tour-import/*` → `/api/admin/tour-import/*`

---

## Frontend-Anpassungen (später)

**Betroffene Dateien:**
- `frontend/admin.html` (17 Stellen)
- `frontend/index.html` (1 Stelle)
- `frontend/admin/tour-import.html` (2 Stellen)

**Migration:**
```javascript
// Alt
fetch('/api/tourplan/batch-geocode', ...)

// Neu
fetch('/api/admin/tourplan/batch-geocode', ...)
```

---

## Entscheidung

**Empfehlung:** Phase 1 jetzt implementieren (Backward Compatibility), Phase 2 später.

**Vorteile:**
- ✅ Keine Breaking Changes
- ✅ Schrittweise Migration möglich
- ✅ Frontend kann später angepasst werden
- ✅ Alte URLs funktionieren weiter

**Nachteile:**
- ⚠️ Doppelte Registrierung (minimaler Overhead)
- ⚠️ Zwei URL-Pfade für dieselbe Funktion

---

**Status:** Warte auf Bestätigung

