# FAMO TrafficApp – Architekturübersicht

Diese Architektur folgt dem in `docs/Neu/Neue Prompts.md` definierten 8‑Schritte-Prozess. Jeder Schritt bildet ein eigenständiges Modul mit klaren Ein- und Ausgaben. Die Module lassen sich einzeln testen, beobachten und versionieren.

---

## 1. Datenimport & Vorverarbeitung

- **Input**: Tourplan-CSV (`tourplaene/Tourenplan*.csv`) oder Upload via API.
- **Komponente**: `backend/parsers/tour_plan_parser.py` (`parse_tour_plan_to_dict`).
- **Aufgaben**:
  - Lesen semikolon-separierter Tourpläne (Latin1-Encoding).
  - Normalisieren deutscher Sonderzeichen (ä→ae, ö→oe, ü→ue, ß→ss).
  - BAR-Touren dem nachfolgenden Haupttourblock zuordnen.
  - Deduplizieren identischer Kunden (KdNr + Adresse).
- **Output**: `TourPlan`-Datensatz (`metadata`, `tours`, `customers`, `stats`).
- **Persistenz**: temporäre Datei im Upload-Verzeichnis (`data/uploads`).
- **Tests**: `scripts/test_csv_parser.py` prüft sämtliche CSV-Beispiele.

## 2. Geokodierung der Adressen

- **Input**: Kundenliste aus Schritt 1.
- **Komponenten**: `backend/services/geocode.py`, `geo_validator.py`.
- **Aufgaben**:
  - Adresse zusammenbauen (`street`, `postal_code`, `city`).
  - Geokoordinaten über Provider (z. B. OpenRouteService / Nominatim) ermitteln.
  - Ergebnisse in SQLite (`data/customers.db`, Tabelle `customers`/`geocache`) speichern, um wiederholte Anfragen zu vermeiden.
  - Fallback-Koordinaten per PLZ-Heuristik; Validierung (Bounding-Box, Geschäftsgebiet).
- **Output**: Kundenliste mit `lat`, `lon`, `geocoded`, `source` + persistiertem Cache-Eintrag.
- **Monitoring**: Logging in `logs/csv_import_debug.log`, Trefferquote / Fallback-Rate in Workflow-Stats.

## 3. Reisezeit- & Distanzmatrix

- **Input**: Depotkoordinaten + Kunden aus Schritt 2.
- **Komponenten**: `backend/services/real_routing.py` (OpenRouteService), `backend/services/optimization_rules.py` (Geschwindigkeiten, Servicezeiten).
- **Aufgaben**:
  - Erzeugen symmetrischer Zeitmatrix (Depot ↔ Kunden, Kunde ↔ Kunde).
  - Ergänzen fester Servicezeit (Standard: 2 Minuten pro Halt).
  - Speichern der Matrix im Workflow-Kontext (In-Memory / Cache für Optimierung).
- **Output**: `time_matrix[index_a][index_b]` in Minuten + Distanzmatrix.
- **Anmerkung**: Bei fehlender Routing-API fallback auf Haversine (Offline-Modus) möglich.

## 4. Kundenclustering unter Zeitrestriktionen

- **Input**: Kunden + Zeitmatrix.
- **Komponenten**: `backend/services/multi_tour_generator.py` (Sweep-Heuristik + KI-Fallback), `optimization_rules.py` (Maximalwerte).
- **Geschäftsregeln**:
  - Max. 60 Minuten Fahrzeit bis zum letzten Kunden (inkl. Servicezeiten).
  - BAR-Kunden verbleiben in der zugehörigen Haupttour.
  - Tourstart/-ende: Depot FAMO Dresden.
- **Ablauf**:
  1. Sweep-Heuristik sortiert Kunden nach Polarwinkel.
  2. Zeitbudget wird sukzessive geprüft; überschreitet es 60 Minuten, startet neuer Cluster.
  3. KI-Optimierung kann alternative Cluster vorschlagen.
- **Output**: Liste von Tourgruppen (`GeneratedTour` Rohdaten ohne Reihenfolge oder geordnete Stoppfolgen je nach Modus).

## 5. Tourenreihenfolge optimieren (TSP)

