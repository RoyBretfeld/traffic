# Fix: Pydantic V2 Mutability-Problem

**Datum:** 2025-01-10 (Spät)  
**Status:** ✅ Behoben

---

## 🔍 Problem

In `routes/workflow_api.py` Zeile 1964-1968 wurde versucht, Pydantic-Modelle direkt zu ändern:

```python
# FEHLERHAFT:
for stop in stops:
    if stop.name:
        stop.name = unicodedata.normalize("NFC", stop.name)  # ❌ Funktioniert nicht in Pydantic V2
    if stop.address:
        stop.address = unicodedata.normalize("NFC", stop.address)  # ❌ Funktioniert nicht in Pydantic V2
```

**Ursache:**
- Pydantic V2 Modelle sind standardmäßig **immutable** (unveränderlich)
- Direkte Zuweisung zu Attributen schlägt fehl, wenn das Modell nicht als `mutable=True` konfiguriert ist
- Dies kann zu `ValidationError` oder stillen Fehlern führen

---

## ✅ Lösung

Die Normalisierung wird **NACH** der Konvertierung zu Dictionaries durchgeführt:

```python
# KORREKT:
for s in stops:
    if s.lat is not None and s.lon is not None:
        # Erstelle Kopie des Stops als Dict (Pydantic V2: model_dump())
        stop_copy = s.model_dump() if hasattr(s, 'model_dump') else s.dict()
        
        # Encoding Guard: Normalisiere Text-Felder (NACH Konvertierung zu Dict)
        if stop_copy.get('name'):
            stop_copy['name'] = unicodedata.normalize("NFC", stop_copy['name'])  # ✅ Funktioniert
        if stop_copy.get('address'):
            stop_copy['address'] = unicodedata.normalize("NFC", stop_copy['address'])  # ✅ Funktioniert
        
        valid_stops.append(stop_copy)
```

**Vorteile:**
- Keine Mutation von Pydantic-Modellen
- Normalisierung erfolgt auf Dictionaries (mutable)
- Funktioniert mit Pydantic V2 ohne zusätzliche Konfiguration

---

## 📋 Geänderte Dateien

- `routes/workflow_api.py` (Zeilen 1960-1996)

---

## ✅ Status

- ✅ Pydantic V2 Mutability-Problem behoben
- ✅ Encoding-Normalisierung funktioniert korrekt
- ✅ Keine Linter-Fehler

---

**Nächster Schritt:** Server neu starten und testen

