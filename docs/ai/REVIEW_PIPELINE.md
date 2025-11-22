# TrafficApp 3.0 – KI-Code‑Pattern‑Review & Change‑Management

**Ziel:** Klare, sichere Architektur dafür, **wie** KIs (Cursor/ChatGPT) Code prüfen, Vorschläge machen und optional „sichere Auto‑Fixes" einspielen – ohne das System zu destabilisieren.

**Scope‑Quelle:** `/mnt/data/CODE_REVIEW_PACKAGE_20251122_190723.zip`

---

## 1) Betriebsmodi der KI

* **Advisor‑Modus (Standard)**
  * Nur Review/Kommentare, keine Commits.
  * Output: SARIF + JSON‑Findings + PR‑Kommentar.

* **Safe‑Autofix (Opt‑in)**
  * Kleine, risikoarme Fixes werden als Patch/Commit vorgeschlagen oder direkt als *separater* PR erstellt.
  * Nur innerhalb einer **Allow‑List** (siehe §5).

* **Architect‑Modus (geplant)**
  * Entwurfsdokumente, Migrationsvorschläge, Refactor‑Plans. Keine Code‑Änderung ohne Ticket.

---

## 2) Triggerpunkte

* **PR geöffnet/aktualisiert** → LLM‑Review auf geänderte Dateien.
* **Nightly** → Baseline‑Scan (Security/Patterns) auf `main`.
* **Pre‑merge Check** → nur Advisor, kein Blocker außer bei Security‑Gate (Severity = critical/high).

---

## 3) Pipeline (S0…S5)

* **S0 – Kontextbau**
  * Laden: `STATUS_AKTUELL.md`, `TrafficApp_SECURITY_GUIDE_*.md`, `TrafficApp_ADMIN_NAVIGATION_*`, `ARCHITEKTUR_REVIEW_*`, `Kosten_Optimierungs_Tipps_*`, `Regeln/*`.
  * Repo‑Map (Dateibaum), Diff‑Summary, Tech‑Stack.

* **S1 – Static & Tests**
  * Linters (ruff/flake8), mypy, bandit, pytest (selektive Suiten), build.
  * Artifacts in PR anhängen.

