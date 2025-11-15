# Geo Fail Cache - Policy & Verhalten

## ❌ Altes Verhalten (FALSCH)

- Adressen wurden **permanent** im Fail-Cache gespeichert
- TTL von 1-24 Stunden → Adressen blieben lange blockiert
- Keine Möglichkeit, verbesserte Routinen auf fehlgeschlagene Adressen anzuwenden
- **Problem:** 100% Abdeckung nicht erreichbar

## ✅ Neues Verhalten (KORREKT)

### Kurzfristiges Rate-Limiting

Der Fail-Cache ist **NUR** für sehr kurzfristiges Rate-Limiting gedacht:

- **Temporäre Fehler:** 5 Minuten TTL (statt 1 Stunde)
- **No-Hit Adressen:** 10 Minuten TTL (statt 24 Stunden)
- **Automatische Bereinigung:** Abgelaufene Einträge werden automatisch entfernt
- **Wiederholtes Versuchen:** Nach Ablauf werden Adressen **automatisch wieder versucht**

### Ziel: 100% Abdeckung

**Wichtig:**
- Adressen werden **NICHT permanent** blockiert
- Alle Adressen werden **immer wieder versucht**
- Bei Verbesserungen der Erkennungsroutine: Fail-Cache **komplett leeren**

## Funktionen

### Automatische Bereinigung

Beim Server-Start werden abgelaufene Einträge automatisch bereinigt:

```python
# In backend/app.py
cleanup_expired()  # Entfernt abgelaufene Einträge → werden erneut versucht
```

### Manuelle Bereinigung

Wenn die Erkennungsroutine überarbeitet wurde:

```bash
# Alle Einträge löschen
python scripts/clear_fail_cache_for_retry.py

# Oder via API
POST /api/geocode/clear-all-fail-cache
```

### API-Endpoints

- `POST /api/geocode/clear-all-fail-cache` - Löscht ALLE Einträge
- `POST /api/geocode/cleanup-fail-cache` - Bereinigt abgelaufene Einträge
- `GET /api/geocode/fail-stats` - Statistiken
- `POST /api/geocode/force-retry?address=...` - Erzwingt Retry für eine Adresse

## Implementierung

### Repository (`repositories/geo_fail_repo.py`)

- `skip_set()` - Gibt nur sehr aktuelle Einträge zurück (max 10 Min)
- `mark_temp()` - TTL: 5 Minuten
- `mark_nohit()` - TTL: 10 Minuten
- `clear_all()` - Löscht ALLE Einträge
- `cleanup_expired()` - Entfernt abgelaufene Einträge

### Workflow

1. **Geocoding startet** → Prüft Fail-Cache (nur aktuelle Einträge)
2. **Fehlgeschlagen** → Markiert mit kurzer TTL (5-10 Min)
3. **Nach Ablauf** → Automatisch wieder versucht
4. **Bei Verbesserungen** → Fail-Cache komplett leeren → Alle Adressen erneut versuchen

## Regel

**Einmal fehlgeschlagen ≠ nie wieder versuchen**

**Sondern:** Kurz warten → Erneut versuchen → Ziel: 100% Abdeckung

