# Multi-Monitor Support

**Status:** 🚧 Geplant  
**Priorität:** Medium  
**Datum:** 2025-01-09

---

## Ziel

Die Möglichkeit, die **Karte** und die **Tour-Übersicht** gleichzeitig auf verschiedenen Monitoren anzuzeigen, um:
- Bessere Übersicht beim Planen
- Größere Karte auf einem separaten Monitor
- Tour-Liste parallel sichtbar

---

## Anforderungen

### 1. Separates Fenster für Karte
- **Route:** `/ui/map-view` (neues HTML)
- **Inhalt:** Nur die Leaflet-Karte mit allen Tour-Markern und Routen
- **Größe:** Vollbildfähig (kann auf zweiten Monitor maximiert werden)
- **Interaktiv:** Marker-Klicks, Zoom, Pan

### 2. Separates Fenster für Tour-Übersicht
- **Route:** `/ui/tour-overview` (neues HTML)
- **Inhalt:** Tour-Liste (Cards) ohne Karte
- **Features:**
  - Tour-Filterung
  - Tour-Details (Kundenliste)
  - BAR-Flags
  - Zeit-Anzeigen

### 3. Synchronisation
- **WebSocket oder Shared State:** Änderungen in einem Fenster werden im anderen angezeigt
- **Shared Session:** Beide Fenster verwenden dieselbe Session-ID
- **LocalStorage:** Syncing via `localStorage` Events

---

## Implementierung

### Phase 1: Separate HTML-Dateien

#### `frontend/map-view.html`
```html
<!DOCTYPE html>
<html>
<head>
    <title>FAMO TrafficApp - Karte</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        body { margin: 0; padding: 0; }
        #map { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script>
        // Shared State aus localStorage lesen
        // Karte initialisieren
        // Marker und Routen zeichnen
    </script>
</body>
</html>
```

#### `frontend/tour-overview.html`
```html
<!DOCTYPE html>
<html>
<head>
    <title>FAMO TrafficApp - Tour-Übersicht</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container-fluid">
        <h1>Tour-Übersicht</h1>
        <div id="tourList"></div>
    </div>
    <script>
        // Shared State aus localStorage lesen
        // Tour-Liste rendern
    </script>
</body>
</html>
```

### Phase 2: Shared State Management

#### `frontend/shared-state.js`
```javascript
class SharedState {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.storageKey = `famo_tours_${sessionId}`;
        
        // Listener für localStorage-Änderungen
        window.addEventListener('storage', (e) => {
            if (e.key === this.storageKey) {
                this.onStateChange(JSON.parse(e.newValue));
            }
        });
    }
    
    save(tours) {
        localStorage.setItem(this.storageKey, JSON.stringify(tours));
        // Trigger custom event für aktuelles Fenster
        window.dispatchEvent(new CustomEvent('stateChanged', { detail: tours }));
    }
    
    load() {
        const data = localStorage.getItem(this.storageKey);
        return data ? JSON.parse(data) : null;
    }
    
    onStateChange(tours) {
        // Wird in abgeleiteten Klassen implementiert
    }
}
```

### Phase 3: Backend-Routen

#### `routes/ui_routes.py`
```python
@app.get("/ui/map-view", response_class=HTMLResponse)
async def map_view():
    """Separate Karten-Ansicht für Multi-Monitor"""
    with open("frontend/map-view.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/ui/tour-overview", response_class=HTMLResponse)
async def tour_overview():
    """Separate Tour-Übersicht für Multi-Monitor"""
    with open("frontend/tour-overview.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
```

---

## Navigation in Haupt-UI

### Button "Auf zweitem Monitor anzeigen"

In `frontend/index.html`:
```html
<button class="btn btn-secondary" onclick="openOnSecondMonitor()">
    <i class="fas fa-external-link-alt"></i> Auf zweitem Monitor anzeigen
</button>
```

```javascript
function openOnSecondMonitor() {
    const sessionId = getCurrentSessionId();
    const mapUrl = `/ui/map-view?session=${sessionId}`;
    const tourUrl = `/ui/tour-overview?session=${sessionId}`;
    
    // Öffne in separatem Fenster (kann manuell auf zweiten Monitor ziehen)
    window.open(mapUrl, 'FAMO_Karte', 'width=1920,height=1080');
    window.open(tourUrl, 'FAMO_Touren', 'width=1920,height=1080');
}
```

---

## Nächste Schritte

1. ✅ Dokumentation erstellt (dieses Dokument)
2. ⬜ `frontend/map-view.html` erstellen
3. ⬜ `frontend/tour-overview.html` erstellen
4. ⬜ Shared State Management implementieren
5. ⬜ Backend-Routen hinzufügen
6. ⬜ Button in Haupt-UI integrieren
7. ⬜ Tests mit zwei Monitoren

---

**Hinweis:** Dies ist eine geplante Feature. Die Implementierung kann schrittweise erfolgen.

