# Panel-Synchronisation - Technische Dokumentation

## Übersicht

Die Panel-Synchronisation ermöglicht bidirektionale Kommunikation zwischen dem Hauptfenster und abgedockten Panel-Fenstern (Karte, Touren).

## Architektur

### Kommunikations-Kanäle

1. **BroadcastChannel** (Primär)
   - Channel-Name: `trafficapp-panels`
   - Funktioniert zwischen allen Fenstern derselben Origin
   - Event-basiert, asynchron

2. **localStorage** (Fallback)
   - Key: `panel-sync-tours`
   - Timestamp: `panel-sync-timestamp`
   - Polling alle 500ms in Panels
   - Verwendet wenn BroadcastChannel nicht funktioniert

### Event-Typen

#### Hauptfenster → Panel
- `tours-update`: Aktualisiert Tour-Liste
  ```javascript
  { tours: [...], activeTourKey: "workflow-0" }
  ```
- `tour-select`: Markiert ausgewählte Tour
  ```javascript
  { tourKey: "workflow-0" }
  ```
- `route-update`: Aktualisiert Karten-Daten
  ```javascript
  { routes: [...], markers: [...], bounds: [...] }
  ```

#### Panel → Hauptfenster
- `tour-selected`: Tour wurde im Panel ausgewählt
  ```javascript
  { tourKey: "workflow-0" }
  ```
- `panel-ready`: Panel ist bereit
  ```javascript
  { type: "tours" | "map" }
  ```
- `panel-closed`: Panel wurde geschlossen
  ```javascript
  { type: "tours" | "map" }
  ```

## Implementierung

### Hauptfenster (`frontend/index.html`)

#### Synchronisations-Funktionen

**`syncToursToPanel()`**
- Konvertiert `allTourCustomers` zu Panel-Format
- Sendet via BroadcastChannel
- Speichert auch in localStorage (Fallback)

**`syncMapToPanel()`**
- Sammelt Route-Daten von Leaflet-Karte
- Sendet Marker, Routes und Bounds

**`selectTour(key)`**
- Wird erweitert um Panel-Benachrichtigung
- Sendet `tour-select` Event
- Synchronisiert Tour-Liste und Karte

#### Kontinuierliche Synchronisation

```javascript
// Tours-Panel
const syncInterval = setInterval(() => {
    if (toursPanelWindow.closed) {
        clearInterval(syncInterval);
        return;
    }
    syncToursToPanel();
}, 1000); // Alle 1 Sekunde

// Map-Panel
const syncInterval = setInterval(() => {
    if (mapPanelWindow.closed) {
        clearInterval(syncInterval);
        return;
    }
    syncMapToPanel();
}, 1000); // Alle 1 Sekunde
```

#### Event-Listener

```javascript
window.panelIPC.on('panel-ready', (data) => {
    if (data.type === 'tours') {
        syncToursToPanel();
    } else if (data.type === 'map') {
        syncMapToPanel();
    }
});

window.panelIPC.on('tour-selected', (data) => {
    if (data.tourKey && allTourCustomers[data.tourKey]) {
        selectTour(data.tourKey);
    }
});
```

### Panel (`frontend/panel-tours.html`)

#### Event-Listener

```javascript
window.panelIPC.on('tours-update', (data) => {
    tours = data.tours || [];
    activeTourKey = data.activeTourKey || null;
    renderTours();
});

window.panelIPC.on('tour-select', (data) => {
    activeTourKey = data.tourKey || null;
    renderTours();
});
```

#### localStorage-Fallback

```javascript
let lastSyncTimestamp = 0;
setInterval(() => {
    const syncTimestamp = parseInt(localStorage.getItem('panel-sync-timestamp') || '0');
    if (syncTimestamp > lastSyncTimestamp) {
        lastSyncTimestamp = syncTimestamp;
        const syncData = localStorage.getItem('panel-sync-tours');
        if (syncData) {
            const data = JSON.parse(syncData);
            tours = data.tours || [];
            activeTourKey = data.activeTourKey || null;
            renderTours();
        }
    }
}, 500);
```

