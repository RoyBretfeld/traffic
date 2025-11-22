# Änderungen 2025-11-20 – FAMO TrafficApp 3.0

**Datum:** 2025-11-20  
**Version:** 3.1  
**Zweck:** Dokumentation der neuesten Features und Verbesserungen

---

## 📋 Übersicht

Diese Dokumentation beschreibt die wichtigsten Änderungen und Verbesserungen vom 20. November 2025.

---

## ✅ Neue Features

### 1. W-Touren und PIR Anlief-Touren in Datenbank speichern

**Problem:** W-Touren und PIR Anlief-Touren wurden im Workflow verarbeitet, aber nicht in der Datenbank gespeichert, wodurch sie nicht in der "Erlaubte Touren" Liste im Tour-Filter erschienen.

**Lösung:** Automatische Speicherung nach erfolgreichem Workflow-Upload.

**Implementierung:**
- **Datei:** `backend/routes/workflow_api.py` (Zeilen 1665-1720)
- **Funktion:** Nach erfolgreichem Workflow-Upload werden alle gefilterten Touren (W-Touren und PIR Anlief) in die `touren`-Tabelle gespeichert
- **Datum-Extraktion:** Automatische Extraktion aus Dateinamen (z.B. "Tourenplan 18.08.2025.csv" → "2025-08-18")
- **Kunden-ID-Extraktion:** Prüft `customer_number`, `kdnr` und `order_id` aus den Stops
- **Duplikat-Prüfung:** Verhindert doppelte Einträge (prüft ob Tour mit gleichem `tour_id` und `datum` bereits existiert)

**Ergebnis:**
- ✅ W-Touren und PIR Anlief-Touren erscheinen in "Erlaubte Touren" Liste
- ✅ Touren können für Statistiken, Tourplan-Übersicht und andere Features verwendet werden
- ✅ Automatische Speicherung ohne manuellen Eingriff

---

### 2. Geo-Cache Vorverarbeitung (Asynchrones Geocoding)

**Problem:** Die Geo-Cache Vorverarbeitung hing beim Start, da synchrone Geocoding-Calls den Event Loop blockierten.

**Lösung:** Umstellung auf asynchrones Geocoding mit `httpx.AsyncClient`.

**Implementierung:**
- **Datei:** `backend/routes/db_management_api.py` (Zeile 128-187)
- **Änderung:** Ersetzt `geocode_address(address)` durch `await _geocode_one(address, geocode_client, company_name=name)`
- **HTTP-Client:** Verwendet `httpx.AsyncClient` für alle Geocoding-Requests (wiederverwendbar, nicht blockierend)

**Vorteile:**
- ✅ Nicht-blockierend: Server bleibt während Geocoding responsiv
- ✅ Schneller: Asynchrone Requests können parallel verarbeitet werden
- ✅ Konsistent: Verwendet die gleiche asynchrone Logik wie der Workflow

**Ergebnis:**
- ✅ Geo-Cache Vorverarbeitung funktioniert ohne Hänger
- ✅ Bessere Performance bei vielen Adressen
- ✅ Server bleibt während der Verarbeitung erreichbar

---

### 3. Tour-Filter: Präzise Filter-Logik

**Problem:** Die "Erlaubte Touren" Liste zeigte keine Touren an, da die Filter-Logik zu einfach war (nur `if pattern.upper() in tour_id.upper()`).

**Lösung:** Verwendung der präzisen Filter-Logik aus `should_process_tour_admin()`.

**Implementierung:**
- **Datei:** `backend/routes/tour_filter_api.py` (Zeile 182-198)
- **Änderung:** Ersetzt einfache Pattern-Prüfung durch `should_process_tour_admin(tour_id, ignore_patterns, allow_list)`
- **Logik:** Berücksichtigt:
  - Exakte Matches
  - Pattern am Anfang der Tour-ID
  - Pattern als ganzes Wort
  - Spezialbehandlung für kurze Patterns (1-2 Zeichen)
  - Allow-Liste (falls vorhanden)

