# Tour-Ignore-Liste & Allow-Liste

**Datum:** 2025-01-09  
**Status:** ✅ Implementiert

---

## Übersicht

Das System unterstützt jetzt **zwei Filter-Listen**:

1. **Ignore-Liste:** Touren die **übersprungen** werden sollen
2. **Allow-Liste:** Touren die **verarbeitet** werden sollen (wenn vorhanden, werden NUR diese Touren verarbeitet)

### Filter-Logik

**Priorität:**
1. **Ignore-Liste hat IMMER Vorrang** → Touren in Ignore-Liste werden übersprungen
2. **Allow-Liste** (wenn vorhanden und nicht leer):
   - Nur Touren die in Allow-Liste stehen werden verarbeitet
   - Alle anderen Touren werden übersprungen
3. **Keine Allow-Liste oder leer:**
   - Alle Touren werden verarbeitet (außer Ignore-Liste)

**Beispiele:**
- Tour "DBD Nachtlieferung" → übersprungen (in Ignore-Liste)
- Tour "CB-08.00 Tour" → verarbeitet (wenn in Allow-Liste oder Allow-Liste leer)
- Tour "FG-09.00 Tour" → übersprungen (wenn Allow-Liste = ["CB", "T", "BZ"] und "FG" nicht drin)

### Verwendung

Touren die mit einem Pattern aus der Liste beginnen oder das Pattern im Namen enthalten, werden ignoriert.

**Beispiele:**
- `DBD` → ignoriert Touren wie "DBD", "DBD Nachtlieferung", etc.
- `DPD` → ignoriert Touren wie "DPD", "DPD Pickup", etc.
- `DVD` → ignoriert Touren wie "DVD", etc.

---

## Konfigurationsdatei

**Datei:** `config/tour_ignore_list.json`

```json
{
  "ignore_tours": [
    "DBD",
    "DPD",
    "DVD"
  ],
  "allow_tours": [
    "CB",
    "T",
    "BZ"
  ],
  "description": "Touren die nicht in die Routenplanung einbezogen werden sollen",
  "allow_description": "Touren die VERARBEITET werden sollen (wenn Liste vorhanden, werden NUR diese Touren verarbeitet)",
  "reason": "Pickup/Nachtlieferung - werden separat gehandhabt",
  "allow_reason": "Direkte Routen (Cottbus, Taucher, Bautzen) - können schnell verarbeitet werden",
  "usage": {
    "ignore_tours": "Touren mit diesen Patterns werden übersprungen",
    "allow_tours": "Wenn diese Liste vorhanden ist und nicht leer, werden NUR Touren verarbeitet die hier stehen. Ignore-Liste hat Vorrang."
  }
}
```

### Neue Touren hinzufügen

**Ignore-Liste:** Einfach neue Patterns zur `ignore_tours` Liste hinzufügen:

```json
{
  "ignore_tours": [
    "DBD",
    "DPD",
    "DVD",
    "NEUE_TOUR"  // ← Hier hinzufügen
  ],
  "allow_tours": [
    "CB",
    "T",
    "BZ",
    "NEUE_ALLOW_TOUR"  // ← Hier hinzufügen (optional)
  ]
}
```

### Allow-Liste deaktivieren

Um alle Touren zu verarbeiten (außer Ignore-Liste), einfach `allow_tours` auf leeres Array setzen oder entfernen:

```json
{
  "ignore_tours": ["DBD", "DPD", "DVD"],
  "allow_tours": []  // ← Leer = alle Touren erlauben (außer Ignore-Liste)
}
```

---

## Implementierung

### Code-Stelle

**Datei:** `routes/workflow_api.py`

**Funktionen:**
- `load_tour_filter_lists()` - Lädt beide Listen (Ignore + Allow) aus JSON
- `should_process_tour(tour_name, ignore_list, allow_list)` - Prüft ob Tour verarbeitet werden soll

**Filter (Zeile ~958-969):**
```python
# ✅ FILTER: Tour-Ignore-Liste und Allow-Liste prüfen
ignore_list, allow_list = load_tour_filter_lists()
if not should_process_tour(tour_name, ignore_list, allow_list):
    print(f"[WORKFLOW] Tour '{tour_name}' übersprungen ({...})")
    continue  # Überspringe diese Tour komplett
```

### Fallback

Falls die JSON-Datei nicht gefunden werden kann, werden Standard-Listen verwendet:
- Ignore: `["DBD", "DPD", "DVD"]`
- Allow: `[]` (leer = alle erlauben)

---

## Logging

Wenn eine Tour übersprungen wird, erscheint im Log:
```
[WORKFLOW] Tour 'DPD Nachtlieferung' übersprungen (in Ignore-Liste: ['DPD'])
```

---

**Letzte Aktualisierung:** 2025-01-09  
**Status:** ✅ Produktiv

