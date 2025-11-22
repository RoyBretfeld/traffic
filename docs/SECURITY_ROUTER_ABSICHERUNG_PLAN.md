# Security: Router-Absicherung Plan

**Datum:** 2025-11-22  
**Status:** 📋 **Planung**

---

## 🎯 Ziel

Alle Admin-Router mit `Depends(require_admin)` absichern, **OHNE** etwas kaputt zu machen.

---

## 📋 Zu absichernde Router

### 1. `backend/routes/db_management_api.py`

**Endpoints:**
- [x] `/api/tourplan/batch-geocode` (POST) - **BEREITS GESCHÜTZT**
- [ ] `/api/tourplan/list-legacy` (GET) - **ZU ABSICHERN**
- [ ] `/api/tourplan/geocode-file` (POST) - **ZU ABSICHERN**
- [ ] `/api/db/info` (GET) - **ZU ABSICHERN**
- [ ] `/api/db/tables` (GET) - **ZU ABSICHERN**
- [ ] `/api/db/table/{table_name}` (GET) - **ZU ABSICHERN**
- [ ] `/api/db/stats` (GET) - **ZU ABSICHERN**

**Status:** 1/7 geschützt

---

### 2. `backend/routes/test_dashboard_api.py`

**Endpoints:**
- [ ] `/api/tests/status` (GET) - **ZU ABSICHERN**
- [ ] `/api/tests/modules` (GET) - **ZU ABSICHERN**
- [ ] `/api/tests/list` (GET) - **ZU ABSICHERN**
- [ ] `/api/tests/run` (POST) - **ZU ABSICHERN**

**Zusätzlich:** Router sollte nur mit `ENABLE_DEBUG_ROUTES=1` aktiv sein.

**Status:** 0/4 geschützt

---

### 3. `backend/routes/code_checker_api.py`

**Endpoints:**
- [ ] `/api/code-checker/analyze` (POST) - **ZU ABSICHERN**
- [ ] `/api/code-checker/learned-patterns` (GET) - **ZU ABSICHERN**
- [ ] `/api/code-checker/reload-patterns` (POST) - **ZU ABSICHERN**
- [ ] `/api/code-checker/add-lesson` (POST) - **ZU ABSICHERN**

**Zusätzlich:** Router sollte nur mit `ENABLE_DEBUG_ROUTES=1` aktiv sein.

**Status:** 0/4 geschützt

---

### 4. `backend/routes/upload_csv.py`

**Endpoints:**
- [ ] `/api/tourplaene/list` (GET) - **ZU PRÜFEN** (vielleicht öffentlich?)
- [ ] `/api/process-csv-direct` (POST) - **ZU ABSICHERN**
- [ ] `/api/upload/csv` (POST) - **ZU ABSICHERN**
- [ ] `/api/upload/status` (GET) - **ZU ABSICHERN**

**Zusätzlich:** Upload-Sicherheit (Filename-Whitelist, Pfad-Check) implementieren.

**Status:** 0/4 geschützt

---

### 5. `backend/routes/backup_api.py`

**Endpoints:**
- [ ] Alle Endpoints - **ZU PRÜFEN**

**Status:** Zu prüfen

---

### 6. `backend/routes/system_rules_api.py`

**Endpoints:**
- [ ] Alle Endpoints - **ZU PRÜFEN**

**Status:** Zu prüfen

---

## ⚠️ WICHTIG: Vorsichtige Umsetzung

### Schritt 1: Backup erstellen
```bash
git add -A
git commit -m "Backup vor Router-Absicherung"
```

### Schritt 2: Router einzeln absichern
- **Nur einen Router pro Commit**
- **Nach jedem Router: Tests ausführen**
- **Server starten und prüfen**

### Schritt 3: Test-Plan
1. Server starten
2. Login testen
3. Jeden Endpoint testen (mit und ohne Auth)
4. Prüfen ob normale Funktionen noch funktionieren

---

## 🔧 Implementierungs-Pattern

### Pattern 1: Einzelner Endpoint

```python
from fastapi import Depends, Request
from backend.routes.auth_api import require_admin

@router.get("/api/endpoint")
async def my_endpoint(session: dict = Depends(require_admin)):
    # Endpoint-Logik
    pass
```

### Pattern 2: Router-Level (alle Endpoints)

```python
from fastapi import APIRouter, Depends
from backend.routes.auth_api import require_admin

router = APIRouter(
    prefix="/api/admin",
    dependencies=[Depends(require_admin)]  # Alle Endpoints geschützt
)
```

### Pattern 3: Debug-Router (nur mit Flag)

```python
# In app_setup.py
ENABLE_DEBUG_ROUTES = os.getenv("ENABLE_DEBUG_ROUTES", "0") == "1"
if ENABLE_DEBUG_ROUTES:
    app.include_router(
        test_dashboard_router,
        dependencies=[Depends(require_admin)]  # Zusätzlich Admin-Auth
    )
```

---

## ✅ Test-Checkliste

Nach jeder Änderung:

- [ ] Server startet ohne Fehler
- [ ] Login funktioniert
- [ ] Endpoint ohne Auth → 401/403
- [ ] Endpoint mit Auth → funktioniert
- [ ] Normale Funktionen (nicht-Admin) funktionieren weiterhin

---

## 📊 Fortschritt

**Gesamt:** 0/20+ Endpoints geschützt

**Nächster Schritt:** Router einzeln absichern und testen

---

**WICHTIG:** Nichts kaputt machen! Immer testen nach jeder Änderung!

