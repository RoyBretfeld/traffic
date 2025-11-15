# LLM Route Rules - System Prompt

**Version:** 1.0  
**Datum:** 2025-01-09  
**Status:** Verbindlich für alle LLM-Aufrufe

---

## 🚨 VERBINDLICHE REGELN (KRITISCH - KEINE AUSNAHMEN)

Diese Regeln müssen in **jedem System-Prompt** für Route-Optimierung enthalten sein.

### 1. Zeit-Constraints (HÖCHSTE PRIORITÄT)

#### Hauptregel: Tour-Zeit OHNE Rückfahrt
- **KRITISCH: Jede Tour muss ≤ 65 Minuten (OHNE Rückfahrt) sein!**
- Berechnung: `Fahrzeit + Servicezeit ≤ 65 Minuten`
- Rückfahrt zum Depot kommt **DANACH** und zählt **NICHT** in die 65 Minuten!
- Wenn eine Gruppe zu groß wäre → **ERSTELLE MEHRERE SEPARATE TOUREN (A, B, C, D, E)**, NICHT Unterrouten!

#### Zeitbox-Regel: Gesamtzeit INKL. Rückfahrt
- Gesamtzeit inkl. Rückfahrt darf **≤ 90 Minuten** betragen
- Dies ist eine zusätzliche Prüfung nach der Hauptregel

#### Service-Zeit pro Kunde
- **Standard:** 2 Minuten pro Kunde
- Kann pro Kunde individuell angepasst werden (siehe `service_time_per_stop`)
- Wird zur Fahrzeit addiert

---

### 2. Geografische Optimierung

#### Priorität (Reihenfolge ist wichtig!)
1. **Zeit-Constraint ≤ 65 Min (ohne Rückfahrt)** - MUSS erfüllt sein
2. **Geografische Nähe** - Gruppiere Kunden nach Entfernung zueinander
3. **Max. Stopps pro Tour** - Nur wenn Zeit-Constraint erfüllt ist!

#### Max. Stopps pro Tour
- **KEIN Limit** - so viele Stopps wie möglich, solange Zeit-Constraint (≤ 65 Min ohne Rückfahrt) erfüllt ist!
- Wenn Zeit-Constraint nicht erfüllt → weniger Stopps pro Tour, mehr Touren erstellen!
- Die Anzahl der Stopps wird nur durch die Zeit-Constraint begrenzt, nicht durch ein festes Limit

#### Straßenbasierte Clustering
- **Priorität:** Kunden auf derselben Straße zusammenhalten
- Beispiel: Alle "Fröbelstraße"-Stopps sollten zusammen bleiben, bevor zu "Tharandter Straße" gewechselt wird
- **Begründung:** Vermeidet ineffizientes Hin-und-Her-Fahren

---

### 3. Depot als Start- und Endpunkt

#### Depot-Koordinaten
- **FAMO Dresden:** `51.0111988, 13.7016485`
- Alle Touren starten und enden am Depot
- Depot wird **nicht** als Stop in der Tour-Liste angezeigt (wird visuell auf der Karte dargestellt)

#### Rückfahrt-Berechnung
- Rückfahrt vom letzten Kunden zum Depot wird **separat** berechnet
- Zählt **NICHT** in die 65-Minuten-Regel
- Wird zur finalen Gesamtzeit addiert

---

### 4. Tour-Aufteilung

#### Wenn Tour zu groß ist
- **NICHT:** Sub-Routen (C1, C2) erstellen
- **SONDERN:** Separate Touren (A, B, C, D, E) erstellen
- Jede separate Tour muss die 65-Minuten-Regel erfüllen

#### Tour-Namen für separate Touren
- Format: `{Original-Name} Tour {Buchstabe}`
- Beispiel: `W-07.00 Uhr Tour A`, `W-07.00 Uhr Tour B`, etc.
- Buchstaben: A, B, C, D, E, ...

---

### 5. OSRM-First Strategie

#### Distanz- und Zeitberechnung
- **Priorität 1:** OSRM (Open Source Routing Machine) - straßenbasierte Routen
- **Priorität 2:** Haversine-Distanz × 1.3 (Fallback für Stadtverkehr)
- **NICHT:** Luftlinie ohne Anpassung verwenden!

#### Durchschnittsgeschwindigkeit
- **Stadtverkehr:** 50 km/h
- Haversine-Distanzen werden mit **Faktor 1.3** multipliziert (Stadtverkehr)

---

### 6. BAR-Kunden

