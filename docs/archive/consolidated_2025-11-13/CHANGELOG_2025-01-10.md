# Changelog - 10. Januar 2025

## Übersicht
Heute wurden zwei kritische Probleme behoben:
1. **Panel-Synchronisation**: Abgedockte Fenster synchronisieren jetzt bidirektional mit dem Hauptfenster
2. **Route-Details 422-Fehler**: Frontend sendet jetzt korrekte Daten an das Backend

---

## 1. Panel-Synchronisation (Bidirektional)

### Problem
- Abgedockte Panels (Karte, Touren) zeigten keine Daten an
- Synchronisation funktionierte nur 10 Sekunden nach dem Öffnen
- Keine bidirektionale Kommunikation zwischen Hauptfenster und Panels

### Lösung

#### Frontend (`frontend/index.html`)
- **Kontinuierliche Synchronisation**: Intervalle laufen jetzt dauerhaft (alle 1 Sekunde), nicht nur 10 Sekunden
- **localStorage-Fallback**: Falls BroadcastChannel nicht funktioniert, prüfen Panels alle 500ms localStorage
- **Automatische Synchronisation**: Nach `renderToursFromMatch()`, `renderToursFromWorkflow()` und `renderToursFromCustomers()`
- **Bidirektionale Kommunikation**: 
  - Hauptfenster → Panel: `selectTour()` benachrichtigt Panels
  - Panel → Hauptfenster: `tour-selected` Event wird empfangen
- **Debug-Logging**: Console-Logs mit `[SYNC]`, `[PANEL]`, `[MAIN]` für besseres Debugging

#### Frontend (`frontend/panel-tours.html`)
- **localStorage-Fallback**: Prüft alle 500ms auf neue Daten in localStorage
- **Verbesserte Event-Handler**: Besseres Logging für Debugging

### Technische Details

**BroadcastChannel-Kommunikation:**
- Channel: `trafficapp-panels`
- Events:
  - `tours-update`: Aktualisiert Tour-Liste in Panel
  - `tour-select`: Markiert ausgewählte Tour
  - `route-update`: Aktualisiert Karten-Daten
  - `panel-ready`: Signalisiert, dass Panel bereit ist
  - `panel-closed`: Cleanup beim Schließen

**localStorage-Fallback:**
- Key: `panel-sync-tours`
- Timestamp: `panel-sync-timestamp`
- Panels prüfen alle 500ms auf Änderungen

### Dateien geändert
- `frontend/index.html`: Synchronisations-Logik erweitert
- `frontend/panel-tours.html`: localStorage-Fallback hinzugefügt
- `frontend/js/panel-ipc.js`: (unverändert, funktioniert korrekt)

---

## 2. Route-Details 422-Fehler

### Problem
- Backend gab 422 (Unprocessable Entity) zurück
- Frontend sendete falsches Datenformat
- Routen wurden nur als gerade Linien gezeichnet (keine OSRM-Geometrie)

### Lösung

#### Frontend (`frontend/index.html`)

**Request-Korrektur:**
```javascript
// VORHER (falsch):
{ stops: [{ lat, lon, name, customer_number }], include_depot: true }

// NACHHER (korrekt):
{ stops: [{ lat, lon }] }  // Nur lat/lon, keine zusätzlichen Felder
```

**Response-Verarbeitung:**
- Backend gibt zurück: `{ geometry_polyline6, total_distance_m, total_duration_s, source, warnings, degraded }`
- Frontend verarbeitet jetzt die korrekte Struktur
- Verwendet `decodePolyline6Inline()` für Polyline6-Dekodierung

**Koordinaten-Konvertierung:**
- Konvertiert `latitude`/`longitude` zu `lat`/`lon` falls nötig
- Filtert ungültige Koordinaten (NaN-Check)

### Technische Details

**Backend-Endpoint:**
- `POST /api/tour/route-details`
- Erwartet: `RouteDetailsReq` mit `stops: List[Dict[str, float]]`
- Gibt zurück: `{ geometry_polyline6, total_distance_m, total_duration_s, source, warnings, degraded }`

**Polyline6-Dekodierung:**
- Verwendet `decodePolyline6Inline()` Funktion
- Konvertiert encodierte Polyline6-Strings zu Koordinaten-Arrays
- Zeichnet Route mit Leaflet `L.polyline()`

### Dateien geändert
- `frontend/index.html`: Request-Format und Response-Verarbeitung korrigiert

---

## 3. Weitere Verbesserungen

### Debug-Logging
- `[SYNC]`: Synchronisations-Logs
- `[PANEL]`: Panel-spezifische Logs
- `[MAIN]`: Hauptfenster-Logs
- `[ROUTE-VIS]`: Route-Visualisierungs-Logs
- `[ROUTE-DETAILS]`: Route-Details API-Logs

### Fehlerbehandlung
- Fallback auf gerade Linien, falls OSRM nicht verfügbar
- Validierung von Koordinaten vor dem Senden
- Bessere Fehlermeldungen in der Console

---

## Bekannte Probleme / Offene Punkte

### 1. Match/Upload 500-Fehler
- **Status**: Noch nicht behoben
- **Problem**: `/api/tourplan/match` gibt 500 zurück
- **Nächste Schritte**: Backend-Logs prüfen, Fehlerursache identifizieren

### 2. Blitzer/Hindernisse-Integration
- **Status**: Auskommentiert
- **Grund**: Backend liefert aktuell keine `speed_cameras` oder `traffic_incidents` in route-details Response
- **Nächste Schritte**: Backend erweitern oder separaten Endpoint verwenden

### 3. Panel-Map Synchronisation
- **Status**: Funktioniert, aber könnte optimiert werden
- **Verbesserungspotenzial**: Route-Geometrie könnte direkt an Map-Panel gesendet werden

---

## Testing

### Panel-Synchronisation testen:
1. Hauptfenster öffnen
2. Panels abdocken (Karte, Touren)
3. Tour im Hauptfenster auswählen → Panel sollte markieren
4. Tour im Panel auswählen → Hauptfenster sollte aktualisieren
5. Neue Touren laden → Panels sollten automatisch aktualisiert werden

### Route-Details testen:
1. Tour auswählen
2. Console öffnen (F12)
3. Prüfen auf `[ROUTE-VIS] ✅ Dekodierung erfolgreich`
4. Route sollte auf Karte gezeichnet werden (nicht nur gerade Linien)

---

## Cloud-Sync Checkliste

### Zu synchronisierende Ordner:
- [ ] `backend/` - Backend-Code
- [ ] `frontend/` - Frontend-Code
- [ ] `services/` - Services
- [ ] `db/` - Datenbank-Schema
- [ ] `config/` - Konfigurationsdateien
- [ ] `docs/` - Dokumentation
- [ ] `scripts/` - Scripts
- [ ] `tests/` - Tests
- [ ] `static/` - Statische Dateien
- [ ] `data/` - Daten (falls nicht in .gitignore)

### Wichtige Dateien:
- `frontend/index.html` - Hauptänderungen
- `frontend/panel-tours.html` - Panel-Synchronisation
- `docs/CHANGELOG_2025-01-10.md` - Diese Datei

---

## Nächste Schritte

1. **Match/Upload-Fehler beheben**: Backend-Logs analysieren
2. **Blitzer-Integration**: Backend erweitern oder separaten Endpoint implementieren
3. **Performance-Optimierung**: Panel-Synchronisation könnte optimiert werden (weniger Polling)
4. **Tests schreiben**: Unit-Tests für Panel-Synchronisation und Route-Details

---

## Autoren
- Cursor AI (Auto)

## Datum
10. Januar 2025

