# Phase 2: Datenbank-Schema-Erweiterung

**Status:** 🟡 In Planung  
**Datum:** 2025-11-08  
**Priorität:** Phase 2 (Kurzfristig)

---

## Ziel

Erweitere das Datenbank-Schema um neue Tabellen für:
- **Stats-Aggregation** (stats_monthly, stats_daily)
- **Routes** (routes, route_legs) - für detaillierte Routen-Speicherung
- **OSRM-Cache** (osrm_cache) - für Route-Geometrie-Caching

---

## Neue Tabellen

### 1. `stats_monthly`
Speichert monatliche Statistiken (aggregiert).

```sql
CREATE TABLE IF NOT EXISTS stats_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,  -- Format: YYYY-MM
    tours_count INTEGER DEFAULT 0,
    stops_count INTEGER DEFAULT 0,
    total_km REAL DEFAULT 0.0,
    avg_stops_per_tour REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(month)
);
```

**Indizes:**
- `idx_stats_monthly_month` auf `month`

---

### 2. `routes`
Speichert optimierte Routen mit Metadaten.

```sql
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id TEXT NOT NULL,
    tour_date TEXT NOT NULL,
    route_name TEXT,  -- z.B. "W-07:00 A"
    total_distance_km REAL,
    total_duration_min INTEGER,
    stops_count INTEGER,
    status TEXT DEFAULT 'active',  -- active, completed, cancelled
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

**Indizes:**
- `idx_routes_tour_date` auf `(tour_id, tour_date)`
- `idx_routes_date` auf `tour_date`

---

### 3. `route_legs`
Speichert einzelne Route-Segmente (zwischen Stops).

```sql
CREATE TABLE IF NOT EXISTS route_legs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    sequence_order INTEGER NOT NULL,
    from_stop_id INTEGER,  -- Referenz auf kunden.id
    to_stop_id INTEGER,    -- Referenz auf kunden.id
    distance_km REAL,
    duration_min INTEGER,
    geometry TEXT,  -- Polyline6-encoded
    geometry_type TEXT DEFAULT 'polyline6',
    source TEXT DEFAULT 'osrm',  -- osrm, haversine_fallback
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);
```

**Indizes:**
- `idx_route_legs_route` auf `route_id`
- `idx_route_legs_sequence` auf `(route_id, sequence_order)`

---

### 4. `osrm_cache`
Cached OSRM-Route-Geometrien (Polyline6).

```sql
CREATE TABLE IF NOT EXISTS osrm_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_lat REAL NOT NULL,
    from_lon REAL NOT NULL,
    to_lat REAL NOT NULL,
    to_lon REAL NOT NULL,
    geometry TEXT NOT NULL,  -- Polyline6-encoded
    distance_km REAL,
    duration_min INTEGER,
    cached_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,  -- Optional: Cache-Ablauf
    UNIQUE(from_lat, from_lon, to_lat, to_lon)
);
```

**Indizes:**
- `idx_osrm_cache_coords` auf `(from_lat, from_lon, to_lat, to_lon)`
- `idx_osrm_cache_expires` auf `expires_at`

---

## Migration-Strategie

### Schritt 1: Tabellen erstellen (ohne Daten)
- Tabellen werden beim Start erstellt (in `app_startup.py`)
- Bestehende Daten bleiben unverändert

### Schritt 2: Schrittweise Migration
- **Stats:** Aggregation schreibt in `stats_monthly`, liest weiterhin aus `touren`
- **Routes:** Neue Routen werden in `routes` gespeichert, alte bleiben in `touren`
- **OSRM-Cache:** Wird beim ersten Route-Request gefüllt

### Schritt 3: Dual-Write (optional)
- Neue Daten werden in beide Tabellen geschrieben
- Lesen erfolgt aus neuen Tabellen

### Schritt 4: Migration bestehender Daten (optional)
- Migrations-Script für bestehende Touren → Routes
- Nur wenn nötig

---

## Rollback-Plan

1. **Feature-Flag:** `app.feature_flags.new_schema_enabled: false`
2. **Tabellen bleiben:** Werden nicht gelöscht, nur nicht verwendet
3. **Code-Rollback:** Alte Queries bleiben funktionsfähig

---

## Tests

- [ ] Tabellen werden beim Start erstellt
- [ ] Indizes werden korrekt erstellt
- [ ] Foreign Keys funktionieren
- [ ] Migration-Script testen (mit Backup)

---

**Status:** 🟡 Bereit zur Implementierung

