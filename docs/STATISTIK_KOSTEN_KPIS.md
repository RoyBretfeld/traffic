# TrafficApp 3.0 – Statistik- & Kosten-KPIs (Implementierungs-Guide für Cursor/KI)

## 1. Ziel

Dieses Dokument beschreibt, **was** aus den vorhandenen Tourdaten berechnet werden soll und **wie** es strukturiert werden kann, damit KIs (z.B. Cursor) die Statistik- und Kostenfunktionen konsistent implementieren können.

Datenbasis ist eine Touren-Ansicht wie im UI-Screenshot (Stops, Distanz, Fahrzeit, Servicezeit, Gesamtzeit, Rückfahrt, Kunden/Depot).

---

## 2. Daten, die pro Tour gespeichert werden sollen

Jede Tour in der Tabelle `tours` (oder einer erweiterten Tour-Tabelle) soll mindestens folgende Felder enthalten:

* `stops_count` – Anzahl der Kunden-Stops (ohne Depot)
* `distance_total_km` – Gesamtstrecke der Tour inkl. Rückfahrt
* `drive_time_min` – reine Fahrzeit in Minuten
* `service_time_min` – Service-/Entladezeit beim Kunden (Summe)
* `total_time_min` – Gesamtzeit der Tour (Fahren + Service)
* optional `return_distance_km` – reine Rückfahrtstrecke
* optional `return_time_min` – reine Rückfahrtzeit

Das können entweder berechnete Felder beim Abschluss der Tour sein oder beim Anlegen der geplanten Tour.

**Ziel:**

* Alle relevanten Kenngrößen einer Tour sind direkt in `tours` verfügbar, ohne die Stops jedes Mal neu auswerten zu müssen.

---

## 3. Aggregation pro Tag/Woche

Auf Basis der Tour-Werte werden in einer Aggregationstabelle (z.B. `stats_daily`) folgende Werte gespeichert.

### 3.1 Mengen- & Auslastungs-KPIs

Pro Tag (und optional Region/Fahrer):

* `total_tours` – Anzahl Touren
* `total_stops` – Anzahl Stops
* `avg_stops_per_tour` – `total_stops / total_tours`
* `total_distance_km` – Summe `distance_total_km`
* `avg_distance_per_tour_km` – `total_distance_km / total_tours`

### 3.2 Zeit-KPIs

* `total_drive_time_min` – Summe `drive_time_min`
* `total_service_time_min` – Summe `service_time_min`
* `total_time_min` – Summe `total_time_min`
* `avg_time_per_tour_min` – `total_time_min / total_tours`

Optional:

* Verhältnis Fahrzeit/Servicezeit (z.B. als berechnetes Feld im API-Response)

Diese Werte werden aus `tours` pro Tag aggregiert und in `stats_daily` gespeichert.

---

## 4. Kostenberechnung

Für Kosten werden Konfigurationswerte benötigt (z.B. in `app_settings`):

* `cost_per_km` – variable Kosten pro km (Kraftstoff, Verschleiß, Maut etc.)
* `cost_driver_per_hour` – Kosten pro Fahrer-Stunde (Bruttolohn + Nebenkosten)
* optional `cost_vehicle_per_hour` – Fahrzeugkosten pro Stunde (Leasing/Abschreibung)

### 4.1 Kosten pro Tour (Backend-Logik)

Für jede Tour:

```text
hours_total          = total_time_min / 60.0
vehicle_cost_km      = distance_total_km * cost_per_km
driver_cost          = hours_total * cost_driver_per_hour
optional_vehicle_hour_cost = hours_total * cost_vehicle_per_hour

tour_cost_total      = vehicle_cost_km + driver_cost (+ optional_vehicle_hour_cost)
cost_per_stop        = tour_cost_total / stops_count
cost_per_km          = tour_cost_total / distance_total_km
```

Es bietet sich an, folgende Felder in einer separaten Tabelle (z.B. `tour_costs`) zu speichern **oder** als berechnete Felder im API-Response zu liefern:

* `tour_id`
* `tour_cost_total`
* `cost_per_stop`
* `cost_per_km`

### 4.2 Kosten auf Tages-/Wochebene

Auf Basis der Tourkosten:

