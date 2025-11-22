# TrafficApp 3.0 – Hardening TODO (Restkiste)

**Scope/Ref:** `/mnt/data/CODE_REVIEW_PACKAGE_20251122_190723.zip`

Kompakte Aufgabenliste zur Stabilisierung, Performance‑Tuning und Datenqualität. Jede Zeile = 1 Ticket.

---

## 1) Code & API

* [HT-01] API **Versionierung** einführen: Prefix `/api/v1/*`; Deprecation‑Pfad dokumentieren.

* [HT-02] **Pydantic‑Validation** schärfen (Limits für Stops, Dateigröße, Status‑Enum, Koordinatenbereich, ISO‑Datetime).

* [HT-03] **Idempotency** beim Import: `idempotency_key` (Header/Param) + Server‑Side Dedupe.

* [HT-04] Einheitlicher **Error‑Contract** (code/message/trace_id) für alle Endpoints.

* [HT-05] **CSV‑Injection** beim Export entschärfen (`= + - @` prefixen/escapen).

---

## 2) Datenmodell & DB

* [HT-06] SQLite PRAGMAs setzen: `WAL`, `synchronous=NORMAL`, `foreign_keys=ON`.

* [HT-07] Indizes: `tours(tour_plan_id)`, `tour_stops(tour_id,sequence)`, `tour_events(tour_id,created_at)`, `stats_daily(date,region)`, `customers(external_id)`.

* [HT-08] Constraints: `CHECK(lat BETWEEN -90 AND 90)`, `CHECK(lon BETWEEN -180 AND 180)`, `CHECK(score_success BETWEEN 0 AND 100)`.

* [HT-09] **Zeitzonen/Einheiten** vereinheitlichen: Zeiten in UTC, Distanzen intern in Metern; UI rendert km.

* [HT-10] **Tourplan‑Totals** materialisieren (km/min/kosten) beim Plan‑Abschluss.

---

## 3) Performance

* [HT-11] **Geocoding‑Cache** (Adresse→lat/lon) mit TTL; Backoff/Retry. ✅ **Bereits vorhanden** (`geo_cache` Tabelle)

* [HT-12] **OSRM‑Cache** (Koord‑Paar→Distanz/Zeit) + Table‑API batching. ✅ **Bereits vorhanden** (`osrm_cache` Tabelle)

* [HT-13] **CSV‑Streaming** & Chunk‑Parsing für große Dateien; Progress Events.

---

## 4) Admin‑UI & UX

* [HT-14] Eine **Admin‑Seite mit Tabs** (Policy durchziehen) – alle Module dort einhängen. ⚠️ **In Arbeit** (AR-09)

* [HT-15] **Loading/Skeletons** + klare Empty‑States statt Null‑Charts.

* [HT-16] **ENV‑Badge** (DEV/PROD) + Debug‑Schalter nur in DEV.

* [HT-17] **Drilldown**: Woche → Tag → Tourplan → Tour.

---

## 5) Sicherheit (ergänzend zum Security‑Guide)

* [HT-18] **Session‑Rotation** nach Login (Fixation vermeiden).

* [HT-19] **Audit‑Log** für Import/Geocoding/Kosten‑Änderungen/Exports.

* [HT-20] **ETag/Cache‑Control** für statische Assets; CSP‑Nonces wenn Inline‑JS nötig.

---

## 6) Ops & Observability

* [HT-21] **Job‑Runner/Queues** (import/geocode/stats/embeddings) mit Retries & Dead‑Letter + Health/Ready‑Probes. ⚠️ **Geplant** (AR-01)

* [HT-22] **Metriken**: `queue_length_*`, `geocode_failed_total`, `osrm_failed_total`, `import_duration_ms`, `stats_agg_duration_ms`, `requests_latency_bucket`.

* [HT-23] **Backups & VACUUM** (SQLite) planen; Restore‑Playbook testen.

---

## 7) Tests

* [HT-24] **Property‑Based Tests** für CSV‑Parser (Delimiter/Encoding/Missing Fields) via Hypothesis.

* [HT-25] **Contract‑Tests** der API (Error‑Shapes, Limits, Auth‑Pflicht).

* [HT-26] **Load‑Tests light** (Import 10k Stops, Geocode‑Burst) mit Locust/Gatling.

---

## 8) Recht & Datenschutz

* [HT-27] **PII‑Reduktion** in Logs (Adressen kürzen); **Retention** definieren.

* [HT-28] **Export/Deletion‑Pfad** pro Kunde/Tourplan (DSGVO‑Support).

---

## Snippets

**SQLite PRAGMAs (on connect):**
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
```

**Error‑Contract (Beispiel):**
```json
{"error":{"code":"IMPORT_SIZE_LIMIT","message":"CSV zu groß","trace_id":"…"}}
```

**CSV‑Injection Schutz (Server‑Side):**
* Felder, die mit `=`, `+`, `-`, `@` beginnen → Präfix `'` setzen oder als Text quoted exportieren.

---

**Letzte Aktualisierung:** 2025-11-22

