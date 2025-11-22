# Code Patterns – TrafficApp 3.0

**Zweck:** Do's und Don'ts für konsistenten, sicheren Code. Wird von KI-Code-Review verwendet.

**Status:** Aktiv

---

## ✅ DO's (Best Practices)

### 1. Defensive Programmierung
```python
# ✅ GUT: Null-Checks, Type-Checks, Array-Checks
if not address or not isinstance(address, str):
    raise ValueError("Address must be a non-empty string")

if not coordinates or len(coordinates) < 2:
    raise ValueError("Coordinates must have at least 2 values")
```

### 2. Input Validation
```python
# ✅ GUT: Pydantic-Models mit Limits
class TourRequest(BaseModel):
    stops: List[Stop] = Field(..., min_items=1, max_items=100)
    max_distance_km: float = Field(..., ge=0, le=1000)
```

### 3. Error Handling
```python
# ✅ GUT: Spezifische Exceptions, Trace-IDs
try:
    result = geocode_address(address)
except GeocodingError as e:
    logger.error(f"Geocoding failed: {e}", extra={"trace_id": trace_id})
    raise HTTPException(500, detail="Geocoding failed")
```

### 4. Security Headers
```python
# ✅ GUT: Security-Header in Middleware
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-Content-Type-Options"] = "nosniff"
```

### 5. Upload Security
```python
# ✅ GUT: Filename-Whitelist + resolve()
SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_.\-]+$")
if not SAFE_FILENAME.match(filename):
    raise HTTPException(400, "Invalid filename")

file_path = (UPLOAD_DIR / filename).resolve()
if not str(file_path).startswith(str(UPLOAD_DIR.resolve())):
    raise HTTPException(400, "Path traversal detected")
```

---

## ❌ DON'Ts (Anti-Patterns)

### 1. Keine Null-Checks
```python
# ❌ SCHLECHT: Keine Validierung
def process_tour(tour):
    return tour.stops[0].address  # Kann None sein!
```

### 2. Unsichere Uploads
```python
# ❌ SCHLECHT: Keine Validierung
file_path = UPLOAD_DIR / filename  # Path Traversal möglich!
```

### 3. Hardcoded Secrets
```python
# ❌ SCHLECHT: Secrets im Code
API_KEY = "sk-1234567890"  # Nie im Code!
```

### 4. Unsichere CORS
```python
# ❌ SCHLECHT: CORS zu offen
app.add_middleware(CORSMiddleware, allow_origins=["*"])  # Mit Credentials unsicher!
```

### 5. Keine Rate-Limits
```python
# ❌ SCHLECHT: Keine Drosselung
@router.post("/api/import")
async def import_tours():  # Kann überlastet werden!
```

---

## 🔒 Security Patterns (SC-Checklist)

### SC-01: Keine Default-Credentials
```python
# ✅ GUT
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD")
if not MASTER_PASSWORD:
    raise ValueError("MASTER_PASSWORD must be set")
```

### SC-02: Passwort-Hashing
```python
# ✅ GUT: bcrypt
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
bcrypt.checkpw(password.encode(), hashed)
```

### SC-03: Sichere Cookies
```python
# ✅ GUT
response.set_cookie(
    "session_id",
    value=session_id,
    httponly=True,
    secure=is_production,
    samesite="strict"
)
```

### SC-05: Admin-Auth
```python
# ✅ GUT
@router.post("/api/admin/import")
async def admin_import(session: dict = Depends(require_admin)):
    ...
```

### SC-07: Upload-Schutz
```python
# ✅ GUT: Siehe Upload Security oben
```

---

## 📐 Admin-Navigation Pattern

### ✅ GUT: Eine Seite mit Tabs
```html
<!-- admin.html -->
<div class="tab-pane fade" id="tourplan" role="tabpanel">
    <!-- Tourplan-Inhalt -->
</div>
```

### ❌ SCHLECHT: Separate Seiten
```html
<!-- admin/tourplan-uebersicht.html --> ❌ Separate Seite
```

**Regel:** Alle Admin-Module als Tabs in `admin.html` integrieren.

---

## 🎯 Kosten & Stats Patterns

### ✅ GUT: Materialisierte Aggregationen
```python
# stats_daily Tabelle füllen (täglich)
def aggregate_daily_stats(date: str):
    # Aggregiere aus tours/tour_stops
    # Speichere in stats_daily
```

### ❌ SCHLECHT: Direkte DB-Abfragen im Frontend
```python
# Frontend sollte stats_daily nutzen, nicht tours direkt
```

---

## 🔄 Error-Pattern-Aggregation

### ✅ GUT: Strukturierte Fehler-Logs
```python
logger.error(
    "Geocoding failed",
    extra={
        "address": address[:50],  # PII-reduziert
        "error_type": type(e).__name__,
        "trace_id": trace_id
    }
)
```

---

## 📝 Naming Conventions

- **Router:** `*_router` oder `*_api_router`
- **Services:** `*_service.py` oder direkter Funktionsname
- **Models:** PascalCase (`TourRequest`, `StopResponse`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_UPLOAD_BYTES`)

---

**Letzte Aktualisierung:** 2025-11-22

