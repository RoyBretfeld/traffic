
# Traffic Ingest Engine (TIE) — Minimalpaket

**Maintainer/Architekt:** Roy Bretfeld – FA: RH - Automation  
**API-Port:** 5500 (anpassbar in `run.sh`)

Dieses Repo/Archiv enthält eine lauffähige Minimal-Version der **Traffic Ingest Engine (TIE)** auf Basis von **FastAPI** und **SQLite**. Ziel: deterministisches Normalisieren von Adressen mit selbstlernender Pattern-DB, klaren Gates und Admin-APIs.

---

## Inhalte

- `app.py` — FastAPI-Service mit Endpunkten:
  - `POST /engine/ingest` → Batch-Normalisierung (Hot-Path: Exact → Regex → Rules)
  - `POST /api/patterns/upsert` → Pattern anlegen (staged/active etc.)
  - `POST /api/patterns/{id}/promote` → Promotion gemäß Gate-Schwellen
  - `GET  /api/patterns/stats` → Überblick über Status & Konflikte
- `patterns.py` — Pattern-Store & deterministische Auswahl (Scoring: Quelle/Exact/Confidence/Support).
- `repair_text.py` — Unicode-Cleanup + `make_input_norm()` als kanonischer Schlüssel.
- `migrations/005_patterns.sql` — Schema: `patterns`, `pattern_blacklist`, `pattern_conflicts`, `pattern_events`, Trigger.
- `tools/pattern_revalidate.py` — Nightly-Promotion für `staged` gemäß Gates.
- `.env.example` — Engine-Versionen, Gate-Schwellen, Owner, DB-Pfad.
- `requirements.txt`, `run.sh`, `README.md` (Kurzstart).

---

## Verzeichnisstruktur

```
tie_minimal/
├─ app.py
├─ patterns.py
├─ repair_text.py
├─ migrations/
│  └─ 005_patterns.sql
├─ tools/
│  └─ pattern_revalidate.py
├─ requirements.txt
├─ .env.example
├─ run.sh
└─ README.md
```

---

## Installation & Start (lokal)

```bash
unzip traffic_ingest_engine_minimal.zip -d tie_minimal
cd tie_minimal
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./run.sh
```

Der Service läuft danach auf `http://localhost:5500`.

---

## Quick-Smoke-Test

```bash
curl -s http://localhost:5500/engine/ingest -X POST -H "content-type: application/json"   -d '[{"raw_address":"Bannewitz, OT Posen"},{"raw_address":"Byrna / Bürkewitz"},{"raw_address":"Bad Gottloiba - Berghübel"}]' | jq
```

Erwartung: Normalisierte Ortsnamen (z. B. „Bannewitz“, „Byrna“, „Bad Gottloiba“) basierend auf Rules (OT-/Slash-/Dash-Split).

---

## Admin-Flow (Beispiel)

**Pattern anlegen (staged):**
```bash
curl -s http://localhost:5500/api/patterns/upsert -X POST -H "content-type: application/json"   -d '{"input_text":"Byrna / Bürkewitz","normalized_output":"Byrna","pattern_type":"slash_split","source":"manual","status":"staged","confidence_pct":90,"support_count":2}'
```

**Promoten (Gates: `confidence_pct ≥ 80`, `support_count ≥ 2`):**
```bash
curl -s http://localhost:5500/api/patterns/1/promote -X POST
```

**Statistiken ansehen:**
```bash
curl -s http://localhost:5500/api/patterns/stats | jq
```

---

## API-Referenz (Minimal)

### `POST /engine/ingest`
Batch-Normalisierung von Rohadressen.

**Request-Body:**
```json
[
  {"raw_address": "Bannewitz, OT Posen"},
  {"raw_address": "Byrna / Bürkewitz"},
  {"raw_address": "Bad Gottloiba - Berghübel"}
]
```

**Response-Body (Beispiel):**
```json
[
  {"norm_address":"Bannewitz","pattern_id":null,"score":335,"escalated":false,"blocked":false},
  {"norm_address":"Byrna","pattern_id":null,"score":285,"escalated":false,"blocked":false},
  {"norm_address":"Bad Gottloiba","pattern_id":null,"score":285,"escalated":false,"blocked":false}
]
```

### `POST /api/patterns/upsert`
Legt ein Pattern an oder markiert Konflikt (409), wenn abweichender Output zum selben `input_norm`/`pattern_type` existiert.

**Body:**
```json
{
  "input_text": "Byrna / Bürkewitz",
  "normalized_output": "Byrna",
  "pattern_type": "slash_split",
  "source": "manual",
  "status": "staged",
  "confidence_pct": 90,
  "support_count": 2
}
```

**Antwort:**
```json
{"status":"ok","id":1}
```
oder bei Konflikt:
```json
{"status":"conflict","message":"conflict recorded"}
```

### `POST /api/patterns/{id}/promote`
Befördert ein `staged`-Pattern auf `active`, wenn Gate-Schwellen erfüllt sind. Optional Parameter `min_conf`, `min_support`.

**Antwort:**
```json
{"status":"ok"}
```
oder
```json
{"status":"not-promoted"}
```

### `GET /api/patterns/stats`
Aggregierte Übersicht.

**Antwort (Beispiel):**
```json
{
  "patterns": {"staged": 3, "active": 5, "disabled": 0, "conflicted": 0, "deprecated": 0},
  "conflicts": 1
}
```

---

## Konfiguration (.env)

```env
ENGINE_VERSION=1.0.0
RULESET_VERSION=2.1
REPAIR_VERSION=1.3

# Gates
PATTERN_GATE_MIN_CONF=80
PATTERN_GATE_MIN_SUPPORT=2
PATTERN_PROMOTE_AUTOMATICALLY=false
PATTERN_AUTO_LEARN=rules_only
PATTERN_REGEX_ALLOWED=true
PATTERN_VERSION_ENFORCE=true

# Owner
ENGINE_OWNER="Roy Bretfeld – FA: RH - Automation"
ENGINE_OWNER_ROLE="Architect"

# DB
DB_PATH=./tie.sqlite
TZ=UTC
LC_ALL=C.UTF-8
```

---

## Betriebsnotizen

- **Determinismus:** Feste Kandidatenreihenfolge (Blacklist → Exact → Regex → Rules) und stabiler Score mit Tie-Breaker über ID.
- **Selbstlernen (Minimal):** Neue sichere Treffer können als `staged` persistiert und nach Gates promoted werden.
- **Konflikte:** Abweichende Outputs pro `input_norm`/`pattern_type` werden in `pattern_conflicts` protokolliert (HTTP 409).
- **Nightly-Revalidate:** `tools/pattern_revalidate.py` kann via systemd/Taskplaner ausgeführt werden, um `staged` → `active` zu prüfen.
- **Erweiterbar:** Gazetteer/Postal-Lookup, Admin-Review/Blacklist/Generalize-UI, Golden-Tests, OSRM/Geocoder-Checks als nächste Schritte.

---

## Lizenz/Attribution

© Roy Bretfeld – FA: RH - Automation / FAMO Dresden. Alle Rechte vorbehalten.  
Dieses Minimalpaket dient als Startpunkt und kann projektspezifisch erweitert werden.
