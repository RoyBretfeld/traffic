# Fix 404/402/500 Routing & Health (Minimal-Patches)
**Datum:** 2025-01-10  
**Status:** ✅ IMPLEMENTIERT

---

## ✅ Implementierte Fixes

### 1. Backend: Globaler 500-Handler
- ✅ `backend/app.py`: Globaler Exception-Handler hinzugefügt
- ✅ Strukturierte 500-Antworten mit Trace-ID
- ✅ Fängt alle unhandled Exceptions ab

### 2. Backend: Health-Checks vereinfacht
- ✅ `routes/health_check.py`: DB-Health vereinfacht (nur SELECT 1)
- ✅ `routes/health_check.py`: OSRM-Health vereinfacht (kurzer nearest-Call)
- ✅ Robuste Fehlerbehandlung

### 3. Frontend: Upload→Match-Vertrag korrigiert
- ✅ `frontend/index.html`: `apiUploadCsv` - kein doppeltes Lesen
- ✅ `frontend/index.html`: `loadMatchForFile` - kein doppeltes Lesen
- ✅ `stored_path` als vereinheitlichtes Feld
- ✅ URL-Encoding für file-Parameter

### 4. Frontend: OSRM-Badge
- ✅ `frontend/index.html`: `refreshOsrmBadge()` Funktion
- ✅ Automatische Aktualisierung beim Laden
- ✅ Online/Offline-Status-Anzeige

---

## 📋 Änderungen im Detail

### Backend (`backend/app.py`)
```python
# Globaler 500-Handler
@app.exception_handler(Exception)
async def global_500_handler(req: Request, exc: Exception):
    trace_id = uuid.uuid4().hex[:8]
    return JSONResponse(
        {"error": "internal", "trace_id": trace_id, "detail": str(exc)},
        status_code=500
    )
```

### Health-Checks (`routes/health_check.py`)
```python
# DB-Health: Einfach & robust
@router.get("/health/db")
async def health_db():
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return JSONResponse({"ok": True}, status_code=200)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=503)

# OSRM-Health: Kurzer Health-Call
@router.get("/health/osrm")
async def health_osrm():
    url = os.getenv("OSRM_URL", "") or cfg("osrm:base_url", "http://localhost:5000")
    if not url:
        return JSONResponse({"ok": False, "reason": "no_osrm_url"}, status_code=503)
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            r = await client.get(f"{url}/nearest/v1/driving/13.7373,51.0504")
            return JSONResponse({"ok": r.status_code == 200}, status_code=200)
    except Exception:
        return JSONResponse({"ok": False}, status_code=503)
```

### Frontend (`frontend/index.html`)
```javascript
// Upload: Nur einmal lesen
async function apiUploadCsv(file) {
    const response = await fetch('/api/upload/csv', {method: 'POST', body: formData});
    if (!response.ok) throw new Error(`Upload fehlgeschlagen: ${response.status}`);
    const data = await response.json(); // Nur einmal lesen
    const p = data?.stored_path;
    if (!p) throw new Error('Upload response missing stored_path');
    return data;
}

// Match: Nur einmal lesen + URL-Encoding
async function loadMatchForFile(filePath) {
    const r = await fetch(`/api/tourplan/match?file=${encodeURIComponent(pathToUse)}`);
    if (!r.ok) throw new Error(`match failed ${r.status}`);
    const matchData = await r.json(); // Nur einmal lesen
    // ...
}

// OSRM-Badge
async function refreshOsrmBadge() {
    try {
        const r = await fetch('/health/osrm');
        const j = await r.json();
        setBadge('osrm', j.ok ? 'online' : 'offline');
    } catch {
        setBadge('osrm', 'offline');
    }
}
```

---

## 🧪 Smoke-Tests

```bash
# Backend Health-Checks
curl -sf http://localhost:8111/health/db
curl -sf http://localhost:8111/health/osrm

# Upload & Match
curl -sf -F file=@samples/tourplan.csv http://localhost:8111/api/upload/csv
curl -sf "http://localhost:8111/api/tourplan/match?file=/staging/XYZ.csv"
```

---

## 📝 HTTP-Code-Policy

- ✅ **Kein 402 mehr**: Für "fehlender Input/Precondition" → `422` oder `400`
- ✅ **500 nur bei echten Serverfehlern**: Strukturierte Antworten mit Trace-ID
- ✅ **503 für Service-Probleme**: DB/OSRM offline → 503

---

## ✅ Status

**Alle Fixes implementiert:**
- ✅ Globaler 500-Handler
- ✅ Health-Checks vereinfacht
- ✅ Upload→Match-Vertrag korrigiert
- ✅ OSRM-Badge hinzugefügt

**Bereit für Tests!** 🎉