**Ergebnis:**
- ✅ "Erlaubte Touren" Liste zeigt korrekt alle nicht-ignorierten Touren
- ✅ Konsistente Filter-Logik zwischen Workflow und Admin-Bereich
- ✅ Präzise Pattern-Erkennung verhindert False Positives

---

### 4. Farbzuweisung für PIR Anlief-Touren

**Problem:** Alle PIR Anlief-Touren hatten die gleiche Farbe, da sie den gleichen Basis-Namen hatten.

**Lösung:** Erweiterte `getTourColor()` Funktion erkennt PIR Anlief-Touren und weist basierend auf der Zeit unterschiedliche Farben zu.

**Implementierung:**
- **Datei:** `frontend/index.html` (Zeile 6344-6365)
- **Logik:** Extrahiert Stunde und Minute aus Tour-Namen (z.B. "PIR Anlief. 7.45 Uhr" → 7×60+45 = 465)
- **Farbzuweisung:** Verwendet Zeit-Index für eindeutige Farbzuweisung aus einer Palette von 22 Farben

**Ergebnis:**
- ✅ Jede PIR Anlief-Tour hat eine eindeutige Farbe
- ✅ Visuell besser unterscheidbar
- ✅ Konsistent mit W-Touren (verwendet `_route_index` wenn vorhanden)

---

### 5. Admin-Navigation: Neue Seiten

**Neue Admin-Seiten:**
- **Tourplan-Übersicht** (`/admin/tourplan-uebersicht.html`): Zeigt Gesamt-KPIs und Details für einen ausgewählten Tourplan
- **Geo-Cache Vorverarbeitung** (`/admin/geo-cache-vorverarbeitung.html`): Batch-Geocoding für historische Tourpläne

**Navigation:**
- Beide Seiten sind in der Admin-Navigation integriert
- Konsistente Navigation über alle Admin-Seiten
- "Cool Band" Stil mit Gradient-Hintergrund

---

## 🔧 Verbesserungen

### 1. Workflow: Asynchrones Geocoding

**Vorher:** Synchrone `geocode_address()` Calls blockierten den Event Loop  
**Nachher:** Asynchrones `_geocode_one()` mit `httpx.AsyncClient`

**Datei:** `backend/routes/workflow_api.py` (Zeile 1434-1518)

**Vorteile:**
- ✅ Workflow läuft deutlich schneller
- ✅ Server bleibt responsiv während Geocoding
- ✅ Potenzial für parallele Requests

---

### 2. Tour-Filter: Korrekte Filter-Logik

**Vorher:** Einfache `if pattern.upper() in tour_id.upper()` Prüfung  
**Nachher:** Präzise `should_process_tour_admin()` Logik

**Datei:** `backend/routes/tour_filter_api.py` (Zeile 182-198)

**Vorteile:**
- ✅ Präzise Pattern-Erkennung
- ✅ Verhindert False Positives
- ✅ Konsistente Logik zwischen Workflow und Admin

---

### 3. Admin-Navigation: Konsistenz

**Änderungen:**
- Alle Admin-Seiten verwenden die gleiche Navigation
- "Cool Band" Stil mit Gradient-Hintergrund
- Konsistente Top-Padding (20px)
- Entfernung redundanter Navigation-Elemente

**Dateien:**
- `frontend/admin/system.html`
- `frontend/admin/statistik.html`
- `frontend/admin/systemregeln.html`
- `frontend/admin/db-verwaltung.html`
- `frontend/admin/tour-filter.html`
- `frontend/admin/tour-import.html`
- `frontend/admin/dataflow.html`
- `frontend/admin/ki-integration.html`
- `frontend/admin/ki-improvements.html`
- `frontend/admin/ki-kosten.html`
- `frontend/admin/ki-verhalten.html`

---

## 🐛 Fehlerbehebungen

### 1. "local variable 're' referenced before assignment"

