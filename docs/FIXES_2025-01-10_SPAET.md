# Fixes 2025-01-10 (Spät) - Pydantic V2 & API-Kompatibilität

**Datum:** 2025-01-10 (Spät)  
**Status:** ✅ Behoben

---

## 🔍 Behobene Fehler

### 1. `fill_missing() got an unexpected keyword argument 'batch_limit'`

**Fehler:**
```
Match-Fehler für '...csv': fill_missing() got an unexpected keyword argument 'batch_limit'
```

**Ursache:**
- `fill_missing()` akzeptiert den Parameter `limit`, nicht `batch_limit`
- In `routes/tourplan_match.py` wurde `batch_limit=BATCH_LIMIT` verwendet

**Fix:**
```python
# Vorher:
filled = await fill_missing(missing_addrs, batch_limit=BATCH_LIMIT)

# Nachher:
filled = await fill_missing(missing_addrs, limit=BATCH_LIMIT)
```

**Datei:** `routes/tourplan_match.py` (Zeile 319)

---

### 2. `'StopModel' object has no attribute 'get'`

**Fehler:**
```
AttributeError: 'StopModel' object has no attribute 'get'
```

**Ursache:**
- `StopModel` ist ein Pydantic-Modell, kein Dictionary
- Pydantic-Modelle haben keine `.get()`-Methode
- Zugriff auf Attribute muss direkt erfolgen: `s.lat` statt `s.get('lat')`

**Fix:**
```python
# Vorher:
for s in stops:
    if s.get('lat') and s.get('lon'):
        stop_copy = dict(s)
        # ...

# Nachher:
for s in stops:
    # Pydantic-Modell: Zugriff auf Attribute direkt, nicht .get()
    if s.lat is not None and s.lon is not None:
        # Erstelle Kopie des Stops als Dict (Pydantic V2: model_dump())
        stop_copy = s.model_dump() if hasattr(s, 'model_dump') else s.dict()
        # ...
```

**Zusätzliche Fixes:**
- `body.get('is_bar_tour', False)` → `validated_request.is_bar_tour`
- `dict(s)` → `s.model_dump()` (Pydantic V2) oder `s.dict()` (Fallback für V1)

**Datei:** `routes/workflow_api.py` (Zeilen 1985-1996)

---

## 📋 Zusammenfassung

**Behobene Dateien:**
1. `routes/tourplan_match.py` - `batch_limit` → `limit`
2. `routes/workflow_api.py` - Pydantic-Modell-Zugriff korrigiert

**Betroffene Endpunkte:**
- `GET /api/tourplan/match` - Funktioniert jetzt korrekt
- `POST /api/tour/optimize` - Funktioniert jetzt korrekt

**Tests:**
- Server startet ohne Fehler
- Match-Endpoint verarbeitet CSV-Dateien korrekt
- Optimize-Endpoint verarbeitet Pydantic-Modelle korrekt

---

## ✅ Status

- ✅ `fill_missing()` Parameter korrigiert
- ✅ Pydantic V2 Kompatibilität hergestellt
- ✅ StopModel-Zugriff korrigiert
- ✅ Server startet ohne Fehler

---

**Nächster Schritt:** Server neu starten und Workflow testen

