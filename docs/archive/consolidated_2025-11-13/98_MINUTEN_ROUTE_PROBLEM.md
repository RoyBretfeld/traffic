# 98-Minuten-Route Problem

**Datum:** 2025-01-09  
**Status:** 🔴 Identifiziert, Lösung in Arbeit

---

## Problem

Tour "W-07.00 Uhr Tour" (oder ähnlich) zeigt **98 Minuten Gesamtzeit**, obwohl das Limit bei:
- **65 Minuten OHNE Rückfahrt** (Fahrzeit + Servicezeit)
- **90 Minuten INKL. Rückfahrt** (Gesamtzeit)

liegt.

---

## Ursachen-Analyse

### 1. Route wird trotz Überschreitung erstellt

**Datei:** `services/sector_planner.py` (Zeile 676-708)

**Aktuelle Logik:**
1. Während der Greedy-Planung wird geprüft, ob der nächste Kandidat die Limits überschreitet (Zeile 589, 595)
2. Wenn ja → `break` (Route wird abgeschlossen)
3. **ABER:** Route wird trotzdem erstellt, auch wenn sie die Limits überschreitet

**Problem:**
- Route könnte zu lang sein, weil:
  - Ein einzelner Segment sehr lang ist (z.B. 30 Minuten zum ersten Kunden)
  - Die Berechnung während der Planung (Zeile 573) unterscheidet sich von der finalen Berechnung (Zeile 673)
  - Rundungsfehler oder Fehler bei der Rückfahrt-Berechnung

### 2. Validierung findet NACH Erstellung statt

**Aktuell:**
- Validierung findet **nach** Erstellung statt (Zeile 676)
- Es gibt nur eine **Warnung**, aber Route wird trotzdem erstellt
- `validated: false` Flag wird gesetzt (Zeile 704), aber Route wird verwendet

**Erwartet:**
- Route sollte **automatisch aufgeteilt** werden, wenn sie Limits überschreitet
- ODER Route sollte **nicht erstellt werden** (verworfen werden)

---

## Beobachtete Symptome

- Tour zeigt 98 Minuten Gesamtzeit
- Warnung im Log: `⚠️ WARNUNG: Route '...' überschreitet ...`
- Route wird trotzdem angezeigt und verwendet
- Frontend zeigt Tour mit gelbem Warn-Icon (⚠️), aber Tour ist funktional

---

## Lösungsvorschläge

### Lösung 1: Automatische Aufteilung (Empfohlen)

Wenn Route Limits überschreitet:
1. Route **nicht direkt erstellen**
2. Stopps **automatisch aufteilen** in mehrere Routen
3. Jede neue Route muss innerhalb Limits sein

**Implementierung:**
- Neue Funktion: `_split_overlong_route()` in `sector_planner.py`
- Wird aufgerufen, wenn `time_without_return_final > 65` oder `total_with_return_final > 90`
- Teilt Stopps in mehrere Routen auf (ähnlich wie `splitTourIntoSubRoutes` im Frontend)

### Lösung 2: Route verwerfen (Einfacher, aber weniger optimal)

Wenn Route Limits überschreitet:
1. Route **nicht erstellen**
2. Stopps bleiben in `remaining` Liste
3. Nächste Iteration versucht es nochmal mit anderen Kombinationen

**Problem:** Könnte zu Endlosschleife führen, wenn keine Kombination möglich ist.

### Lösung 3: Strengere Validierung während Planung (Präventiv)

**Verbesserte Prüfung:**
- Prüfe nicht nur `time_without_return >= 65`, sondern auch **Prognose für finale Route**
- Berücksichtige Rundungsfehler und Puffer (z.B. `time_without_return >= 64.5` statt `65.0`)

**Problem:** Kann zu konservativ sein und Routen zu früh abschneiden.

---

## Debugging-Schritte

### 1. Log-Analyse

Im Server-Log suchen nach:
```
⚠️ WARNUNG: Route '...' überschreitet 65 Min OHNE Rückfahrt: ...
⚠️ WARNUNG: Route '...' überschreitet 90 Min INKL. Rückfahrt: ...
```

**Prüfen:**
- Welche Route genau?
- Wie viele Stopps?
- Welche Zeit-Komponenten (Fahrzeit, Servicezeit, Rückfahrt)?

### 2. Route-Details prüfen

Im Frontend:
- Route in Tabelle öffnen
- Zeiten prüfen:
  - `estimated_driving_time_minutes` (Fahrzeit OHNE Rückfahrt)
  - `estimated_service_time_minutes` (Servicezeit)
  - `estimated_return_time_minutes` (Rückfahrt)
  - `estimated_total_with_return_minutes` (Gesamtzeit INKL. Rückfahrt)

**Berechnung prüfen:**
```
time_without_return = driving_time + service_time  # Sollte ≤ 65 Min
total_with_return = time_without_return + return_time  # Sollte ≤ 90 Min
```

### 3. OSRM-Distanzen prüfen

**Möglich:** OSRM gibt falsche/ungenaue Zeiten zurück.

**Prüfen:**
- Sind die Distanzen realistisch?
- Gibt es einen sehr langen Segment (z.B. Depot → erster Kunde)?

---

## Aktueller Workaround

**Frontend:** Tour mit ⚠️-Warnung wird angezeigt, Benutzer kann manuell splitten.

**Backend:** Route wird erstellt mit `validated: false`, aber trotzdem verwendet.

---

## Nächste Schritte

1. ✅ **Problem identifiziert** - Route wird trotz Überschreitung erstellt
2. 🔄 **Lösung implementieren** - Automatische Aufteilung bei Überschreitung
3. 🧪 **Testen** - Mit 98-Minuten-Tour testen
4. 📝 **Dokumentation aktualisieren** - Nach Implementierung

---

**Letzte Aktualisierung:** 2025-01-09  
**Status:** Problem identifiziert, Lösung in Arbeit