**Problem:** Workflow schlug fehl mit `Workflow fehlgeschlagen: local variable 're' referenced before assignment`

**Ursache:** Redundante lokale `import re` Statements überschrieben den globalen Import

**Fix:** Entfernung aller redundanten lokalen `import re` Statements

**Datei:** `backend/routes/workflow_api.py` (Zeilen 1670, 2072, 2175)

**Dokumentiert:** ✅ `Regeln/LESSONS_LOG.md` (Eintrag #29)

---

### 2. Geo-Cache Vorverarbeitung hängt

**Problem:** Geo-Cache Vorverarbeitung hing beim Start

**Ursache:** Synchrone `geocode_address()` Calls blockierten den Event Loop

**Fix:** Umstellung auf asynchrones Geocoding mit `httpx.AsyncClient`

**Datei:** `backend/routes/db_management_api.py` (Zeile 128-187)

---

### 3. "Erlaubte Touren" Liste leer

**Problem:** "Erlaubte Touren" Liste zeigte keine Touren an

**Ursache:** Zu einfache Filter-Logik (`if pattern.upper() in tour_id.upper()`)

**Fix:** Verwendung der präzisen `should_process_tour_admin()` Logik

**Datei:** `backend/routes/tour_filter_api.py` (Zeile 182-198)

---

### 4. Admin-Navigation: 404-Fehler für `admin_navigation.js`

**Problem:** 404-Fehler beim Laden von `/js/admin_navigation.js`

**Ursache:** Referenzen auf nicht mehr benötigte JavaScript-Datei

**Fix:** Entfernung aller `<script src="/js/admin_navigation.js"></script>` Referenzen und `initAdminNavigation()` Aufrufe

**Dateien:**
- `frontend/admin/tour-import.html`
- `frontend/admin/tour-filter.html`
- `frontend/admin/db-verwaltung.html`
- `frontend/admin/systemregeln.html`

---

## 📊 Technische Details

### Datenbank-Schema

**Neue Spalten (falls noch nicht vorhanden):**
- `touren.gesamtzeit_min` (INTEGER) - Gesamtzeit in Minuten (inkl. Rückfahrt)

**Verwendung:**
- Wird automatisch gesetzt, wenn Routen-Daten gespeichert werden
- Fallback auf `dauer_min` wenn `gesamtzeit_min` nicht vorhanden

---

### API-Endpoints

**Neue/Geänderte Endpoints:**

1. **`POST /api/workflow/upload`**
   - Speichert jetzt automatisch W-Touren und PIR Anlief-Touren in DB
   - Asynchrones Geocoding

2. **`POST /api/tourplan/batch-geocode`**
   - Asynchrones Geocoding implementiert
   - Cache-Hit-Rate Tracking

3. **`GET /api/tour-filter/allowed`**
   - Verwendet präzise Filter-Logik
   - Zeigt korrekt alle erlaubten Touren

---

## 🎯 Nächste Schritte

### Geplant

1. **Tourplan-Übersicht erweitern:**
   - Details für einzelne Touren
   - Export-Funktionen
   - Filter-Optionen

2. **Geo-Cache Vorverarbeitung:**
   - Batch-Verarbeitung mehrerer Dateien
   - Progress-Tracking pro Datei
   - Fehler-Report für manuelle Bearbeitung

3. **Statistiken:**
   - Kosten-KPIs vollständig implementieren
   - Charts für Kosten-Trends
   - Export-Funktionen

---

## 📚 Verwandte Dokumentation

- **Admin-Bereich:** `docs/ADMIN_BEREICH_DOKUMENTATION.md`
- **Statistik & Kosten:** `docs/STATISTIK_KOSTEN_KPIS.md`
- **Fehlerkatalog:** `Regeln/LESSONS_LOG.md` (Eintrag #29)
- **Tour-Filter:** `docs/TOUR_IGNORE_LIST.md`

---

**Ende der Dokumentation**  
**Letzte Aktualisierung:** 2025-11-20 20:00

