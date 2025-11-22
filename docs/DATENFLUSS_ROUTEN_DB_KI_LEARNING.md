# TrafficApp 3.0 – Datenfluss, Routen-DB & KI-Learning

## 1. Ziel dieses Dokuments

Dieses Dokument beschreibt den **End-to-End-Flow** der Daten in der TrafficApp 3.0:

* Von der **Tourenplanung** (CSV-Import)
* über **Durchführung & Speicherung** in der Datenbank
* bis hin zu **KI-Auswertung & optionaler Vektor-Datenbank**.

Es dient als Grundlage für:

* Adminbereich (Reiter: Daten / DB / KI)
* Entwickler (Backend, KI-Module)
* Dokumentation für externe KIs (z.B. Cursor / ChatGPT)

---

## 2. High-Level-Datenfluss (Überblick)

1. CSV-Tourenplan wird hochgeladen.
2. Backend parst CSV, legt eine geplante Tour-Struktur an.
3. OSRM + Optimierung berechnen die Route(n) und Sub-Routen.
4. Fahrer führt die Tour real aus (Ist-Daten entstehen: Zeiten, Abweichungen etc.).
5. Nach Tourabschluss werden **Ist-Daten + Kennzahlen** in der relationalen DB gespeichert.
6. Ein Hintergrundprozess (Job/Worker) erzeugt daraus **KI-Features**:

   * Kennzahlen (Score, Delay, Qualität)
   * Embeddings für eine Vektor-Datenbank (optional)

7. Bei neuen Touren nutzt die App:

   * Historische Daten, Statistiken und ggf. Vektor-Ähnlichkeitssuche
   * zur Verbesserung von Optimierung und Vorschlägen.

8. Im Adminbereich kann dieser Flow eingesehen und kontrolliert werden.

---

## 3. Relationale Datenbank – Kern-Tabellen

### 3.1 Tabelle: `tours`

**Zweck:** Repräsentiert eine komplette Tour (Plan + Ergebnis) als Einheit.

**Beispielschema (konzeptionell):**

* `id` (PRIMARY KEY)
* `date` (Datum der Tour)
* `driver_id` (Referenz auf Fahrer/Benutzer)
* `region` (z.B. Dresden Nord, Dresden Süd)
* `status` (z.B. `planned`, `in_progress`, `completed`, `aborted`)
* `distance_planned_km` (geplante Strecke)
* `distance_real_km` (real gefahrene Strecke)
* `total_delay_minutes` (Summe der Verspätungen)
* `score_success` (0–100, kombiniert aus Distanz + Pünktlichkeit + Stabilität)
* `created_at`
* `updated_at`

**Bemerkung:**

* `score_success` ist wichtig für das spätere KI-Lernen (Belohnung / Bewertung).

---

### 3.2 Tabelle: `tour_stops`

**Zweck:** Jeder Stopp (Kunde / Adresse) einer Tour.

**Beispielschema (konzeptionell):**

* `id` (PRIMARY KEY)
* `tour_id` (FOREIGN KEY → `tours.id`)
* `customer_id` (optional, falls Kundentabelle existiert)
* `lat`, `lon` (Koordinaten)
* `address_text` (Anzeigename / Originaladresse)
* `planned_time_window_start`
* `planned_time_window_end`
* `actual_arrival` (Ist-Ankunftszeit)
* `sequence` (Position in der Tour / Sub-Route)
* `subroute_id` (optional, falls Sub-Routen separat markiert werden)

**Bemerkung:**

* Diese Tabelle ist die Basis für:

  * spätere Auswertungen (z.B. Pünktlichkeit pro Kunde)
  * Rekonstruktion der tatsächlichen Route.

---

### 3.3 Tabelle: `tour_events`

**Zweck:** Log von Ereignissen während einer Tour (für Debugging, KI und Analyse).

**Beispielschema (konzeptionell):**

* `id` (PRIMARY KEY)
* `tour_id` (FOREIGN KEY → `tours.id`)
* `type` (z.B. `delay`, `reroute`, `traffic_jam`, `manual_override`, `error`)
* `payload_json` (zusätzliche Daten, flexibel)
* `created_at`

**Bemerkung:**

* Dient als „Fehler- und Ereignis-Gedächtnis".
* Kann später von der KI genutzt werden, um Problem-Muster zu erkennen.

---

## 4. Optional: Vektor-Datenbank / Embedding-Tabelle

### 4.1 Tabelle: `route_embeddings`

**Zweck:** Speichert komprimierte, numerische Repräsentationen (Vektoren) von Touren für KI-Abfragen.

**Beispielschema (konzeptionell):**

* `id` (PRIMARY KEY)
* `tour_id` (FOREIGN KEY → `tours.id`)
* `embedding` (Vektor – Speicherung je nach DB-Technik)
* `model_name` (z.B. `text-embedding-3-large`)
* `success_score` (aus `tours.score_success` gespiegelt)
* `meta_json` (z.B. Anzahl Stops, Region, Fahrzeugtyp)
* `created_at`

**Einsatz:**

* KNN-Queries (Nearest Neighbour): „Finde die 10 ähnlichsten Touren zu dieser neuen geplanten Tour."
* Grundlage, um der KI Beispiele aus der Historie zu geben.

---

## 5. Ablauf – Flow im Detail

