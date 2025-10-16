# Prompt 13 - Geocoding-Robustheit: Retry/Backoff + Fail-Cache

## Übersicht

Das Geocoding-System wurde um Retry/Backoff-Mechanismen und einen Fail-Cache erweitert, um es robuster gegen temporäre Fehler und Rate-Limiting zu machen.

## Implementierte Features

### ✅ **Fail-Cache Schema**

- **Tabelle**: `geo_fail` mit `address_norm`, `reason`, `until`, `updated_at`
- **TTL**: 1 Stunde für temporäre Fehler, 24 Stunden für No-Hit-Adressen
- **Idempotent**: Schema wird automatisch erstellt

### ✅ **Fail-Cache Repository**

- **`skip_set(addresses)`** - Gibt Adressen zurück, die aktuell im Fail-Cache stehen
- **`mark_temp(address, minutes, reason)`** - Markiert temporäre Fehler (1h TTL)
- **`mark_nohit(address, minutes, reason)`** - Markiert No-Hit-Adressen (24h TTL)
- **`clear(address)`** - Entfernt Adresse aus Fail-Cache (bei Erfolg)
- **`get_fail_stats()`** - Statistiken über Fail-Cache

### ✅ **Retry/Backoff-Mechanismen**

- **Max Retries**: 3 Versuche pro Adresse
- **Exponential Backoff**: 1s, 2s, 4s bei Timeout/Connection-Fehlern
- **429 Rate-Limiting**: Beachtet `Retry-After` Header von Nominatim
- **Timeout-Behandlung**: `ReadTimeout`, `ConnectTimeout`, `ConnectError`

### ✅ **Geocoding-Service-Erweiterungen**

- **Fail-Cache-Integration**: Überspringt Adressen im Fail-Cache
- **Status-Tracking**: `ok`, `nohit`, `error` Status für jede Adresse
- **Automatische Bereinigung**: Erfolgreiche Geocoding entfernt Fail-Einträge
- **Meta-Informationen**: Verarbeitungszeit, übersprungene Adressen

## Technische Details

### **Retry-Parameter**
```python
MAX_RETRIES = 3
BASE_SLEEP = 1.0  # Sekunden (exponentiell)
```

### **429 Rate-Limiting-Behandlung**
```python
if r.status_code == 429:
    ra = r.headers.get('Retry-After')
    delay = float(ra) if ra and ra.isdigit() else BASE_SLEEP * (2 ** (attempt - 1))
    await asyncio.sleep(delay)
    continue
```

### **Fail-Cache-Integration**
```python
# Fail-Cache ausschließen
skip = skip_set(unique)
todo = [a for a in unique if a not in skip][:max(0, int(limit))]

# Bei Erfolg: Fail-Eintrag löschen
if res and not dry_run:
    upsert(addr, res["lat"], res["lon"])
    clear(addr)  # ggf. Fail-Eintrag löschen

# Bei Fehler: Temporär markieren
except Exception as e:
    if not dry_run:
        mark_temp(addr, minutes=60, reason=type(e).__name__)
```

### **TTL-Konfiguration**
```python
_DEF_TTL_MIN = 60        # 1h für temporäre Fehler
_DEF_TTL_NOHIT_MIN = 24 * 60  # 24h für "keine Treffer"
```

## Verwendung

### **Automatische Integration**
Das robuste Geocoding wird automatisch verwendet, wenn `/api/tourplan/geocode-missing` aufgerufen wird.

### **Fail-Cache-Management**
```python
from repositories.geo_fail_repo import skip_set, mark_temp, mark_nohit, clear

# Adressen im Fail-Cache überspringen
skip_addresses = skip_set(["Adresse 1", "Adresse 2"])

# Temporären Fehler markieren
mark_temp("Problem-Adresse", minutes=60, reason="timeout")

# No-Hit markieren
mark_nohit("Nicht Existente Adresse", minutes=1440, reason="no_result")

# Bei Erfolg: Fail-Eintrag löschen
clear("Erfolgreiche Adresse")
```

## Akzeptanzkriterien

✅ **Retry mit Exponential Backoff** implementiert  
✅ **429/Retry-After** wird beachtet  
✅ **Fail-Cache** verhindert wiederholte Anfragen  
✅ **TTL**: 1h für temporäre Fehler, 24h für No-Hit  
✅ **Erfolgreiche Treffer** entfernen Fail-Einträge  
✅ **Bestehende Endpoints** bleiben unverändert  
✅ **Tests bestehen** (6/6 bestanden)  

## Test-Ergebnisse

```bash
tests/test_geocode_robust_simple.py::test_fail_cache_basic_functionality PASSED
tests/test_geocode_robust_simple.py::test_nohit_marking PASSED
tests/test_geocode_robust_simple.py::test_geocode_retry_basic PASSED
tests/test_geocode_robust_simple.py::test_geocode_429_handling PASSED
tests/test_geocode_robust_simple.py::test_geocode_timeout_handling PASSED
tests/test_geocode_robust_simple.py::test_geocode_nohit_handling PASSED
```

## Dateien

- **`db/schema_fail.py`** - Fail-Cache Schema
- **`repositories/geo_fail_repo.py`** - Fail-Cache Repository
- **`services/geocode_fill.py`** - Erweiterte Geocoding-Service
- **`app_startup.py`** - Schema-Initialisierung
- **`tests/test_geocode_robust_simple.py`** - Tests (6/6 bestanden)

## Git-Commit

**Branch:** `fix/encoding-unification`  
**Commit:** `263e822` - "feat: Prompt 13 - Geocoding-Robustheit: Retry/Backoff + Fail-Cache"
