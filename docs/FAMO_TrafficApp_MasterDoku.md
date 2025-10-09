# FAMO TrafficApp – Master-Dokumentation

**Version:** 2.0 (Entwurf)  
**Stand:** 30.09.2025  
**Referenz:** `docs/Neu/Neue Prompts.md`

---

## Inhaltsverzeichnis
1. [Projektziele & Überblick](#projekziele--überblick)
2. [Architektur nach 8 Schritten](#architektur-nach-8-schritten)
3. [Module & Codepfade](#module--codepfade)
4. [API & Workflows](#api--workflows)
5. [Daten & Persistenz](#daten--persistenz)
6. [Frontend-Konzept](#frontend-konzept)
7. [Tests & Qualitätssicherung](#tests--qualitätssicherung)
8. [Betrieb & Logging](#betrieb--logging)
9. [Roadmap & ToDos](#roadmap--todos)
10. [Anhang & Referenzen](#anhang--referenzen)

---

## Projektziele & Überblick

Die FAMO TrafficApp verarbeitet tägliche Tourplan-CSV-Dateien (TEHA-Export) zu optimierten Fahrzeugrouten. Kernanforderungen:

- Max. 60 Minuten Fahrzeit bis zum letzten Stop (inkl. 2 Minuten Servicezeit pro Kunde).
- BAR-Kunden werden in der Tour visualisiert, aber logisch mit der Haupttour verknüpft.
- KI dient als Kontroll- und Erklärschicht, nicht als Blackbox-Planer.
- Vollständige Nachvollziehbarkeit (Logs, Prompt-Versionierung, reproduzierbare Ergebnisse).
- Betrieb On-Premises (kein Abfluss sensibler Daten).

---

## Architektur nach 8 Schritten

| Schritt | Ziel | Hauptkomponenten |
|---------|------|------------------|
| 1. Datenimport & Vorverarbeitung | CSV lesen, normalisieren, BAR mappen, Duplikate entfernen | `backend/parsers/tour_plan_parser.py`, `scripts/test_csv_parser.py` |
| 2. Geokodierung & Validierung | Adress-→Koordinaten, Geschäftsgebiet prüfen | `backend/services/geocode.py`, `geo_validator.py`, SQLite Cache |
| 3. Zeit-/Distanzmatrix | Depot↔Kunden↔Kunden Fahrzeiten, inkl. Servicezeit-Offset | `backend/services/real_routing.py`, `optimization_rules.py` |
| 4. Clustering | Kunden gemäß 60-Minuten-Regel gruppieren (Sweep + Heuristiken) | `backend/services/multi_tour_generator.py` |
| 5. Tourenreihenfolge | TSP-Heuristik + KI-Optimierung, Kennzahlen berechnen | `multi_tour_generator.py`, `ai_optimizer.py` |
| 6. KI-Kommentare | Touren begründen, Besonderheiten hervorheben | `ai_optimizer.py`, gepl. `ai_commentary_service` |
| 7. Frontend | Karte + Tourliste (Akkordeon), Uploads, Statistiken | React/Leaflet (geplant), MVP unter `docs/Neu/famo_route_app` |
| 8. Tests & Logging | Parser-Golden-Test, Workflow-Logs, Prompt-Versionierung | `scripts/test_csv_parser.py`, `logs/` |

Jeder Schritt ist modular, testbar und kann einzeln weiterentwickelt werden.

---

## Module & Codepfade

### Parser & Import (Schritt 1)
- `backend/parsers/tour_plan_parser.py`
  - `parse_tour_plan(path)` → `TourPlan`
  - `parse_tour_plan_to_dict(path)` → API-Output
  - `export_tour_plan_markdown(plan)` → Markdown-Ausgabe
- `scripts/test_csv_parser.py` – Testet Parser gegen alle CSV-Beispiele
- Legacy (`backend/parsers/csv_parser.py`) entfernt

### Geokodierung & Validierung (Schritt 2)
- `backend/services/geocode.py`: Provideranbindung + Fallbacks
- `backend/services/geo_validator.py`: Adress-/Koordinatenprüfungen
- SQLite-Cache `data/customers.db` (Adressen werden nur einmal geokodiert, Ergebnisse persistiert)

### Routing & Optimierung (Schritt 3–5)
- `backend/services/real_routing.py`: OpenRouteService-Anbindung (in Arbeit); fallback Haversine
- `backend/services/optimization_rules.py`: Zeit/Kosten-Settings (60-Min-Limit, Servicezeit, max Stops)
- `backend/services/multi_tour_generator.py`: Sweep-Heuristik, KI-Optimierung, Kennzahlen
- `backend/services/ai_optimizer.py`: LLM-Integration, Reasoning, Fallback-Strategien
- **Clustering-Logik:** Sweep-Heuristik (Polarwinkel vom Depot), Stopp solange 60-Minuten-Budget (Fahrzeit + 2 Min Servicezeit) nicht überschritten; BAR-Stops bleiben bei zugehöriger Haupttour (Details siehe `docs/Neu/Neue Prompts.md`).

### KI-Kommentare & Report (Schritt 6)
- `backend/services/ai_optimizer.py`: LLM-Integration, Reasoning, Fallback-Strategien
- Geplantes Modul `ai_commentary_service` (RAG/Vectorstore-Anbindung für FAQ & historische Antworten)

### Frontend (Schritt 7)
- MVP: `docs/Neu/famo_route_app`
- Ziel: React + Leaflet, Akkordeon-Tourliste rechts unten, Filter links, BAR-Highlighting.

### Tests & Logging (Schritt 8)
- Parser-Golden-Test: `python scripts/test_csv_parser.py`
- Pytest-Suite: `tests/` (Legacy). Anpassung an neue Pipeline in Planung.
- Logging: `logs/` (CSV-Import, Workflow, KI – wird konsolidiert).

---

## API & Workflows

Detailliert in `docs/Api_Docs.md`. Kernendpunkte:

1. `POST /api/parse-csv-tourplan` – Schritt-1-Parsing (Upload).
2. `POST /api/process-csv-modular` – Komplett-Workflow (Schritte 1–6).
3. `GET /api/workflow-info` – Aktuelle Workflow-Einstellungen.
4. Tour-API (`GET /api/touren`, `GET /api/tours/{id}`) – Legacy, wird migriert.
5. `POST /api/csv-bulk-process` – Ältere Batch-Pipeline; bleibt übergangsweise.

---

## Daten & Persistenz

- **Uploads:** `data/uploads/` – eingehende Tourenpläne.
- **Tourpläne (Quelle):** `tourplaene/`.
- **Geocoding Cache:** SQLite `data/customers.db` (`customers`, `processing_stats`).
- **Logging:** `logs/csv_import_debug.log` u. a.
- **Routenexport:** Geplant `routen/YYYY-MM-DD/`, incl. JSON/PDF.
- **Prompt-/Workflow-Logs:** Aufbau geplant (`ai_logs/`).

---

## Frontend-Konzept

- **Karte (Leaflet)** in der Mitte; zeigt alle Touren.
- **Rechte Spalte** (unter Karte): Akkordeon-Liste aller Touren; `+` klappt Kundenliste, Statistiken und KI-Kommentar aus.
- **Linke Spalte**: Upload-Status, Filter (Datum, Tourtyp, BAR), Workflow-Feedback.
- **Farbkodierung:** BAR-Kunden orange, aktive Tour farbig, andere abgeblendet.
- **Export/Aktionen:** Buttons für CSV-/PDF-Export, Workflow-Restart.

---

## Tests & Qualitätssicherung

- **Parser:** `scripts/test_csv_parser.py` (alle CSVs).
- **Services:** Pytest (neu aufzubauen) für Geocode, Clustering, Optimierung.
- **Integration:** geplanter End-to-End-Test: Upload → Workflow → Tour-Ergebnis → Export.
- **Legacy-Tests:** `tests/test_api_health.py`, `tests/test_api_summary.py` aktualisieren.

---

## Betrieb & Logging

- **Start:** `python start_server.py` (FastAPI), optional `uvicorn backend.app:app --reload --port 8000`.
- **Konfiguration:** `.env` (Routing-/KI-Keys), `ai_models/config.json` (Modelle), `optimization_rules.py` (Parameter).
- **Logging:**
  - CSV-Import: RotatingFileHandler → `logs/csv_import_debug.log`
  - Workflow: Logging im Orchestrator (inkl. Schrittstatus, Fehler)
  - KI: Prompt/Response-Logging (geplant)
- **Monitoring:** `GET /health`, `/api/db-status`, `/api/llm-status`; Erweiterung geplant.

---

## Roadmap & ToDos

| Bereich | Aufgabe | Status |
|---------|---------|--------|
| Parser | Legacy (pandas) komplett entfernen | 🔄 in Arbeit |
| Geokodierung | Batch-/Status-API veröffentlichen | 🟡 geplant |
| Routing | OpenRouteService produktiv nutzen, Matrix-Endpunkt | 🟡 geplant |
| Optimierung | Async-Workflows, Job-Status-API | 🟡 geplant |
| KI-Kommentare | Eigenes Modul + Endpunkte | 🟡 geplant |
| Frontend | React/Leaflet mit Akkordeon-Liste | 🔄 gestartet (MVP vorhanden) |
| Logging | Einheitliches Schema + Prompt-Archiv | 🟡 geplant |
| Doku | README, Guides, API synchronisieren | 🔄 laufend |
| Tests | Pytest-Suite für Pipeline | 🟡 geplant |

---

## Anhang & Referenzen

- **Prompts & Strategie:** `docs/Neu/Neue Prompts.md`
- **Parser-Quellen (historisch):** `docs/Neu/parse_w7.py`, `docs/Neu/parse_all_tours.py`
- **MVP-Webapp:** `docs/Neu/famo_route_app`
- **Alte Doku (Legacy):** `docs/PROJEKT_DOKUMENTATION_FINAL.md` – wird sukzessive abgelöst
- **Logs & Testdaten:** `logs/`, `tests/test_data/`

> Diese Master-Dokumentation ist der Single Source of Truth. Änderungen an API, Architektur oder Workflow erfordern eine sofortige Aktualisierung.
