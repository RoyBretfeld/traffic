# Prompt 17 - Vorschläge übernehmen (Alias) + Audit

## Übersicht

Implementierung eines Alias-Systems zum Übernehmen von Fuzzy-Vorschlägen ohne Daten-Duplikation. Das System erstellt Alias-Zuordnungen zwischen problematischen und kanonischen Adressen und integriert diese nahtlos in die bestehende Match-Route.

## Implementierte Features

### ✅ **Alias-Schema**

- **`db/schema_alias.py`** - Idempotente Tabellenerstellung
- **`geo_alias`** - Haupttabelle für Alias-Zuordnungen
- **`geo_audit`** - Audit-Log für alle Alias-Aktionen
- **SQLite-kompatible** separate CREATE-Statements

### ✅ **Alias-Repository**

- **`repositories/geo_alias_repo.py`** - Vollständige Repository-Schicht
- **`set_alias()`** - Alias-Erstellung mit Validierung
- **`resolve_aliases()`** - Bulk-Auflösung von Alias-Zuordnungen
- **`remove_alias()`** - Alias-Entfernung mit Audit-Log
- **`get_alias_stats()`** - Statistiken über Alias-System

### ✅ **Match-Route Integration**

- **`routes/tourplan_match.py`** - Alias-fähig gemacht
- **`alias_of` Feld** - Zeigt kanonische Adresse bei Alias-Nutzung
- **Nahtlose Integration** - Keine Änderung der bestehenden API
- **Bulk-Performance** - Effiziente Alias-Auflösung

### ✅ **Accept-Endpoint**

- **`routes/tourplan_accept.py`** - Neue API-Endpoints
- **`POST /api/tourplan/suggest/accept`** - Hauptendpoint für Vorschlag-Übernahme
- **`GET /api/tourplan/suggest/accept/stats`** - Alias-Statistiken
- **`DELETE /api/tourplan/suggest/accept/{query}`** - Alias-Entfernung

### ✅ **Unit-Tests**

- **7 Tests** alle bestanden
- **Vollständige Abdeckung** aller Funktionen
- **SQLite-basiert** für isolierte Tests
- **Edge Cases** und realistische Szenarien

## Technische Details

### **Alias-Schema**

```sql
CREATE TABLE IF NOT EXISTS geo_alias (
  address_norm TEXT PRIMARY KEY,          -- problematische Schreibweise
  canonical_norm TEXT NOT NULL,           -- verweist auf geo_cache
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT
);

CREATE TABLE IF NOT EXISTS geo_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  action TEXT NOT NULL,                   -- 'alias_set', 'alias_remove'
  query TEXT,
  canonical TEXT,
  by_user TEXT
);
```

### **Alias-Repository**

```python
def set_alias(query: str, canonical: str, created_by: str | None = None):
    """Setzt einen Alias von query zu canonical."""
    q = canon_addr(query)  # Erweiterte Normalisierung für Query
    c = normalize_addr(canonical)  # Standard-Normalisierung für Canonical
    
    if not q or not c or q == c:
        raise ValueError("alias invalid: empty or identical")
    
    # Prüfe ob canonical im geo_cache existiert
    # Erstelle Alias-Zuordnung
    # Logge in Audit-Tabelle

def resolve_aliases(addresses: Iterable[str]) -> Dict[str, str]:
    """Löst Alias-Zuordnungen für eine Liste von Adressen auf."""
    # Bulk-Lookup für effiziente Performance
    # Rückgabe: query_norm -> canonical_norm
```

### **Match-Route Integration**

```python
# Vorher: Nur direkter geo_cache Lookup
geo = bulk_get(addrs)

# Nachher: Alias-Auflösung + erweiterter Lookup
aliases = resolve_aliases(addrs)  # map: query_norm -> canonical_norm
geo = bulk_get(addrs + list(aliases.values()))  # beide Mengen laden

# Ergebnis mit Alias-Information
canon = aliases.get(addr_norm)
rec = geo.get(addr_norm) or (geo.get(canon) if canon else None)
status = "ok" if (rec and not marks) else ("warn" if (not marks and not rec) else "bad")

out.append({
    "row": int(i + 1),
    "address": addr_norm,
    "alias_of": canon,  # neu: zeigt, wenn Alias greift
    "has_geo": bool(rec),
    "geo": rec,
    "markers": marks,
    "status": status,
})
```

### **Accept-Endpoint**