## Datenstrukturen

### Tour-Format (Panel)

```javascript
{
    key: "workflow-0",
    name: "W-07.00 Uhr Tour",
    stops: 29,
    distance: 0,  // Wird später geladen
    duration: 0   // Wird später geladen
}
```

### Route-Format (Map-Panel)

```javascript
{
    routes: [{
        geometry: "polyline6-string",
        color: "#3388ff",
        geometry_type: "polyline6"
    }],
    markers: [{
        lat: 51.01127,
        lon: 13.70161,
        name: "FAMO Depot",
        color: "#9c27b0"
    }],
    bounds: [[south, west], [north, east]]
}
```

## Debugging

### Console-Logs

- `[SYNC]`: Synchronisations-Logs im Hauptfenster
- `[PANEL]`: Panel-spezifische Logs
- `[MAIN]`: Hauptfenster-Logs

### Beispiel-Logs

```
[SYNC] Sende Tours-Update: { tourCount: 19, activeTourKey: "workflow-0", ... }
[PANEL] Tours-Update erhalten: { tours: [...], activeTourKey: "workflow-0" }
[PANEL] Tours-Update aus localStorage: { tours: [...], activeTourKey: "workflow-0" }
```

## Fehlerbehandlung

### BroadcastChannel nicht verfügbar
- Fallback auf localStorage
- Warnung in Console: `[SYNC] panelIPC nicht verfügbar`

### Panel geschlossen
- Interval wird automatisch beendet
- Cleanup beim `panel-closed` Event

### Ungültige Daten
- Validierung vor dem Senden
- Fallback auf leere Arrays/Objekte

## Performance

### Optimierungen
- Polling-Intervalle: 1 Sekunde (Hauptfenster), 500ms (Panel localStorage)
- Nur bei Änderungen synchronisieren (Tour-Count-Check)
- Cleanup bei geschlossenen Panels

### Verbesserungspotenzial
- Event-basierte Synchronisation statt Polling
- Debouncing bei häufigen Updates
- Komprimierung großer Datenstrukturen

## Bekannte Probleme

1. **BroadcastChannel-Browser-Support**: Nicht in allen Browsern verfügbar
   - Lösung: localStorage-Fallback

2. **Performance bei vielen Touren**: Kann bei 100+ Touren langsam werden
   - Lösung: Pagination oder Virtual Scrolling

3. **Map-Panel Route-Geometrie**: Wird aktuell nicht direkt synchronisiert
   - Lösung: Route-Geometrie direkt an Map-Panel senden

## Testing

### Manuelle Tests

1. **Bidirektionale Synchronisation**:
   - Tour im Hauptfenster auswählen → Panel markiert
   - Tour im Panel auswählen → Hauptfenster aktualisiert

2. **Automatische Synchronisation**:
   - Neue Touren laden → Panels aktualisieren automatisch
   - Tour-Details ändern → Panels aktualisieren automatisch

3. **Fallback-Test**:
   - BroadcastChannel deaktivieren (DevTools)
   - localStorage-Fallback sollte funktionieren

### Automatisierte Tests

```javascript
// TODO: Unit-Tests für Panel-Synchronisation
describe('Panel Synchronisation', () => {
    it('should sync tours to panel', () => {
        // Test implementation
    });
    
    it('should handle panel selection', () => {
        // Test implementation
    });
});
```

## Wartung

### Regelmäßige Checks
- BroadcastChannel-Browser-Support prüfen
- Performance bei vielen Touren testen
- localStorage-Quota überwachen

### Code-Review-Punkte
- Interval-Cleanup korrekt implementiert?
- Event-Listener werden entfernt?
- Fehlerbehandlung vorhanden?

