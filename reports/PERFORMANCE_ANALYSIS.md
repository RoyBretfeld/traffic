# ⚡ PERFORMANCE-ANALYSE

**Datum:** 2025-11-13  
**Umfang:** Backend-Codebase (Routes, Services, Utils)  
**Fokus:** Bottlenecks, ineffiziente Queries, Memory-Leaks

---

## 📊 EXECUTIVE SUMMARY

### Performance-Score: **6/10** (Verbesserungspotenzial vorhanden)

**Hauptprobleme:**
- 🔴 `workflow_api.py`: 2568 Zeilen (Monolith-File)
- 🟡 Nested Loops in `optimize_tour_with_ai`
- 🟡 Blocking `time.sleep()` in async context
- 🟡 Keine Caching-Strategy für häufige Queries

**Positiv:**
- ✅ Database Connection-Pooling (SQLAlchemy)
- ✅ Async/Await für I/O-Operations
- ✅ Circuit-Breaker für externe Services

---

## 🔍 DETAILLIERTE FINDINGS

### 🔴 CRITICAL: workflow_api.py ist zu groß (2568 Zeilen)

**Datei:** `backend/routes/workflow_api.py`  
**Problem:** MONOLITH-FILE  
**Impact:** 
- Schwer zu warten
- Lange Compile-Zeit
- Merge-Konflikte wahrscheinlich
- Schwierige Code-Navigation

**Empfohlene Refactoring-Strategie:**

```
backend/routes/
├── workflow_api.py (200 Zeilen - nur Router-Registration)
├── workflow/
│   ├── __init__.py
│   ├── upload.py (File-Upload-Logic)
│   ├── optimize.py (Tour-Optimization)
│   ├── classify.py (AI-Classification)
│   ├── group.py (Tour-Grouping)
│   └── helpers.py (Shared utilities)
```

**Aufwand:** 8-12 Stunden  
**Priorität:** 🔴 HOCH (Maintainability)

---

### 🟡 MEDIUM: Blocking time.sleep() in Async Context

**Dateien gefunden:**
- `backend/routes/workflow_api.py`
- `backend/routes/tourplan_geofill.py`
- `backend/services/geocode.py`

**Problem:**
```python
# ❌ BLOCKING in async function
async def some_function():
    time.sleep(1.0)  # Blockiert gesamten Event-Loop!
```

**Warum ist das ein Problem?**
- `time.sleep()` blockiert den gesamten Event-Loop
- Alle anderen Requests müssen warten
- Performance-Degradation unter Last

**Richtig:**
```python
# ✅ Non-blocking
import asyncio

async def some_function():
    await asyncio.sleep(1.0)  # Gibt Event-Loop frei
```

**Gefundene Stellen:**
1. `workflow_api.py:1179, 1197` - File-Handle-Wait (0.2s)
2. `workflow_api.py:1480` - Cleanup-Retry (0.2s)
3. `tourplan_geofill.py:115` - Rate-Limiting (1.0s)

**Fix:**
```python
# VORHER:
time.sleep(0.2)

# NACHHER:
await asyncio.sleep(0.2)
```

**Aufwand:** 1-2 Stunden  
**Priorität:** 🟡 MITTEL

---

### 🟡 MEDIUM: Nested Loops in Tour-Optimization

**Datei:** `backend/routes/workflow_api.py`  
**Funktion:** `optimize_tour_with_ai` (und Helfer)  
**Geschätzter Count:** 47 nested loops

**Problem:**
Viele nested loops → O(n²) oder O(n³) Komplexität

**Kritische Stellen:**
1. Sub-Tour-Splitting-Logic
2. Time-Calculation für Stops
3. Koordinaten-Validierung

**Beispiel (schematisch):**
```python
for tour in tours:  # O(n)
    for stop in tour['stops']:  # O(m)
        for validation in validations:  # O(k)
            # ... → O(n*m*k)
```

**Empfohlene Optimierungen:**
1. **Batch-Processing:** Gruppiere ähnliche Operations
2. **Caching:** Wiederholte Berechnungen cachen
3. **Vectorization:** NumPy für numerische Operations
4. **Early-Exit:** Breche ab wenn Bedingung erfüllt

**Aufwand:** 4-6 Stunden (pro kritischer Stelle)  
**Priorität:** 🟡 MITTEL

---

### 🟡 LOW: Keine Caching-Strategy für häufige Queries

**Problem:**
Keine explizite Caching-Layer für:
- System-Rules (werden bei jedem Request neu geladen)
- Geocoding-Results (nur DB-Cache, kein In-Memory)
- OSRM-Routes (keine Cache-Strategy)

**Empfohlene Lösung:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

# 1. In-Memory-Cache für System-Rules
@lru_cache(maxsize=1)
def get_cached_system_rules(cache_key: str):
    return load_system_rules()

def get_system_rules_with_ttl():
    # Cache-Key ändert sich alle 5 Minuten
    cache_key = datetime.now().strftime("%Y-%m-%d-%H-%M")[:-1]  # Runde auf 10 Min
    return get_cached_system_rules(cache_key)

# 2. Redis-Cache für Geocoding (Optional)
import redis
redis_client = redis.Redis(host='localhost', port=6379)

