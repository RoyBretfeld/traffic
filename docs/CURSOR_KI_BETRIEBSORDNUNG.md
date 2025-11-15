# Cursor‑KI Betriebsordnung – TrafficApp (Post‑Erkennung)

**Ziel:** Cursor‑KI soll *geordnet, deterministisch und nachvollziehbar* implementieren – keine Experimente am Eingangsbereich (Erkennung/CSV), keine unkontrollierten Code‑Änderungen. Alles beginnt **ab Übergabepunkt „Touren erkannt"**.

**Scope (fix):**

* **Unberührt:** Erkennung der Touren & CSV‑Input. Nichts daran ändern.
* **Im Fokus:** Adapter → UID‑Erzeugung → Normalisierung (Repair/Patterns) → GeoQueue → OSRM‑Nutzung (Table/Route) → Optimierung → LLM‑Fallback (guarded) → Admin‑APIs/Telemetry.
* **Stack/Ports:** FastAPI (Pydantic v2), Python ≥3.11, SQLite, Router/OSRM (mld) vor OSRM, Ports **5500/5510**.

---

## 0) Grundprinzipien (nicht verhandelbar)

* **Determinismus:** Gleicher Input ⇒ gleicher Output. Keine Zufallsquellen, keine kontextabhängigen Zeiten. Sortierung und Tie‑Breaker festlegen.
* **Vertragstreue:** Eingehendes Touren‑Format bleibt stabil (siehe §1). Keine Änderung/Umbenennung von Feldern upstream.
* **Defense‑in‑Depth:** Blacklist → Exact → Regex → Gazetteer/Postal → Rules → LLM (nur als Fallback, temp=0, JSON‑Schema, verifiziert).
* **Transparenz:** Jede Änderung durch Events/Metriken belegbar (Audit‑Log, Stats‑API). Kein „silent fix‑up".
* **Sicherheitsgurt:** Fehler ⇒ Quarantäne/HTTP‑4xx, *nicht* heuristisch weiterrechnen.

---

## 1) Übergabepunkt (Kontrakt von Erkennung → Engine)

**Input (gegeben, unverändert):**

```json
{
  "tours": [
    {
      "tour_id": "ext-2025-11-01-A",
      "label": "…",
      "stops": [
        {
          "source_id": "ROW-12345",
          "label": "Kunde …",
          "address": "Fröbelstraße 10, Dresden",
          "lat": 51.0,
          "lon": 13.7,
          "time_window": {"start": "08:00", "end": "12:00"},
          "attrs": { }
        }
      ]
    }
  ]
}
```

**Cursor‑KI:** Input *nicht* verändern. Adapter auf unserer Seite übernimmt Normalisierung und UID‑Erzeugung.

---

## 2) Adapter & interne UIDs

* `tour_uid = sha256(tour_id)` (Hex, lower).
* `stop_uid = sha256(source_id | norm(address) | plz | ort)` – norm() via Repair‑Layer (NFKC, Umlaut‑Folding, Trim) + Pattern‑Engine (OT/Slash/Dash etc.).
* `stop_uid` ist Pflicht. Fehlen `lat/lon` ⇒ GeoQueue einplanen, bis dahin **keine Optimierung**.

---

## 3) Engine‑APIs (ab Übergabe)

* `POST /engine/tours/ingest` – akzeptiert Erkennungsformat, erzeugt UIDs, normalisiert, plant Geo.
* `GET  /engine/tours/{tour_uid}/status` – `pending_geo|ready|optimized|failed`, inkl. Countern.
* `POST /engine/tours/optimize` – optimiert nur vollständige Touren (alle Stops mit `lat/lon`).
* `POST /engine/tours/split` – Subtourenbildung anhand **OSRM Table** (Fahrzeiten), optional mit `time_window`/Kapazität.

**Antwortschema (Optimize):**

```json
{
  "tour_uid": "…",
  "route": ["<stop_uid>", "<stop_uid>", …],
  "meta": {"objective": "time"}
}
```

**Valider Zwang:** `set(route) == set(valid_stop_uids)` **und** `len(route) == n`. Sonst 400 + Quarantäne.