- **Input**: Cluster aus Schritt 4.
- **Komponenten**: `backend/services/multi_tour_generator.py`, `AIOptimizer`, heuristische Verfahren (Nearest Neighbour, 2-Opt, KI).
- **Aufgaben**:
  - Reihenfolge der Stops pro Cluster minimieren (Zeit + Distanz).
  - Zeitbudget prüfen (Fahrzeit + Service + Rückfahrt).
  - Kennzahlen berechnen (Gesamtdauer, Distanz, Kosten).
- **Output**: `GeneratedTour` mit finaler Sequenz, Schätzungen, Constraint-Status, Optimierungsnotizen.

## 6. KI-Kommentare & Report

- **Input**: Optimierte Touren + Statistiken.
- **Komponenten**: `backend/services/ai_optimizer.py` (für reasoning), geplantes Modul `ai_commentary_service` (TODO, inkl. RAG/Vectorstore für Kontextwissen)
- **Aufgaben**:
  - Zusammenfassung jeder Tour in natürlicher Sprache (Begründung Reihenfolge, Verkehr, BAR-Hinweise).
  - Vergleich verschiedener Touren (Zeiteinsparungen, Clusterwechsel).
  - Logging & Prompt-Versionierung in `logs/` (zukünftig `ai_logs/`).
- **Output**: KI-Kommentare pro Tour + Gesamtbericht.

## 7. Frontend-Integration & Darstellung

- **Technologie**: React (geplant) + Leaflet; aktuelles MVP (`docs/Neu/famo_route_app/frontend/index.html`).
- **Layout-Vorgaben**:
  - **Rechte Seite (unter Karte)**: Liste aller Touren als Akkordeon (Tourtitel, z. B. `W-07:00 Uhr`), expandierbar via `+`.
  - **Linke Seitenleiste**: Filter (Datum, Tourtyp), Upload-Status.
  - BAR-Kunden farblich (orange) hervorheben.
  - Statistiken (Stops, Dauer, Distanz) je Tour + Gesamtübersicht.
- **Kommunikation**: REST Endpoints (`/api/parse-csv-tourplan`, `/api/csv-bulk-process`, `/api/csv-summary/{filename}`) + Websocket (geplant) für Live-Updates.

## 8. Tests, Logging & Prompt-Versionierung

- **Tests**:
  - Parser: `scripts/test_csv_parser.py` (Golden-File-Lauf über alle Tourpläne).
  - Services: pytest-Module (TODO) für Geocoding, Routing, Clustering.
  - End-to-End: Upload → Tourenliste → Export (geplant `tests/test_api_summary.py` Erweiterung).
- **Logging**:
  - CSV-Verarbeitung: `logs/csv_import_debug.log`.
  - AI-Interaktionen: geplanter Logger mit Prompt-/Response-Archiv.
  - Routing/Fehler: Standard FastAPI Logging + RotatingFileHandler.
- **Versionierung**:
  - Jeder Prompt erhält ID + Version; Speicherung mit Response für Audits.
  - Exportierte Touren (`routen/YYYY-MM-DD/`) werden signiert/gehasht (TODO).
- **Monitoring**:
  - Kontextinformationen zu Laufzeiten, Erfolgsquoten, Geocoding-Fallback-Rate.

---

## Datenfluss-Zusammenfassung

1. Nutzer lädt CSV hoch → Parser (Schritt 1).
2. Geokodierung ergänzt Koordinaten + Validierung (Schritt 2).
3. Routing erstellt Zeitmatrix (Schritt 3).
4. Clustering erzeugt Tourgruppen (Schritt 4).
5. TSP-Optimierung bestimmt Reihenfolge + Kennzahlen (Schritt 5).
6. KI generiert kommentierte Reports (Schritt 6).
7. Frontend zeigt Tourenliste + Karte + Kommentare (Schritt 7).
8. Tests & Logs sichern Qualität, Prompts werden versioniert (Schritt 8).

Jeder Schritt kann unabhängig deployt und observiert werden. Fehlerfälle (z. B. fehlende Geodaten, Zeitlimit überschritten) werden früh erkannt und mit Vorschlägen zur Korrektur an das Frontend gemeldet.