def geocode_with_cache(address: str):
    # Prüfe Redis-Cache
    cached = redis_client.get(f"geo:{address}")
    if cached:
        return json.loads(cached)
    
    # Geocode und cache
    result = geocode_address(address)
    redis_client.setex(f"geo:{address}", 86400, json.dumps(result))  # 24h TTL
    return result
```

**Aufwand:** 3-4 Stunden  
**Priorität:** 🟢 NIEDRIG (Nice-to-have)

---

### 🟢 LOW: File-Logger schreibt synchron

**Datei:** `backend/utils/file_logger.py`  
**Zeilen:** 30-34

**Problem:**
```python
with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
    safe_message = message.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    f.write(f"[{timestamp}] {safe_message}\n")
    f.flush()  # Synchrones I/O
```

**Warum ist das ein Problem?**
- Synchrones Disk-I/O blockiert kurzzeitig
- Bei vielen Logs: Performance-Impact

**Impact:** Niedrig (wenige ms pro Log)

**Empfohlene Lösung (Optional):**
```python
import aiofiles

async def log_to_file_async(*args):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    message = " ".join(str(arg) for arg in args)
    
    async with aiofiles.open(LOG_FILE, "a", encoding="utf-8") as f:
        await f.write(f"[{timestamp}] {message}\n")
        await f.flush()
```

**Aufwand:** 2-3 Stunden  
**Priorität:** 🟢 NIEDRIG

---

## ✅ GOOD PRACTICES ERKANNT

### Performance-Maßnahmen die GUT sind:

1. **✅ Async/Await für I/O**
   - HTTPClient-Requests sind async
   - Database-Queries nutzen SQLAlchemy async (teilweise)

2. **✅ Connection-Pooling**
   - SQLAlchemy ENGINE mit Connection-Pooling
   - Wiederverwendung von DB-Connections

3. **✅ Circuit-Breaker für OSRM**
   - Verhindert Service-Overload
   - Schnelle Fehler-Erkennung

4. **✅ Timeouts für externe Services**
   - OSRM: 3s/5s/10s (je nach Operation)
   - Geocoding: 20s
   - Verhindert Hanging-Requests

5. **✅ Batch-Geocoding**
   - `_geocode_missing_new` verarbeitet mehrere Adressen
   - Rate-Limiting integriert

6. **✅ Database-Indizes**
   - `db/schema.py` definiert Indizes für häufige Queries
   - Z.B. `idx_system_rules_audit_changed_at`

7. **✅ Pagination für große Resultsets**
   - `limit` Parameter in vielen Endpoints
   - Verhindert Memory-Overload

---

## 📋 EMPFOHLENE OPTIMIERUNGEN (PRIORISIERT)

### Sofort (Diese Woche)
1. 🟡 **Ersetze `time.sleep()` mit `asyncio.sleep()`** (1-2h)
2. 🟢 **Füge Logging-Level-Filter hinzu** (reduziere Debug-Logs in Produktion)

### Kurzfristig (Nächste 2 Wochen)
3. 🔴 **Refactoring: workflow_api.py aufteilen** (8-12h)
4. 🟡 **Optimiere nested loops in Tour-Optimization** (4-6h)

### Mittelfristig (Nächster Monat)
5. 🟡 **Implementiere Caching-Layer (Redis)** (6-8h)
6. 🟢 **Async File-Logging** (2-3h)
7. 🟢 **Database-Query-Profiling** (Analyse langsamer Queries)

---

## 🧪 PERFORMANCE-TESTS EMPFOHLEN

1. **Load-Testing:** `locust` oder `k6` für API-Endpoints
2. **Profiling:** `cProfile` für CPU-intensive Funktionen
3. **Memory-Profiling:** `memory_profiler` für Memory-Leaks
4. **Database-Profiling:** SQLAlchemy Query-Logging aktivieren

**Beispiel (Load-Test):**
```python
# locustfile.py
from locust import HttpUser, task, between

class TrafficAppUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def optimize_tour(self):
        self.client.post("/api/tour/optimize", json={
            "tour_id": "test-tour",
            "stops": [...]  # Test-Daten
        })
    
    @task(2)  # 2x häufiger als optimize
    def health_check(self):
        self.client.get("/health/status")
```

Ausführen:
```bash
locust -f locustfile.py --host=http://localhost:8111
```

---

## 📊 ZUSAMMENFASSUNG

### Performance-Bottlenecks

| Bottleneck | Impact | Aufwand | Priorität |
|------------|--------|---------|-----------|
| workflow_api.py Größe | HOCH | 8-12h | 🔴 |
| Blocking sleep() | MITTEL | 1-2h | 🟡 |
| Nested Loops | MITTEL | 4-6h | 🟡 |
| Keine Caching-Strategy | NIEDRIG | 3-4h | 🟢 |
| Sync File-Logging | NIEDRIG | 2-3h | 🟢 |

### Geschätzter Gesamt-Aufwand: 18-27 Stunden

### ROI-Bewertung
**MITTEL-HOCH:** Die größten Gains kommen von:
1. Refactoring (Maintainability)
2. Async-Fixes (Responsiveness unter Last)
3. Loop-Optimierungen (Skalierbarkeit)

---

**Erstellt:** 2025-11-13  
**Status:** Abgeschlossen  
**Nächste Schritte:** Implementierung der Hochprioritäts-Fixes