---

## 4) OSRM‑Nutzung (vor LLM, strikt)

* **Client:** `ROUTER_URL` (Router‑Service vor OSRM), `connect_timeout=1.5s`, `read_timeout=8s`, Retry 2× (idempotente GETs), Circuit‑Breaker (Trip 5/60s, Halb‑Offen 30s).
* **Endpunkte:** `GET /table/v1/driving/{coords}?annotations=duration` und `GET /route/v1/driving/{coords}?overview=false&steps=false`.
* **Split‑Strategie:** 1) Clustern (DBSCAN/K‑Means, projiziert) → 2) Optimieren je Cluster (Nearest‑Insertion + 2‑Opt Light) → 3) concat.
* **Fallback:** OSRM down ⇒ Haversine × **1.3** Sicherheitsfaktor + `osrm_unavailable` Metric.

---

## 5) LLM‑Guard‑Rails

* **Nur Fallback:** wenn Heuristik/OSRM nicht eindeutig.
* **Prompt‑Inhalt:** ausschließlich `stop_uid` (+ optionale Labels/Constraints), keine Indizes/Koordinaten.
* **temperature=0**, **response_format=json**; Erwartetes Schema s. Optimize‑Antwort.
* **Validierung (hart):** Pydantic‑Schema + Set‑Gleichheit; bei Fehler **kein** „Auto‑Fix" – 422 + Quarantäne.
* **Logging:** Prompt‑Hash, Response‑Hash, Tokenkosten, Latenz; `llm_usage_ratio < 5%` Ziel.

---

## 6) Pattern‑Engine & Repair‑Layer (Post‑Erkennung)

* Reihenfolge: Repair → Pattern Lookup (Exact/Regex) → Gazetteer/Rules → LLM (nur Fallback, staged).
* **Promotion‑Gates:** `confidence ≥ 80`, `support ≥ 2`, Golden‑Precision ≥ 99%, kein Konflikt, versionskompatibel.
* **Konflikte:** `pattern_conflicts` + Admin‑Review (Promote/Disable/Generalize/Blacklist). Keine Auto‑Aktivierung aus LLM.

---

## 7) Coding‑Standards (Cursor‑KI muss erzwingen)

* Python ≥3.11, **Pydantic v2**, FastAPI; `TZ=UTC`, `LC_ALL=C.UTF-8` in allen Services.
* **Keine** globalen Zustände; Repos/Services als Konstruktor‑Dependencies.
* **Konfiguration:** nur via ENV (12‑Factor): `ENGINE_VERSION|RULESET_VERSION|REPAIR_VERSION|ROUTER_URL` etc.
* **HTTP:** Zeitouts/Retry/Circuit‑Breaker zentral in Client; keine Ad‑hoc‑Requests im Codepfad.
* **Fehlerbehandlung:** 4xx für Userfehler, 5xx für Systemfehler; niemals 200 bei Fehlvalidierung.
* **Logging:** strukturiert (JSON), Felder: `correlation_id`, `tour_uid`, `stop_uid`, `phase`, `latency_ms`.
* **Metriken:** Prometheus‑kompatibel, s. §10.
* **Dependencies:** versionsfix (`==`), kein Sniffing (CSV), kein `random` ohne Seed.

---

## 8) Tests & CI (Gatekeeper)

* **Golden‑Tests** für Problemstraßen (Fröbelstraße, Löbtauer, Mosen, Bärensteiner, Österreicher, Straße der MTS).
* **Property‑Tests:** Idempotenz Repair/Pattern (zweimal = einmal), Set‑Gleichheit Route.
* **Snapshot‑Tests:** Optimize‑Antworten (mit fixen Seeds).
* **Coverage ≥ 80%**, Lint/Typecheck (ruff/mypy), Pre‑commit Hooks.
* **CI‑Fail** wenn irgendein DoD‑Kriterium bricht.

---

## 9) PR‑Prozess (Anti‑Chaos‑Regeln)

