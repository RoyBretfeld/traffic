-- Phase 2 Migration: Routing-Stats & OSRM-Cache
-- Datum: 2025-11-09
-- Beschreibung: Neue Tabellen für OSRM-Cache, Routen-Tracking, Statistik

-- OSRM Cache
CREATE TABLE IF NOT EXISTS osrm_cache (
  key TEXT PRIMARY KEY,         -- method|profile|coords|params hash
  geometry TEXT NOT NULL,       -- polyline6
  distance REAL, 
  duration REAL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_osrm_cache_created ON osrm_cache(created_at);

-- Routen & Legs
CREATE TABLE IF NOT EXISTS routes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_id TEXT,             -- Tour-ID/Name
  started_at DATETIME, 
  finished_at DATETIME,
  distance_m REAL, 
  duration_s REAL,
  status TEXT DEFAULT 'draft'   -- draft|ok|error
);
CREATE INDEX IF NOT EXISTS idx_routes_external_id ON routes(external_id);
CREATE INDEX IF NOT EXISTS idx_routes_status ON routes(status);

CREATE TABLE IF NOT EXISTS route_legs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  from_addr TEXT, 
  to_addr TEXT,
  from_lat REAL, 
  from_lon REAL, 
  to_lat REAL, 
  to_lon REAL,
  geometry TEXT, 
  distance_m REAL, 
  duration_s REAL,
  osrm_source TEXT,            -- cache|live|fallback
  UNIQUE(route_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_route_legs_route ON route_legs(route_id);

-- Statistik (täglich + Runs)
CREATE TABLE IF NOT EXISTS stats_run (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ran_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  tours INT, 
  legs INT,
  routed_ok INT, 
  routed_fallback INT, 
  routed_error INT,
  total_distance_m REAL, 
  total_duration_s REAL
);
CREATE INDEX IF NOT EXISTS idx_stats_run_ran_at ON stats_run(ran_at);

CREATE TABLE IF NOT EXISTS stats_day (
  day TEXT PRIMARY KEY,         -- YYYY-MM-DD
  tours INT, 
  legs INT,
  distance_m REAL, 
  duration_s REAL
);

-- Geo-Fails (bereits vorhanden? dann ergänzen)
CREATE TABLE IF NOT EXISTS geo_fail (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  raw_address TEXT, 
  reason TEXT, 
  first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_geo_fail_reason ON geo_fail(reason);
CREATE INDEX IF NOT EXISTS idx_geo_fail_first_seen ON geo_fail(first_seen);

