-- OSRM Cache (polyline6, feature-hash, params-hash)
-- Phase 2 Runbook: Persistenter Cache für Routing-Ergebnisse

CREATE TABLE IF NOT EXISTS osrm_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  params_hash TEXT NOT NULL,
  geometry_polyline6 TEXT NOT NULL,
  distance_m INTEGER NOT NULL,
  duration_s INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_osrm_cache_params_hash ON osrm_cache(params_hash);

-- Optional: Index für TTL-Cleanup (nach created_at)
CREATE INDEX IF NOT EXISTS idx_osrm_cache_created_at ON osrm_cache(created_at);