* Branch‑Namen: `feat/engine-…`, `fix/osrm-…`, `chore/telemetry-…`.
* Commit‑Nachrichten (Conventional): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.
* **PR‑Checklist (Cursor automatisch anhängen):**

  * [ ] Keine Änderungen an Erkennung/CSV & deren Schemas.
  * [ ] API‑Kontrakte unverändert (oder Migrationsnotiz enthalten).
  * [ ] Tests grün (Golden/Property/Snapshot) & Coverage ≥ 80%.
  * [ ] Timeouts/Retry/Circuit‑Breaker konfiguriert (OSRM).
  * [ ] LLM‑Pfad strikt validiert, Quotenmetriken hinzugefügt.
  * [ ] Metriken & Logs erweitert.

---

## 10) Telemetrie & Alarme

**Metriken:**

* Tours: `tours_ingested`, `tours_ready`, `tours_pending_geo`, `optimize_success`, `optimize_fail`.
* Routing: `osrm_table_latency_ms`, `osrm_unavailable`, `split_subroutes_count`.
* LLM: `llm_calls`, `llm_invalid_schema`, `llm_usage_ratio` (<5%).
* Patterns: `pattern_lookup_hit_ratio`, `pattern_conflict_count`, `pattern_staged_backlog`.

**Alarme:**

* `osrm_unavailable > 0` in 5min ⇒ Warnung.
* `llM_invalid_schema > 0` ⇒ Review.
* `tours_pending_geo` steigt 3 Intervalle ⇒ GeoQueue prüfen.

---

## 11) DoD (Definition of Done)

* Erkennungsinput 1:1 ingestiert; UIDs korrekt; Geo‑Status sichtbar.
* Optimize/Split nutzen **OSRM Table** (Fallback gezählt/alarmsiert).
* LLM nur Fallback; strikt validiert; `llm_usage_ratio < 5%` in Staging.
* Pattern‑Promotion ausschließlich via Gates + Event `promoted`.

---

## 12) Cursor‑KI Arbeitsaufträge (konkret, nacheinander)

1. **Adapter & `/engine/tours/ingest`**: UIDs generieren, Normalisierung anwenden, GeoQueue markieren; Status‑API.
2. **OSRM‑Client**: Timeouts/Retry/Circuit‑Breaker; `table`+`route` Wrapper mit Tests.
3. **Split & Optimize**: Cluster → Heuristik → Route; harte Set‑Validierung.
4. **LLM‑Fallback** (optional): Prompt/Schema/Validator/Telemetry; Feature‑Flag `LLM_FALLBACK=guarded`.
5. **Admin‑API Erweiterung**: Review/Promote/Disable/Blacklist; Stats‑Endpoint.
6. **Telemetry & Alarme**: Metriken/Counter & Dash‑Panels; Schwellwerte aktivieren.

---

## 13) Verbote (Anti‑Anarchie‑Liste)

* ❌ Keine Änderungen an CSV/Erkennung oder deren Feldnamen.
* ❌ Kein Index‑Mapping/Koordinatenvergleich als Identität – nur `stop_uid`.
* ❌ Kein LLM ohne Schema/Validierung/Verifikation.
* ❌ Keine externen HTTP‑Calls ohne zentralen Client/Timeout/Retry.
* ❌ Keine „silent fixes" – Fehler müssen sichtbar/quittiert sein.

---

## 14) Vorlagen & Snippets (Kurz, für Cursor)

**UID‑Hash:** `sha256(f"{source_id}|{norm_addr}|{plz}|{ort}")`

**Optimize Response Schema (Pydantic):**

```python
class OptimizeResponse(BaseModel):
    tour_uid: str
    route: list[str]  # stop_uids
    meta: dict = {"objective": "time"}
```

**Set‑Validierung (harte Regel):**

```python
assert set(resp.route) == set(valid_stop_uids) and len(resp.route) == len(valid_stop_uids)
```

**OSRM Table Call (Policy):** `connect_timeout=1.5s`, `read_timeout=8s`, Retry=2, CB: Trip 5/60s, Half‑Open 30s.

---

> **Merksatz für Cursor‑KI:** *„Erkennung bleibt wie sie ist. Ab Übergabe arbeite deterministisch, nutze OSRM vor LLM, validiere strikt – und protokolliere alles."*