* **S2 – KI Code‑Pattern‑Review**
  * Regeln: `Regeln/CODE_PATTERNS.md` (Do/Don't), Security‑SC‑IDs.
  * Output: `ai_reports/<PR>/<commit>_patterns.jsonl` + SARIF.

* **S3 – KI Security‑Review**
  * Gegen **SC‑Checklist** (SC‑01…SC‑16) prüfen; konkrete Hinweise mit Code‑Zeilen.

* **S4 – Safe‑Autofix (optional)**
  * Nur Allow‑List (siehe §5). Ergebnis als Patch/PR „safe‑autofix/<short‑id>".

* **S5 – Human Gate**
  * Maintainer reviewt; Merge nur nach grünem CI + Zustimmung.

---

## 4) Output‑Formate

* **SARIF 2.1.0** für Code‑Scanning (GitHub/Gitea kompatibel).

* **JSONL Findings**
  ```json
  {"id":"SC-06","severity":"high","file":"backend/app_setup.py","line":42,
   "summary":"CORS zu offen","suggest":"allow_origins auf Prod‑Domains setzen"}
  ```

* **PR‑Kommentar**: Kurzfazit + Top 5 Findings + Link zu Artefakten.

---

## 5) Safe‑Autofix – Allow‑List

Nur diese Klassen von Änderungen sind auto‑erlaubt (sonst Advisor):

* Formatierung, Typo, Kommentar, dead code removal (ohne public API‑Change).
* Linter‑Fixes (ruff/flake8), mypy‑Annotationen (keine Logikänderung).
* **Security‑Header/CORS**: nur wenn Zielwerte in `APP_ENV=production` Feature‑Flag geschützt sind.
* **Upload‑Schutz**: Dateiname‑Whitelist + `resolve()`‑Guard; keine Pfad‑Konstanten ändern.

**Block‑List (nie auto):** Auth/Session, RBAC, DB‑Schema/Migrations, Zahlungs‑/Kostenlogik, OSRM/Geocode‑Algorithmik, Build/Deploy‑Pipelines.

---

## 6) Guardrails („No‑Destroy")

* **Write‑Fence**: KI darf nur Dateien unter `frontend/**`, `backend/routes/**`, `backend/services/**` ändern; Ordner wie `auth`, `db/schema`, `migrations`, `infra/**` sind **read‑only** im Safe‑Modus.

* **Test‑Gate**: Jeder Auto‑Fix → `pytest -q` + Linter müssen grün sein, sonst PR nicht erstellen.

* **Diff‑Budget**: max. 200 Zeilen pro Auto‑Fix‑PR.

* **Policy‑Gate**: Änderungen an sensiblen Dateien benötigen Label `requires‑owner‑approval`.

---

## 7) Prompt‑Design (Kontext‑Pack)

* **System‑Prompt:** Rolle, Ziele, „do no harm", SC‑Checklist, Admin‑Navigation‑Standard (eine Seite mit Tabs), Kosten/Stats‑Leitplanken.

* **Context‑Docs:** die o.g. Dokus + Dateibaum + Diffs.

* **Task‑Prompts:**
  * Pattern‑Review: „Finde Anti‑Patterns, begründe knapp, gib Code‑Snippet + Fix‑Diff."
  * Security‑Review: „Mappe Findings auf SC‑01..SC‑16, priorisiere, liefere Exploit‑Gedanke + Fix‑Snippet."
  * Safe‑Autofix: „Erzeuge minimalen Patch innerhalb Allow‑List, halte Tests grün."

---

## 8) Kosten & Performance

* **Model‑Tiers:** Erst **GPT‑4o‑mini** (Diff‑Scope), Eskalation nur bei high/critical → großes Modell.

* **Caching:** Hash je Datei‑Chunk; unveränderte Chunks nicht neu prüfen.

* **Scope‑Reduce:** Nur geänderte Dateien + 1–2 Hop‑Abhängigkeiten.

---

## 9) Metriken & Qualität

* Acceptance‑Rate der KI‑Vorschläge (% übernommen).
* Zeit bis Review (median), Kosten pro PR.
* „Reopened after merge"‑Rate (Qualitätssignal).

---

## 10) Rollout‑Plan

1. **Phase 1 – Advisor only**: Reviews & SARIF, keine Auto‑Fixes.
2. **Phase 2 – Safe‑Autofix**: nur Allow‑List, Diff‑Budget + Tests.
3. **Phase 3 – Erweiterung**: weitere Allow‑List‑Kandidaten nach Telemetrie.

---

## 11) Dateien & Pfade (Empfehlung)

* `Regeln/CODE_PATTERNS.md` – Do/Don't + Beispiele.
* `docs/ai/REVIEW_PIPELINE.md` – diese Architektur.
* `docs/ai/SAFE_AUTOFIX_POLICY.md` – Allow/Block‑List, Diff‑Budget.
* `ai_reports/` – Artefakte je PR/Commit.
* `.github/workflows/ai_review.yml` – CI‑Workflow (S0–S5).

---

## 12) Beispiel‑CI (Ausschnitt)

```yaml
name: ai-review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: make ci_static && make ci_test
      - name: AI Pattern Review
        run: python tools/ai_review.py --mode=patterns --out ai_reports/${{ github.sha }}
      - name: AI Security Review
        run: python tools/ai_review.py --mode=security --out ai_reports/${{ github.sha }}
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: ai_reports/${{ github.sha }}/report.sarif }
```

---

## 13) Risiken & Gegenmaßnahmen

* **False Positives:** Menschlicher Gate in S5, Advisor bleibt Standard.
* **Kostenexplosion:** Diff‑Scope, Caching, 4o‑mini‑First.
* **Drift von Standards:** Kontext‑Docs aus Repo laden (Single Source of Truth).
* **Security:** Safe‑Autofix nur Allow‑List + Tests; sensitive Bereiche write‑protected.

---

## 14) Nächste Schritte

* `Regeln/CODE_PATTERNS.md` anlegen (Beispiele + Gegenbeispiele).
* Tool `tools/ai_review.py` erstellen (Kontext‑Pack, API‑Calls, JSON/SARIF‑Writer).
* CI‑Workflow hinzufügen; zunächst **Advisor only**.
* Telemetrie sammeln → Safe‑Autofix schrittweise freigeben.

---

**Letzte Aktualisierung:** 2025-11-22

