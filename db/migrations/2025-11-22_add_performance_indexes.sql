-- Migration: Performance-Indizes (HT-07)
-- Datum: 2025-11-22
-- Beschreibung: Indizes für bessere Query-Performance

-- Touren-Indizes
CREATE INDEX IF NOT EXISTS idx_tours_tour_plan_id ON tours(tour_plan_id) WHERE tour_plan_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tours_date ON tours(date);
CREATE INDEX IF NOT EXISTS idx_tours_status ON tours(status);
CREATE INDEX IF NOT EXISTS idx_tours_date_status ON tours(date, status);

-- Tour-Stops-Indizes
CREATE INDEX IF NOT EXISTS idx_tour_stops_tour_id ON tour_stops(tour_id);
CREATE INDEX IF NOT EXISTS idx_tour_stops_tour_sequence ON tour_stops(tour_id, sequence);
CREATE INDEX IF NOT EXISTS idx_tour_stops_customer_id ON tour_stops(customer_id) WHERE customer_id IS NOT NULL;

-- Tour-Events-Indizes
CREATE INDEX IF NOT EXISTS idx_tour_events_tour_id ON tour_events(tour_id);
CREATE INDEX IF NOT EXISTS idx_tour_events_tour_created ON tour_events(tour_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tour_events_type ON tour_events(type);
CREATE INDEX IF NOT EXISTS idx_tour_events_created_at ON tour_events(created_at DESC);

-- Stats-Daily-Indizes (bereits in Migration vorhanden, aber zur Sicherheit)
CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_daily_date_region ON stats_daily(date, region);
CREATE INDEX IF NOT EXISTS idx_stats_daily_date ON stats_daily(date DESC);

-- Customers-Indizes (falls customers Tabelle existiert)
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);

-- Geo-Cache-Indizes (Performance)
CREATE INDEX IF NOT EXISTS idx_geo_cache_last_seen ON geo_cache(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_geo_cache_source ON geo_cache(source);

-- Geo-Fail-Indizes (Performance)
CREATE INDEX IF NOT EXISTS idx_geo_fail_next_attempt ON geo_fail(next_attempt) WHERE next_attempt IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_geo_fail_reason ON geo_fail(reason);

-- Users-Indizes (Performance)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active);

