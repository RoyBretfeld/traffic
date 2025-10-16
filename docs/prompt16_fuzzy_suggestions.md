# Prompt 16 - Fuzzy-Vorschläge für fehlende Adressen

## Übersicht

Implementierung von Fuzzy-Vorschlägen für fehlende Adressen basierend auf Ähnlichkeitssuche im `geo_cache`. Das System arbeitet nur lesend und ändert keine Datenbank-Einträge automatisch.

## Implementierte Features

### ✅ **Erweiterte Normalisierung**

- **`canon_addr()`** in `repositories/geo_repo.py` für Fuzzy-Search
- **Abkürzungs-Erkennung**: str. → straße, pl. → platz, etc.
- **Unicode-Normalisierung** und Whitespace-Bereinigung
- **Mehr Toleranz** als `normalize_addr()` für besseres Matching

### ✅ **Fuzzy-Suggest Service**

- **`services/fuzzy_suggest.py`** - Kern-Service für Ähnlichkeitssuche
- **RapidFuzz-Unterstützung** mit Fallback auf difflib
- **Konfigurierbare Parameter**: topk, threshold, pool
- **Statistiken-Funktion** für Service-Überwachung

### ✅ **API-Endpoints**

- **`/api/tourplan/suggest`** - Hauptendpoint für Vorschläge
- **`/api/tourplan/suggest/stats`** - Service-Statistiken
- **Parameter**: file, topk (1-10), threshold (0-100)
- **Nur lesend** - keine DB-Änderungen

### ✅ **Unit-Tests**

- **9 Tests** alle bestanden
- **Vollständige Abdeckung** aller Funktionen
- **Edge Cases** und realistische Szenarien getestet

## Technische Details

### **Kanonische Normalisierung**

```python
def canon_addr(s: str) -> str:
    """Kanonische Adress-Normalisierung für Fuzzy-Search (mehr Toleranz)."""
    s = unicodedata.normalize("NFC", (s or ""))
    s = s.lower()
    # Abkürzungen vereinheitlichen
    for pat, rep in _ABBR:
        s = re.sub(pat, rep, s)
    # Mehrfach-Whitespace entfernen
    s = re.sub(r"\s+", " ", s).strip()
    return s
```

### **Fuzzy-Search-Engine**

```python
# Optional: RapidFuzz für bessere Performance
try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
    def _topn(query: str, choices: Iterable[str], n: int = 3):
        return process.extract(query, choices, scorer=fuzz.WRatio, limit=n)
except ImportError:
    HAS_RAPIDFUZZ = False
    import difflib
    def _topn(query: str, choices: Iterable[str], n: int = 3):
        seq = difflib.get_close_matches(query, choices, n=n, cutoff=0.0)
        return [(c, 100.0 * (1.0 - idx * 0.1), None) for idx, c in enumerate(seq)]
```

### **API-Endpoint**

```python
@router.get("/api/tourplan/suggest")
def api_tourplan_suggest(
    file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene"),
    topk: int = Query(3, ge=1, le=10, description="Maximale Anzahl Vorschläge pro Adresse"),
    threshold: int = Query(70, ge=0, le=100, description="Mindest-Score für Vorschläge (0-100)")
):
    # 1) CSV lesen über zentralen Ingest
    # 2) Fehlende Adressen identifizieren
    # 3) Fuzzy-Vorschläge ermitteln
    # 4) Ergebnis zurückgeben
```

## Verwendung

### **API-Aufruf**

```bash
# Vorschläge für fehlende Adressen
curl "http://127.0.0.1:8111/api/tourplan/suggest?file=Tourenplan%2001.09.2025.csv&topk=3&threshold=70"

# Service-Statistiken
curl "http://127.0.0.1:8111/api/tourplan/suggest/stats"
```

### **Beispiel-Response**

```json
{
  "file": "Tourenplan 01.09.2025.csv",
  "missing": 15,
  "total_addresses": 150,
  "cached_addresses": 135,
  "parameters": {
    "topk": 3,
    "threshold": 70
  },
  "items": [
    {
      "query": "Hauptstr. 42, Dresden",
      "suggestions": [
        {
          "address": "Hauptstraße 42, 01067 Dresden",
          "score": 85.5
        },
        {
          "address": "Hauptstraße 40, 01067 Dresden", 
          "score": 78.2
        }
      ]
    }
  ]
}
```

### **Service-Statistiken**

```json
{
  "total_cached_addresses": 1500,
  "fuzzy_engine": "rapidfuzz",
  "max_pool_size": 50000
}
```

## Akzeptanzkriterien

✅ **Service `suggest_for()`** liefert pro fehlender Adresse bis zu `topk` Vorschläge mit Score ≥ `threshold`  
✅ **Route `/api/tourplan/suggest`** arbeitet nur lesend und basiert auf aktueller CSV + `geo_cache`  
✅ **Unit-Test `test_fuzzy_suggest.py`** ist grün (9/9 bestanden)  
✅ **Keine automatischen DB-Änderungen** - nur Vorschläge werden generiert  

## Test-Ergebnisse

### **Unit-Tests**
```bash
python -m pytest tests/test_fuzzy_suggest.py -v
# 9 passed in 0.77s
```

### **Test-Abdeckung**
- ✅ Kanonische Normalisierung (Grundlagen + Edge Cases)
- ✅ Fuzzy-Suggest-Funktionalität (Basis + Threshold + Topk)
- ✅ Leere Eingaben und keine Matches
- ✅ Realistische deutsche Adressen
- ✅ Service-Statistiken

## Dateien

- **`repositories/geo_repo.py`** - Erweiterte Normalisierung (`canon_addr`)
- **`services/fuzzy_suggest.py`** - Fuzzy-Suggest Service
- **`routes/tourplan_suggest.py`** - API-Endpoints
- **`tests/test_fuzzy_suggest.py`** - Unit-Tests (9 Tests)
- **`backend/app.py`** - Route-Registrierung

## Git-Commit

**Branch:** `fix/encoding-unification`  
**Commit:** `2741b44` - "feat: Prompt 16 - Fuzzy-Vorschläge für fehlende Adressen implementiert"
