
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS address_corrections (
  key TEXT PRIMARY KEY,
  street_canonical TEXT NOT NULL,
  postal_code TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'DE',
  lat REAL,
  lon REAL,
  source TEXT NOT NULL DEFAULT 'manual',
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS address_exception_queue (
  key TEXT PRIMARY KEY,
  street TEXT NOT NULL,
  postal_code TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'DE',
  last_seen TEXT NOT NULL DEFAULT (datetime('now')),
  times_seen INTEGER NOT NULL DEFAULT 1,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS trg_address_corrections_updated
AFTER UPDATE ON address_corrections
FOR EACH ROW BEGIN
  UPDATE address_corrections SET updated_at = datetime('now') WHERE key = OLD.key;
END;

CREATE TRIGGER IF NOT EXISTS trg_address_exception_queue_updated
AFTER UPDATE ON address_exception_queue
FOR EACH ROW BEGIN
  UPDATE address_exception_queue SET updated_at = datetime('now') WHERE key = OLD.key;
END;