Pro Tag/Woche (Aggregation z.B. in `stats_daily` oder `stats_weekly`):

* `total_cost` – Summe aller `tour_cost_total`
* `avg_cost_per_tour` – `total_cost / total_tours`
* `avg_cost_per_stop` – `total_cost / total_stops`
* `avg_cost_per_km` – `total_cost / total_distance_km`

Diese Werte sind die Kern-Kosten-KPIs für den Adminbereich.

---

## 5. Relevante KPI-Liste (Empfehlung)

Für Tages- oder Wochen-Ansichten im Adminbereich sollten mindestens diese KPIs gerechnet und angezeigt werden:

1. **Menge & Auslastung**

   * Touren gesamt (`total_tours`)
   * Stops gesamt (`total_stops`)
   * Ø Stops pro Tour (`avg_stops_per_tour`)
   * Ø Distanz pro Tour (`avg_distance_per_tour_km`)

2. **Strecke & Zeit**

   * Kilometer gesamt (`total_distance_km`)
   * Gesamtzeit Fahrer (`total_time_min` → Stunden)
   * Verhältnis Fahrzeit : Servicezeit (z.B. als Prozentwerte)

3. **Kosten**

   * Gesamtkosten (`total_cost`)
   * Ø Kosten pro Tour (`avg_cost_per_tour`)
   * Ø Kosten pro Stop (`avg_cost_per_stop`)
   * Ø Kosten pro km (`avg_cost_per_km`)

Diese KPIs reichen aus, um:

* Auslastung zu beurteilen
* Effizienz zu vergleichen (zwischen Tagen/Wochen/Fahrern)
* echte Kostenfragen zu beantworten ("Was kostet uns eine Zustellung im Schnitt?").

---

## 6. API-Design (Beispiel)

### 6.1 Tages-/Wochenübersicht

Endpoint-Beispiel:

```http
GET /api/stats/costs?from=YYYY-MM-DD&to=YYYY-MM-DD&group=day|week
```

Response (vereinfacht):

```json
[
  {
    "date": "2025-11-17",
    "total_tours": 42,
    "total_stops": 318,
    "total_distance_km": 812.4,
    "total_time_min": 2370,
    "total_cost": 3540.75,
    "avg_stops_per_tour": 7.57,
    "avg_distance_per_tour_km": 19.35,
    "avg_cost_per_tour": 84.3,
    "avg_cost_per_stop": 11.13,
    "avg_cost_per_km": 4.36
  },
  ...
]
```

Das Frontend kann daraus sowohl Kachel-KPIs als auch Zeitreihen-Charts bauen.

---

## 7. UI-Idee für den Adminbereich (Kosten-Ansicht)

Empfohlene Struktur der „Kosten & Leistung"-Sektion im Admin:

1. **KPI-Kacheln (für gewählten Zeitraum)**

   * Touren gesamt
   * Stops gesamt
   * Kilometer gesamt
   * Gesamtkosten
   * Kosten pro Stop (Ø)
   * Kosten pro km (Ø)

2. **Charts**

   * Linie: Gesamtkosten pro Tag/Woche
   * Linie/Balken: Kilometer & Touren pro Tag/Woche
   * optional: Balken – Kosten pro Stop im Zeitverlauf

3. **Tabelle**

   * Zeilen = Tage/Wochen
   * Spalten = zentrale KPIs (Touren, Stops, km, Kosten gesamt, Kosten/Stop, Kosten/km)

---

## 8. Anforderungen an Cursor/KI bei Implementierung

* **Keine Rohdaten-on-the-fly-Auswertung im Frontend:**

  * Aggregationen müssen im Backend (z.B. per Cron/Worker) in `stats_daily` / `stats_weekly` geschrieben werden.

* **Konfigurierbare Kostenparameter verwenden:**

  * `cost_per_km`, `cost_driver_per_hour`, `cost_vehicle_per_hour` aus Konfig/DB lesen, nicht hardcoden.

* **IDs & Namen konsistent halten:**

  * Feldnamen wie in diesem Dokument verwenden oder sauber dokumentiert abweichend.

Dieses Dokument soll von KIs direkt genutzt werden können, um Statistik- und Kostenberechnung in TrafficApp 3.0 konsistent und erweiterbar umzusetzen.

