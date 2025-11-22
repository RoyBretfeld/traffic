# TrafficApp 3.0 – Statistik & KPIs

## 1. Ziel der Statistik

Die Statistik soll ein **belastbares Controlling-Werkzeug** sein, nicht nur ein paar Charts. Grundlage:

* Alle Auswertungen basieren auf **persistenten DB-Daten**, nicht auf Frontend-State.

* Klare Trennung zwischen:

  * Rohdaten (Tours, Stops, Events)

  * Aggregationen (Stats pro Tag/Zeitraum)

  * Darstellung (Charts & KPI-Boxen im Adminbereich)

---

## 2. Datenbasis

### 2.1 Kern-Tabellen

* `tours`

  * Eine Zeile pro Tour (Plan + Ergebnis)

  * Wichtige Felder:

    * `id`

    * `date`

    * `driver_id`

    * `region`

    * `status` (`planned`, `in_progress`, `completed`, `aborted`)

    * `distance_planned_km`

    * `distance_real_km`

    * `total_delay_minutes`

    * `score_success` (0–100)

* `tour_stops`

  * Alle Stops einer Tour

  * Wichtige Felder:

    * `id`

    * `tour_id`

    * `lat`, `lon`

    * `address_text`

    * `planned_time_window_start`

    * `planned_time_window_end`

    * `actual_arrival`

    * `sequence`

* `tour_events`

  * Log von Ereignissen während einer Tour

  * Wichtige Felder:

    * `id`

    * `tour_id`

    * `type` (`delay`, `reroute`, `traffic_jam`, `manual_override`, `error`, ...)

    * `payload_json`

    * `created_at`

Diese Tabellen sind der **Gold-Storage**. Alle Statistiken müssen sich auf diese Daten beziehen.

---

## 3. Aggregations-Tabelle

### 3.1 Tabelle: `stats_daily`

**Zweck:** Schnelle, konsistente Auswertung pro Tag (oder Region), ohne jedes Mal Rohdaten zu scannen.

**Beispielschema (konzeptionell):**

* `id`

* `date`

* `region` (optional, NULL = global)

* `total_tours`

* `completed_tours`

* `aborted_tours`

* `total_stops`

* `total_km_planned`

* `total_km_real`

* `avg_delay_minutes`

* `avg_success_score`

**Eigenschaften:**

* Genau **eine Zeile pro Tag & Region**.

* Wird von einem Aggregator-Job berechnet (siehe unten).

---

## 4. Aggregations-Flow

### 4.1 Aggregator-Job

Ein Job/Worker, z.B. `stats_aggregator.py`, übernimmt:

1. Nimmt einen Tag (oder Datumsbereich) als Input.

2. Liest alle `tours` dieses Tages aus der DB.

3. Rechnet:

   * `total_tours`: Anzahl aller Touren

   * `completed_tours`: Anzahl mit Status `completed`

   * `aborted_tours`: Anzahl mit Status `aborted`

   * `total_stops`: Summe aller Stops aus `tour_stops` für diese Touren

   * `total_km_planned`: Summe `distance_planned_km`

   * `total_km_real`: Summe `distance_real_km`

   * `avg_delay_minutes`: Durchschnitt aus `total_delay_minutes`

   * `avg_success_score`: Durchschnitt aus `score_success`

4. Schreibt/aktualisiert Eintrag in `stats_daily` (Upsert).

### 4.2 Ausführung

* Kann z.B. laufen:

  * 1× pro Nacht für den Vortag

  * oder direkt nach Abschluss einer Tour (dann Recalc für den betroffenen Tag)

Damit sind Stats immer reproduzierbar und schnell abrufbar.

---

## 5. KPIs (Kennzahlen)

### 5.1 Operative KPIs

* **Touren gesamt** im Zeitraum

* **Stops gesamt**

* **Kilometer geplant vs. real**

* **Durchschnittliche Stops pro Tour**

* **Durchschnittliche Tourdauer** (wenn Start/End-Zeit vorhanden)

### 5.2 Qualitäts-KPIs

* **Pünktlichkeit:**

  * z.B. % der Stops innerhalb des Zeitfensters

* **Durchschnittliche Verspätung pro Tour**

* **Abbruchquote:**

  * `aborted_tours / total_tours`

* **Durchschnittlicher Success-Score** (0–100)

### 5.3 Erweiterte KPIs (später)

* OSRM-/Routing-Fehler pro Zeitraum

* Anteil KI-optimierter Touren

* Vergleich „KI-optimierte vs. manuell geänderte" Touren

---

## 6. API-Design für Statistik

Beispiel-Endpoint:

* `GET /stats/overview?from=YYYY-MM-DD&to=YYYY-MM-DD&group=day|month&region=...`

**Funktion:**

* Liest Daten aus `stats_daily`.

* Gruppiert je nach `group` nach Tag oder Monat.

* Liefert:

  * Liste von Zeitpunkten (x-Achse)

  * Aggregierte Werte (Touren, Stops, km, Delay, Score, ...)

Keine direkte Berechnung mehr über Rohdaten in der API, sondern immer über `stats_daily`.

---

## 7. Darstellung im Adminbereich

### 7.1 KPI-Boxen (oben)

4–6 Kacheln mit z.B.:

* Touren gesamt im Zeitraum

* Kilometer gesamt

* Ø Stops pro Tour

* Ø Verspätung

* Ø Success-Score

* Abbruchquote in %

### 7.2 Charts (Zeitreihen)

1. **Touren & Stops**

   * Linienchart, gleiche X-Achse (Datum)

2. **Kilometer geplant vs. real**

   * Zwei Linien: geplante km, reale km

3. **Verspätung & Score**

   * Balken: avg. Delay

   * Linie: avg. Score

### 7.3 Tabellen / Drilldown

* Tabelle pro Tag:

  * `date`, `total_tours`, `total_stops`, `total_km_real`, `avg_delay_minutes`, `avg_success_score`

* Filtermöglichkeiten:

  * Zeitraum (letzte 7 / 30 Tage, frei)

  * Region

  * Fahrer

---

## 8. Implementierungsphasen

**Phase 1 – DB & Aggregation**

* Tabellen `tours`, `tour_stops`, `tour_events`, `stats_daily` real anlegen.

* Aggregator-Job implementieren.

* API-Endpunkt `/stats/overview` aus `stats_daily` speisen.

**Phase 2 – Admin-UI-Basis**

* KPI-Boxen + 2–3 Charts in der Statistik-Ansicht.

* Einfache Zeitraumauswahl.

**Phase 3 – Erweiterte KPIs & Filter**

* Pünktlichkeit, Abbruchquote, Score-Auswertungen.

* Filter nach Fahrer, Region.

**Phase 4 – KI-Statistiken (optional)**

* KI-spezifische Kennzahlen (z.B. Effektivität von KI-Routenoptimierung).

---

Dieses Dokument beschreibt, wie die Statistik der TrafficApp von „ein paar Charts" zu einem **belastbaren Auswertungs- und Steuerungswerkzeug** wird – sauber getrennt in Datenbasis, Aggregation und Darstellung.

