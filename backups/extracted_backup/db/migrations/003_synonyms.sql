-- Migration 003: Address Synonyms (Alias → Customer/Address/Coordinates)
-- Deterministisches CSV-Parsing mit persistenter Synonymliste

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS address_synonyms (
  alias            TEXT PRIMARY KEY,
  alias_norm       TEXT NOT NULL,
  customer_id      TEXT,
  customer_name    TEXT,
  street           TEXT,
  postal_code      TEXT,
  city             TEXT,
  country          TEXT NOT NULL DEFAULT 'DE',
  lat              REAL,
  lon              REAL,
  note             TEXT,
  active           INTEGER NOT NULL DEFAULT 1,
  priority         INTEGER NOT NULL DEFAULT 0,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_syn_alias_norm ON address_synonyms(alias_norm);
CREATE INDEX IF NOT EXISTS idx_syn_customer ON address_synonyms(customer_id);
CREATE INDEX IF NOT EXISTS idx_syn_active ON address_synonyms(active, priority DESC);

CREATE TRIGGER IF NOT EXISTS trg_synonyms_updated
AFTER UPDATE ON address_synonyms
FOR EACH ROW BEGIN
  UPDATE address_synonyms SET updated_at = datetime('now') WHERE alias = OLD.alias;
END;

-- Nutzungsstatistik für Synonyme
CREATE TABLE IF NOT EXISTS synonym_hits (
  alias_norm TEXT NOT NULL,
  used_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_syn_hits_norm ON synonym_hits(alias_norm);
CREATE INDEX IF NOT EXISTS idx_syn_hits_used ON synonym_hits(used_at);

