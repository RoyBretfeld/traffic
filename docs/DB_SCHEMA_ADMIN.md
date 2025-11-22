# TrafficApp 3.0 – DB-Schema & Admin-Ansicht „DB-Verwaltung"

## 1. Ziel

Dieses Dokument beschreibt:

* die **Zielstruktur** der zentralen TrafficApp-SQLite-Datenbank (`app.db` o.ä.)

* wie diese Struktur im Admin-Bereich unter **„DB-Verwaltung"** dargestellt werden kann.

Damit sieht man im Adminbereich nicht nur „es gibt eine DB", sondern **welche Tabellen mit welchem Zweck** existieren.

---

## 2. Überblick: Haupt-Datenbank

* **Typ:** SQLite

* **Datei:** z.B. `app.db` (Pfad über `DB_PATH` in `.env`)

* **Verwendung:**

  * Touren & Stops

  * Ereignisse / Logs

  * Statistiken

  * App-Konfiguration

---

## 3. Tabellenstruktur (Ziel-Schema)

### 3.1 Tabelle `tours`

Repräsentiert eine komplette Tour (geplant + Ergebnis).

**Konzeptuelles Schema:**

```sql
CREATE TABLE tours (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date                DATE NOT NULL,
    driver_id           TEXT,              -- Kennung/Fahrername oder ID
    region              TEXT,              -- z.B. "Dresden Nord"
    status              TEXT NOT NULL,     -- planned|in_progress|completed|aborted
    distance_planned_km REAL DEFAULT 0,
    distance_real_km    REAL DEFAULT 0,
    total_delay_minutes INTEGER DEFAULT 0,
    score_success       INTEGER DEFAULT 0, -- 0–100
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME
);
```

**Hinweis:**

* `score_success` ist die zentrale Kennzahl für spätere KI-Auswertungen.

---

### 3.2 Tabelle `tour_stops`

Alle Stops einer Tour.

```sql
CREATE TABLE tour_stops (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id                   INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
    customer_id               TEXT,            -- optional
    lat                       REAL NOT NULL,
    lon                       REAL NOT NULL,
    address_text              TEXT,
    planned_time_window_start DATETIME,
    planned_time_window_end   DATETIME,
    actual_arrival            DATETIME,
    sequence                  INTEGER NOT NULL,
    subroute_id               TEXT,            -- Kennung für Sub-Route (optional)
    created_at                DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tour_stops_tour ON tour_stops(tour_id);
```

---

### 3.3 Tabelle `tour_events`

Log-Einträge zu besonderen Ereignissen während einer Tour.

```sql
CREATE TABLE tour_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id     INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,         -- delay|reroute|traffic_jam|manual_override|error|...
    payload_json TEXT,                 -- zusätzliche Infos
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tour_events_tour ON tour_events(tour_id);
```

---

### 3.4 Tabelle `stats_daily`

Vorgeaggregierte Tages-Statistiken (für schnelle Auswertung im Adminbereich).

```sql
CREATE TABLE stats_daily (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              DATE NOT NULL,
    region            TEXT,            -- NULL = global
    total_tours       INTEGER DEFAULT 0,
    completed_tours   INTEGER DEFAULT 0,
    aborted_tours     INTEGER DEFAULT 0,
    total_stops       INTEGER DEFAULT 0,
    total_km_planned  REAL DEFAULT 0,
    total_km_real     REAL DEFAULT 0,
    avg_delay_minutes REAL DEFAULT 0,
    avg_success_score REAL DEFAULT 0
);

CREATE UNIQUE INDEX idx_stats_daily_date_region ON stats_daily(date, region);
```

---

### 3.5 Tabelle `system_logs`

Allgemeine System- / Fehler-Logs der Anwendung.

```sql
CREATE TABLE system_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    level       TEXT NOT NULL,         -- INFO|WARNING|ERROR
    source      TEXT,                  -- Modul/Service
    message     TEXT NOT NULL,
    payload_json TEXT,                 -- optionale strukturierte Daten
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_created ON system_logs(created_at);
```

---

### 3.6 Tabelle `app_settings`

Globale Konfigurationswerte / Flags.

```sql
CREATE TABLE app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Beispieleinträge:

* `"stats_aggregation_last_run"` → letztes erfolgreiches Stats-Update

* `"maintenance_mode"` → on/off

---

### 3.7 (Optional) Tabelle `route_embeddings`

Nur falls Vektor-/KI-Features umgesetzt werden.

```sql
CREATE TABLE route_embeddings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id       INTEGER NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
    model_name    TEXT NOT NULL,
    embedding     BLOB NOT NULL,       -- oder eigenes Vektorformat
    success_score INTEGER,             -- Spiegel von tours.score_success
    meta_json     TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_route_embeddings_tour ON route_embeddings(tour_id);
```

---

## 4. Relationen (Text-ER-Modell)

* **tours 1↔N tour_stops**

  * Eine Tour hat viele Stops

* **tours 1↔N tour_events**

  * Eine Tour hat viele Events

* **tours 1↔N route_embeddings** (optional)

  * Eine Tour kann mehrere Embeddings haben (verschiedene Modelle)

* **stats_daily** ist eine rein aggregierte Sicht (kein direkter FK, wird aus `tours`/`tour_stops` berechnet).

* **system_logs** und **app_settings** sind global und hängen nicht direkt an einer Tour.

---

## 5. Admin-Tab „DB-Verwaltung" – Inhalt

Die Admin-Ansicht **„DB-Verwaltung"** kann diese Struktur wie folgt visualisieren.

### 5.1 Oberer Bereich – DB-Info

* DB-Datei: Pfad + Name (`app.db`)

* Größe der Datei (MB)

* Anzahl Tabellen

* Letzte Migration / Schema-Version (optional)

### 5.2 Mittlerer Bereich – Tabellenliste

Tabelle mit Spalten:

* Tabellenname

* Kurzbeschreibung

* Anzahl Zeilen (Row-Count)

* Aktionen (Details ansehen)

Beispieleinhalte:

* `tours` – "Alle Touren (Plan + Ergebnis)"

* `tour_stops` – "Stops pro Tour"

* `tour_events` – "Ereignisse/Probleme während Touren"

* `stats_daily` – "Aggregierte Tagesstatistiken"

* `system_logs` – "System- und Fehlerlogs"

* `app_settings` – "Globale Einstellungen"

* `route_embeddings` (falls vorhanden) – "KI-Embeddings für Touren"

### 5.3 Detail-Ansicht pro Tabelle

Beim Klick auf eine Tabelle:

* Spaltenliste (Name, Typ, NotNull, Default)

* Indizes (Name, Spalten)

* Optional: kleine Vorschau (erste 10 Datensätze, read-only)

---

## 6. Nutzung

* Dieses Schema ist der **Zielstand** für TrafficApp 3.0.

* Änderungen am Schema sollten immer dokumentiert werden:

  * in Migrations-Scripten (`db/migrations/`)

  * in der Doku (`STATUS_AKTUELL.md` + dieses Dokument)

* Der Admin-Tab „DB-Verwaltung" verwendet diese Infos, um eine transparente Sicht auf die Datenbankstruktur zu geben, ohne dass jemand direkt mit SQL arbeiten muss.