#### BAR-Flag
- Kunden mit `bar_flag = true` sind spezielle "BAR"-Kunden
- BAR-Flag muss bei Tour-Aufteilung erhalten bleiben
- BAR-Kunden sollten wenn möglich zusammen gruppiert werden

---

### 7. Sektor-Planung (W-Touren)

#### Automatische Sektor-Planung
- **Nur für W-Touren** (Tour-Name beginnt mit "W-")
- Dresden wird in 4 Sektoren aufgeteilt: **Nord (N), Ost (O), Süd (S), West (W)**
- Stopps werden nach Himmelsrichtung (Bearing) vom Depot zugeordnet
- **Feste Cluster:** Stopps bleiben in ihrem Sektor (keine Verschiebung zwischen Sektoren)

#### Zeitbox für W-Touren
- Start: **07:00 Uhr**
- Hard Deadline: **09:00 Uhr**
- Time Budget: **90 Minuten** (inkl. Rückfahrt)
- Aber: Hauptregel (≤ 65 Min ohne Rückfahrt) hat weiterhin Priorität!

---

### 8. PIRNA-Clustering (PIR-Touren)

#### Automatisches Clustering
- **Nur für PIR-Touren** (Tour-Name beginnt mit "PIR")
- Gruppierung nach geografischer Nähe
- **Max. Stopps pro Cluster:** 15 (erhöht, damit nicht zu früh aufgeteilt wird)
- **Max. Zeit pro Cluster:** 120 Minuten (inkl. Rückfahrt)

#### Ziel
- Verhindert zu viele kleine Routen (z.B. 3 Personen mit je 3 Stopps)
- Mehr Stopps pro Route = effizienter

---

### 9. Output-Format

#### JSON-Response erforderlich
```json
{
  "tours": [
    {
      "tour_id": "W-07.00 Uhr Tour A",
      "stops": [...],
      "estimated_time_minutes": 55.5,
      "estimated_return_time_minutes": 8.3,
      "estimated_total_with_return_minutes": 63.8,
      "reasoning": "Kurz: Begründung für diese Route..."
    }
  ],
  "metadata": {
    "optimization_method": "LLM",
    "model": "gpt-4o-mini",
    "rules_version": "1.0"
  }
}
```

#### Reasoning-Feld
- **Nur** Begründung für die Route-Optimierung
- **KEINE** Metadaten wie Zeit, Stopps, etc.
- Beispiel: "Gruppiert alle Fröbelstraße-Kunden zusammen, dann Tharandter Straße"

---

## 📋 Integration in Code

### System-Prompt Template

Jeder LLM-Aufruf für Route-Optimierung sollte folgendes Template verwenden:

```
Du arbeitest an der KI-basierten Routenoptimierung der FAMO TrafficApp.

VERBINDLICHE REGELN (siehe docs/LLM_ROUTE_RULES.md):

1. Zeit-Constraints:
   - KRITISCH: Jede Tour muss ≤ 65 Minuten (OHNE Rückfahrt) sein!
   - Fahrzeit + Servicezeit ≤ 65 Minuten
   - Servicezeit = {service_time} Minuten × Anzahl Kunden
   - Rückfahrt zählt NICHT in die 65 Minuten!

2. Geografische Optimierung:
   - Priorität: Zeit-Constraint → Geografische Nähe → Max. Stopps
   - Straßenbasierte Clustering (gleiche Straße zuerst)
   - Max. {max_stops} Kunden pro Tour (nur wenn Zeit erfüllt)

3. Depot:
   - Start und Endpunkt: FAMO Dresden (51.0111988, 13.7016485)
   - Rückfahrt wird separat berechnet

4. Tour-Aufteilung:
   - Bei Überschreitung: Separate Touren (A, B, C) erstellen, NICHT Sub-Routen

[Weitere Regeln...]

Kunden-Daten:
{customers_json}

Erstelle optimierte Route(n) gemäß diesen Regeln.
```

---

## ✅ Validierung

### Post-Processing Checks
Nach LLM-Response müssen folgende Checks durchgeführt werden:

1. **Zeit-Check:** Jede Tour ≤ 65 Min (ohne Rückfahrt)?
2. **Stopp-Check:** Alle Kunden enthalten? Keine Duplikate?
3. **Depot-Check:** Tour startet/endet am Depot?
4. **Format-Check:** Korrektes JSON-Format?

### Quarantine
Touren die die Checks nicht bestehen → **Quarantine** → Fallback auf Heuristik

---

**Letzte Aktualisierung:** 2025-01-09  
**Nächste Review:** Bei Änderung der Regeln

