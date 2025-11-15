# Einführung: Adaptive Pattern Engine

## Für Entwickler: Schnellstart

### Was ist die Adaptive Pattern Engine?

Ein **selbstlernendes System**, das Pattern automatisch erkennt und speichert - **ohne AI-Kosten**.

### Grundkonzept

```
┌─────────────────────────────────────────────┐
│  Problem: AI kostet, Python muss gepflegt   │
│  Lösung: Python mit automatischem Lernen    │
└─────────────────────────────────────────────┘
```

### Code-Beispiel

```python
from backend.services.adaptive_pattern_engine import get_pattern_engine

# Engine initialisieren
engine = get_pattern_engine()

# Normalisieren (lernt automatisch)
normalized, pattern_type = engine.normalize_with_learning("Bannewitz, OT Posen")
# Ergebnis: "Bannewitz" (Pattern gespeichert)

# Nächstes Mal: Direkt aus DB (kostenlos)
normalized, _ = engine.normalize_with_learning("Bannewitz, OT Posen")
# Ergebnis: "Bannewitz" (aus DB, sofort)
```

## Architektur

### Komponenten

1. **Pattern-Datenbank** (`learned_patterns.db`)
   - Speichert: Input → Output
   - Wiederverwendung ohne Neuberechnung

2. **Regel-Engine** (Python)
   - Bekannte Regeln (OT, Slash, Dash)
   - Erweitert durch gelernte Pattern

3. **Selbstlern-Mechanismus**
   - Lernt aus erfolgreichen Normalisierungen
   - Speichert für zukünftige Nutzung

### Datenfluss

```
Input → Prüfe DB → Pattern vorhanden?
                    │
                    ├─> JA: Aus DB (kostenlos, sofort)
                    │
                    └─> NEIN: Python-Regeln → Speichere in DB
```

## Verwendung

### Einfaches Beispiel

```python
from backend.services.adaptive_pattern_engine import get_pattern_engine

engine = get_pattern_engine()

# Normalisieren
result, pattern_type = engine.normalize_with_learning(
    "Bannewitz, OT Posen",
    context={"postal_code": "01728"}
)

print(f"Original: Bannewitz, OT Posen")
print(f"Normalisiert: {result}")
print(f"Pattern: {pattern_type}")
# Output:
# Original: Bannewitz, OT Posen
# Normalisiert: Bannewitz
# Pattern: ot_removed
```

### Statistik abfragen

```python
stats = engine.get_statistics()
print(f"Pattern in DB: {stats['total_patterns']}")
print(f"Total Usage: {stats['total_usage']}")
print(f"Nach Typ: {stats['by_type']}")
```

## Integration

### In bestehende Funktionen

**Vorher (Hardcoded):**
```python
def normalize_city(city):
    if has_ot_part(city):
        return remove_ot_part(city)
    # ... weitere Regeln
```

**Nachher (Mit Adaptive Engine):**
```python
def normalize_city(city):
    engine = get_pattern_engine()
    normalized, _ = engine.normalize_with_learning(city)
    return normalized
```

### In API-Endpoints

```python
@router.post("/normalize")
async def normalize_address(address: str):
    engine = get_pattern_engine()
    result, pattern_type = engine.normalize_with_learning(address)
    
    return {
        "original": address,
        "normalized": result,
        "pattern": pattern_type
    }
```

## Monitoring

### Pattern-Statistiken

```python
stats = engine.get_statistics()

# Beispiel-Ausgabe:
# {
#     "total_patterns": 150,
#     "total_usage": 5000,
#     "by_type": {
#         "ot_removed": 80,
#         "slash_split": 30,
#         "dash_split": 25,
#         "postal_lookup": 15
#     }
# }
```

### Performance-Tracking

- DB-Abfrage: ~1ms
- Regel-Anwendung: ~5ms
- **Gesamt: ~6ms** (vs. 500ms bei AI)

## Best Practices

### 1. Pattern-Typen verwenden

```python
# Spezifischer Pattern-Typ angeben
learned = engine.get_pattern(text, pattern_type="ot_removed")
```

### 2. Context nutzen

```python
# Postleitzahl als Context
result = engine.normalize_with_learning(
    city,
    context={"postal_code": "01728"}
)
```

### 3. Manuelle Pattern hinzufügen

```python
# Manuell Pattern lernen (z.B. aus Admin-UI)
engine.learn_pattern(
    input_text="Spezieller Fall",
    normalized="Normalisiertes Ergebnis",
    pattern_type="custom",
    confidence=1.0
)
```

## Troubleshooting

### Problem: Pattern wird nicht gelernt

**Lösung:**
- Prüfe DB-Zugriff: `engine.db_path.exists()`
- Prüfe Schreibrechte
- Prüfe Logs für Fehler

### Problem: Falsches Pattern

**Lösung:**
- Pattern in DB manuell korrigieren
- Oder: Pattern löschen, neu lernen lassen

### Problem: Performance

**Lösung:**
- DB-Indizes prüfen
- Pattern-Cache verwenden
- Batch-Verarbeitung für viele Requests

## FAQ

**Q: Wie unterscheidet sich das von AI?**  
A: Adaptive Engine lernt **einmal**, speichert Pattern in DB. AI muss **jedes Mal** neu analysieren.

**Q: Wie unterscheidet sich das von normalen Python-Regeln?**  
A: Normale Regeln sind **statisch** (müssen manuell gepflegt werden). Adaptive Engine **lernt automatisch** neue Pattern.

**Q: Was wenn Pattern falsch ist?**  
A: Pattern kann manuell korrigiert oder gelöscht werden. System lernt aus Korrekturen.

**Q: Kann ich AI komplett entfernen?**  
A: Ja, nach Lernphase (<1% AI-Nutzung). Adaptive Engine übernimmt vollständig.

## Nächste Schritte

1. ✅ Adaptive Engine aktivieren
2. ⏳ Pattern sammeln (1-2 Wochen)
3. ⏳ AI-Nutzung reduzieren (<5%)
4. ⏳ Optional: AI entfernen (wenn <1% Nutzung)

## Zusammenfassung

**Adaptive Pattern Engine =**
- ✅ Kostenlos (keine API-Aufrufe)
- ✅ Selbstlernend (automatisches Pattern-Erkennen)
- ✅ Schnell (1ms statt 500ms)
- ✅ Robust (funktioniert immer)

**Ergebnis:** System das automatisch lernt, ohne Kosten zu verursachen.