```python
@router.post("/api/tourplan/suggest/accept")
def api_accept_suggestion(body: AcceptBody):
    """Nimmt einen Fuzzy-Vorschlag als Alias-Zuordnung an."""
    try:
        set_alias(body.query, body.accept, body.by_user)
        return JSONResponse({
            "ok": True,
            "message": f"Alias gesetzt: '{body.query}' → '{body.accept}'"
        }, media_type="application/json; charset=utf-8")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Verwendung

### **API-Aufruf**

```bash
# Vorschlag als Alias übernehmen
curl -X POST "http://127.0.0.1:8111/api/tourplan/suggest/accept" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Froebelstr. 1, Dresden",
    "accept": "Fröbelstraße 1, Dresden",
    "by_user": "admin"
  }'

# Alias-Statistiken abrufen
curl "http://127.0.0.1:8111/api/tourplan/suggest/accept/stats"

# Alias entfernen
curl -X DELETE "http://127.0.0.1:8111/api/tourplan/suggest/accept/Froebelstr.%201,%20Dresden"
```

### **Beispiel-Response (Match-Route)**

```json
{
  "file": "Tourenplan 01.09.2025.csv",
  "rows": 150,
  "ok": 142,
  "warn": 5,
  "bad": 3,
  "items": [
    {
      "row": 1,
      "address": "froebelstraße 1, dresden",
      "alias_of": "Fröbelstraße 1, Dresden",
      "has_geo": true,
      "geo": {
        "lat": 51.0504,
        "lon": 13.7373,
        "address": "Fröbelstraße 1, Dresden"
      },
      "markers": [],
      "status": "ok"
    }
  ]
}
```

### **Beispiel-Response (Accept-Endpoint)**

```json
{
  "ok": true,
  "message": "Alias gesetzt: 'Froebelstr. 1, Dresden' → 'Fröbelstraße 1, Dresden'"
}
```

### **Beispiel-Response (Stats)**

```json
{
  "total_aliases": 15,
  "total_audit_entries": 18
}
```

## Akzeptanzkriterien

✅ **`geo_alias` & `geo_audit`** existieren (idempotent via Startup-Hook)  
✅ **`POST /api/tourplan/suggest/accept`** speichert Alias nur, wenn `accept` bereits im `geo_cache` ist; sonst 400  
✅ **`routes/tourplan_match`** zeigt bei aliasierten Adressen `alias_of` und liefert die Geo-Koordinaten der kanonischen Adresse  
✅ **Unit-Test `test_alias_accept.py`** ist grün (7/7 bestanden)  
✅ **Keine Frontend-Änderung** in diesem Schritt  

## Test-Ergebnisse

### **Unit-Tests**
```bash
python -m pytest tests/test_alias_accept.py -v
# 7 passed in 0.66s
```

### **Test-Abdeckung**
- ✅ Komplette Alias-Funktionalität (Erstellung, Auflösung, Match-Integration)
- ✅ Validierung (leere/identische Adressen, nicht-existierende Canonical)
- ✅ Alias-Überschreibung (UPSERT-Funktionalität)
- ✅ Alias-Entfernung mit Audit-Log
- ✅ Statistiken und leere Eingaben
- ✅ Realistische deutsche Adressen mit Abkürzungen

## Dateien

- **`db/schema_alias.py`** - Alias-Schema (geo_alias, geo_audit)
- **`repositories/geo_alias_repo.py`** - Alias-Repository
- **`routes/tourplan_match.py`** - Alias-fähige Match-Route
- **`routes/tourplan_accept.py`** - Accept-Endpoints
- **`tests/test_alias_accept.py`** - Unit-Tests (7 Tests)
- **`app_startup.py`** - Schema-Initialisierung
- **`backend/app.py`** - Route-Registrierung

## Git-Commit

**Branch:** `fix/encoding-unification`  
**Commit:** `a799b10` - "feat: Prompt 17 - Vorschläge übernehmen (Alias) + Audit implementiert"

## Workflow

1. **Fuzzy-Suggest** generiert Vorschläge für fehlende Adressen
2. **User wählt** einen Vorschlag aus der Liste
3. **Accept-Endpoint** erstellt Alias-Zuordnung ohne Daten-Duplikation
4. **Match-Route** löst Aliasse automatisch auf und liefert Geo-Koordinaten
5. **Audit-Log** protokolliert alle Alias-Aktionen

Das System ermöglicht es, problematische Adressschreibweisen durch intelligente Alias-Zuordnungen zu korrigieren, ohne die ursprünglichen Daten zu duplizieren oder zu verändern.
