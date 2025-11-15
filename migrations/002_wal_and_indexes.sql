PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE INDEX IF NOT EXISTS idx_queue_status    ON address_exception_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_seen      ON address_exception_queue(times_seen, last_seen);

CREATE INDEX IF NOT EXISTS idx_corr_key        ON address_corrections(key);
CREATE INDEX IF NOT EXISTS idx_corr_city_zip   ON address_corrections(city, postal_code);