### 5.1 Phase 1 – Planung & CSV-Import

1. Disponent lädt CSV hoch.
2. Backend:

   * Validiert CSV
   * Mappt Einträge auf Tour-Struktur (Stops, Adressen)
   * Ruft OSRM + Optimierungslogik auf.

3. Es entsteht eine geplante Tour mit:

   * geplanter Stop-Reihenfolge
   * geplanter Gesamtdistanz
   * geplanter Zeitstruktur.

*(Optional: Bereits in dieser Phase kann ein erster Eintrag in `tours` und `tour_stops` angelegt werden – Status `planned`.)*

---

### 5.2 Phase 2 – Durchführung der Tour

1. Fahrer startet Tour (Status → `in_progress`).
2. Während der Tour können entstehen:

   * Ist-Ankunftszeiten
   * manuelle Änderungen (Stops übersprungen, Reihenfolge angepasst)
   * Events (Stau, Umleitungen, Fehler)

3. Diese Daten werden über die Anwendung / API zurück ins Backend gemeldet.

Am Ende der Tour:

* Tourstatus → `completed` oder `aborted`.
* Kennzahlen werden berechnet:

  * Differenz geplant vs. real (Distanz, Zeit)
  * Verspätungen
  * Score.

Alle Infos landen in den Tabellen:

* `tours`
* `tour_stops`
* `tour_events`.

---

### 5.3 Phase 3 – KI-Auswertung & Embedding-Erzeugung

Ein separater Prozess (Batch-Job, Worker, Cron) läuft z.B. **nachts** oder nach Abschluss einer Tour:

1. Sucht Touren mit Status `completed`, für die noch kein Embedding existiert.
2. Erzeugt aus einer Tour eine strukturierte Beschreibung, z.B.:

   * „Tour in Region Dresden Nord, 12 Stops, wenige Verspätungen, Distanz 28 km, Score 92."

3. Ruft ein Embedding-Modell auf → erhält einen Vektor.
4. Speichert den Vektor in `route_embeddings`.

Effekt:

* Die Historie wird Schritt für Schritt in eine **KI-durchsuchbare Wissensbasis** verwandelt.

---

### 5.4 Phase 4 – Nutzung bei neuen Touren

Wenn eine neue Tour geplant wird:

1. Backend erzeugt eine ähnliche Beschreibung wie bei Phase 3 (für die geplante Tour).
2. Embedding dieser geplanten Tour wird berechnet (ohne Speichern – nur für die Abfrage).
3. In `route_embeddings` wird eine Ähnlichkeitssuche gemacht (KNN-Query).
4. Die ähnlichsten Historien-Touren werden gefunden – idealerweise inkl. hoher `success_score`.
5. Diese Beispiele können genutzt werden für:

   * Vorschläge für Sub-Routen / Aufteilung
   * Optimierungsparameter (z.B. Gewichtung von Metriken)
   * Warnungen im Adminbereich („Ähnelt problematischer Tour vom …")

---

## 6. Integration in den Adminbereich

Im Adminbereich kann dieser Flow sichtbar gemacht werden über:

1. **Seite „Datenfluss & Status"**

   * Visualisierung: CSV → Planung → Durchführung → Speicherung → KI
   * Anzeige, wie viele Touren bereits in der DB liegen (Anzahl Einträge `tours`).
   * Anzeige, wie viele Embeddings existieren (`route_embeddings`).

2. **Seite „Tour-Historie"**

   * Liste abgeschlossener Touren mit Kennzahlen (Datum, Distanz, Score, Verspätung).
   * Filter nach Region, Fahrer, Zeitraum.

3. **Seite „KI & Lernen"**

   * Kennzahlen:

     * Anzahl Touren mit Embedding
     * Durchschnittlicher Score
     * Letzte Touren mit besonders guten/schlechten Werten.
   * Optional: „Ähnliche Touren" zu einer ausgewählten Tour anzeigen.

4. **Links zur Doku**

   * `STATUS_AKTUELL.md` (Gesamtstatus)
   * DB-Schema-Doku
   * Dieses Flow-Dokument

---

## 7. Phasenplan für Implementierung

**Phase 1 – Basis-DB & Speicherung**

* Tabellen: `tours`, `tour_stops`, `tour_events` real anlegen.
* Beim Tourabschluss echte Werte in diese Tabellen schreiben.
* Adminbereich: einfache Tour-Historienansicht.

**Phase 2 – Kennzahlen & Auswertungen**

* `score_success` konsistent berechnen.
* Adminbereich: Statistiken, Filter, Berichtsfunktionen.

**Phase 3 – KI-Embeddings & Vektor-Suche**

* Tabelle `route_embeddings` anlegen.
* Worker/Job zum Embedding-Berechnen.
* API-Endpoint für „Finde ähnliche Touren".

**Phase 4 – Tiefe KI-Integration**

* Nutzung der Ähnlichkeitssuche in Optimierung und Vorschlagslogik.
* Erklärbarkeit im Adminbereich („Entscheidung basiert auf Touren X, Y, Z.")

---

Dieses Dokument soll als **Referenz-Flow** dienen – sowohl für die App-Weiterentwicklung als auch für die Darstellung im Adminbereich, damit jederzeit klar ist, wie die Daten sich durch das System bewegen und wo die KI ansetzt.

