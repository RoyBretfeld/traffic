# Multi-Monitor + Manuelle Routen-Bearbeitung + Export

**Erstellt:** 03. November 2025  
**Status:** Geplant  
**Priorität:** Hoch

---

## Übersicht

Implementierung von drei Hauptfeatures:
1. **Multi-Monitor-Support**: Karte, Tourenplanung und Haupt-App auf separaten Monitoren
2. **Manuelle Routen-Bearbeitung**: Drag & Drop für Kunden innerhalb/between Touren
3. **Export zu Maps**: Routen zu Google Maps/Maps App exportieren und an Handy senden

---

## Phase 1: Multi-Monitor-Support

### 1.1 Separate HTML-Dateien erstellen

**Dateien:**
- `frontend/map-view.html` - Nur Karte (für Monitor 1)
- `frontend/tour-overview.html` - Nur Tour-Liste (für Monitor 2)
- `frontend/shared-state.js` - Shared State Management für Synchronisation

**Features:**
- Vollbildfähige Karte auf Monitor 1
- Tour-Liste ohne Karte auf Monitor 2
- Haupt-App (`index.html`) bleibt auf Monitor 3

### 1.2 Backend-Routen hinzufügen

**Datei:** `routes/ui_routes.py` (neu erstellen oder in bestehende Route integrieren)

```python
@app.get("/ui/map-view", response_class=HTMLResponse)
async def map_view():
    """Separate Karten-Ansicht für Multi-Monitor"""

@app.get("/ui/tour-overview", response_class=HTMLResponse)
async def tour_overview():
    """Separate Tour-Übersicht für Multi-Monitor"""
```

### 1.3 Shared State Management

**Datei:** `frontend/shared-state.js`

- `localStorage` Events für Synchronisation zwischen Fenstern
- BroadcastChannel API als Alternative (browser-native)
- Session-ID für Multi-Fenster-Support

### 1.4 Navigation-Button in Haupt-UI

**Datei:** `frontend/index.html`

- Button "Auf Monitor anzeigen" der beide Fenster öffnet
- Fenster-Größe: 1920x1080 (Standard)
- Manuelles Positionieren auf Monitoren (Browser-Limit)

---

## Phase 2: Manuelle Routen-Bearbeitung

### 2.1 Drag & Drop Funktionalität

**Datei:** `frontend/index.html` + `frontend/tour-management.js` (neu)

**Features:**
- **Kunden zwischen Touren verschieben**: Drag & Drop von Tour A → Tour B
- **Reihenfolge innerhalb Tour ändern**: Drag & Drop in Kunden-Liste
- **Visuelles Feedback**: Highlighting während Drag
- **Validierung**: Warnung wenn Zeit-Constraint überschritten wird

**Libraries:**
- HTML5 Drag & Drop API (native)
- Oder: SortableJS (https://sortablejs.github.io/Sortable/)

### 2.2 Backend-API für Route-Updates

**Datei:** `routes/workflow_api.py`

**Neue Endpoints:**
```python
@router.post("/api/tour/{tour_id}/reorder")
async def reorder_tour_stops(tour_id: str, new_order: List[str]):
    """Aktualisiert Reihenfolge der Stopps in einer Tour"""

@router.post("/api/tour/{tour_id}/move-customer")
async def move_customer(customer_id: str, from_tour: str, to_tour: str):
    """Verschiebt Kunde von einer Tour zu einer anderen"""

@router.post("/api/tour/{tour_id}/recalculate")
async def recalculate_route(tour_id: str):
    """Neuberechnung der Route nach manueller Änderung"""
```

### 2.3 Route-Neuberechnung nach Änderung

**Logik:**
- Nach jedem Drag & Drop: OSRM Table API aufrufen für neue Distanzen
- Zeit neu berechnen (Fahrzeit + Servicezeit)
- Warnung wenn > 65 Min (ohne Rückfahrt) oder > 90 Min (mit Rückfahrt)

### 2.4 Undo/Redo Funktionalität

**Datei:** `frontend/route-history.js` (neu)

- Speichere Änderungen in History-Stack
- Undo/Redo Buttons in UI
- Max. 50 Änderungen im Stack

---

## Phase 3: Export zu Maps / Mobile

### 3.1 Google Maps Export

**Datei:** `routes/export_api.py` (neu)

**Endpoints:**
```python
@router.get("/api/export/google-maps/{tour_id}")
async def export_to_google_maps(tour_id: str):
    """Generiert Google Maps URL mit Route"""
    
@router.post("/api/export/google-maps")
async def export_multiple_tours_to_google_maps(tour_ids: List[str]):
    """Exportiert mehrere Touren zu Google Maps"""
```

**Format:**
- Google Maps URL mit waypoints: `https://www.google.com/maps/dir/?api=1&waypoints=...`
- Oder: Google Maps Directions API für detaillierte Route

### 3.2 QR-Code Generation

**Datei:** `frontend/qr-generator.js` (neu)

- QR-Code für Google Maps URL generieren
- Scanner mit Handy → Route öffnet automatisch
- Library: `qrcode.js` oder `qr-scanner`

### 3.3 Weitere Export-Formate

**Optionen:**
- **GPX-Datei**: Für Navigation-Apps (Garmin, etc.)
- **KML-Datei**: Für Google Earth / andere GIS-Tools
- **CSV mit Koordinaten**: Für Excel/andere Tools
- **WhatsApp-Link**: Direkter Link zum Teilen (mit Maps URL)

### 3.4 Backend: Export-Service

**Datei:** `services/export_service.py` (neu)

**Features:**
- Route-Daten zu verschiedenen Formaten konvertieren
- Koordinaten-Reihenfolge beibehalten
- Depot am Anfang/Ende hinzufügen
- Metadaten (Tour-Name, Zeit, etc.) in Export einbetten

---

## Implementierungs-Reihenfolge

1. **Phase 1.1-1.2**: Separate HTML-Dateien + Backend-Routen (1-2 Stunden)
2. **Phase 1.3**: Shared State Management (1 Stunde)
3. **Phase 1.4**: Navigation-Button (30 Min)
4. **Phase 2.1**: Drag & Drop UI (2-3 Stunden)
5. **Phase 2.2**: Backend-API für Updates (1-2 Stunden)
6. **Phase 2.3**: Route-Neuberechnung (1 Stunde)
7. **Phase 2.4**: Undo/Redo (1 Stunde)
8. **Phase 3.1**: Google Maps Export (1-2 Stunden)
9. **Phase 3.2**: QR-Code Generation (1 Stunde)
10. **Phase 3.3-3.4**: Weitere Export-Formate (2-3 Stunden)

**Gesamt:** ~12-16 Stunden Entwicklungszeit

---

## Technische Details

### Shared State Synchronisation

**Option 1: localStorage Events**
- Pro: Einfach, kein Backend nötig
- Contra: Funktioniert nur zwischen Tabs/Fenstern derselben Domain

**Option 2: BroadcastChannel API**
- Pro: Browser-native, besser als localStorage Events
- Contra: Nicht in allen Browsern (aber gut unterstützt)

**Option 3: WebSocket**
- Pro: Echtzeit, Backend-Kontrolle
- Contra: Komplexer, Backend-Änderungen nötig

**Empfehlung:** BroadcastChannel API (Option 2)

### Route-Daten-Struktur

Aktuelle Struktur aus `workflow_api.py`:
```python
{
    "tour_id": "W-07:00",
    "customers": [
        {"name": "...", "lat": ..., "lon": ..., "customer_number": "..."},
        ...
    ],
    "route_uids": ["depot", "stop_1", "stop_2", ..., "depot"],
    "total_time_minutes": 45.5,
    ...
}
```

Für manuelle Bearbeitung:
- Reihenfolge in `route_uids` ändern
- `customers` Array neu sortieren
- Nach Änderung: OSRM Table API für neue Distanzen

### Google Maps URL Format

```
https://www.google.com/maps/dir/?api=1
    &origin=51.0111988,13.7016485  # Depot
    &waypoints=51.05,13.74|51.06,13.75|...  # Kunden-Koordinaten
    &destination=51.0111988,13.7016485  # Depot
    &travelmode=driving
```

---

## ❓ Offene Fragen (für Entscheidung morgen)

### Frage 1: Grafana-Integration
**Wie soll Grafana verwendet werden?**
- a) Für Monitoring/Metriken (Performance, LLM-Calls, etc.)
- b) Für Routen-Visualisierung (statt Leaflet-Karte)
- c) Beides - Monitoring und Routen-Visualisierung
- d) Keine Grafana-Integration gewünscht

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 2: Export-Priorität
**Welches Export-Format ist am wichtigsten?** (Reihenfolge nach Priorität)
- Google Maps URL (für Handy-Navigation)
- GPX-Datei (für Garmin/Nav-Systeme)
- KML-Datei (für Google Earth)
- CSV mit Koordinaten (für Excel)
- WhatsApp-Link (zum Teilen)
- QR-Code (zum Scannen mit Handy)

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 3: Multi-Monitor-Fenster-Positionierung
**Wie sollen die Fenster geöffnet werden?**
- a) Manuell - Button öffnet Fenster, Sie ziehen sie auf die Monitore
- b) Automatisch - Browser versucht automatisch zu positionieren (experimentell, funktioniert nicht in allen Browsern)
- c) Konfiguration - Sie konfigurieren einmal welche Fenster auf welchem Monitor sein sollen

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 4: Route-Verschiebung
**Was soll verschoben werden können?**
- a) Nur einzelne Kunden zwischen Touren
- b) Komplette Routen zwischen Touren verschieben
- c) Beides - einzelne Kunden UND komplette Routen

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 5: Synchronisation zwischen Fenstern
**Wie soll die Synchronisation zwischen den Fenstern funktionieren?**
- a) localStorage Events (einfach, aber nur für gespeicherte Daten)
- b) BroadcastChannel API (browser-native, besser als localStorage)
- c) WebSocket (Echtzeit, benötigt Backend-Änderungen)

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 6: Manuelle Routen-Bearbeitung - Undo/Redo
**Soll es Undo/Redo geben?**
- a) Ja, mit History-Stack (max. 50 Änderungen)
- b) Nein, zu komplex
- c) Nur "Letzte Änderung rückgängig" (kein vollständiger History)

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 7: Route-Neuberechnung
**Wann soll die Route neu berechnet werden?**
- a) Automatisch nach jeder Änderung (Drag & Drop)
- b) Manuell über Button "Route neu berechnen"
- c) Beides - automatisch mit Option für manuelle Neuberechnung

**Ihre Antwort:** _[Hier eintragen]_

---

### Frage 8: Validierung bei Zeit-Überschreitung
**Was passiert wenn eine Route nach manueller Änderung zu lang wird (>65 Min ohne Rückfahrt)?**
- a) Warnung anzeigen, aber Route behalten
- b) Route automatisch zurücksetzen zur letzten gültigen Version
- c) Vorschlag zur Aufteilung in mehrere Routen anbieten

**Ihre Antwort:** _[Hier eintragen]_

---

## Verwandte Dokumentation

- `docs/MULTI_MONITOR_SUPPORT.md` - Existierende Multi-Monitor-Dokumentation
- `docs/TOUR_MANAGEMENT.md` - Existierende Tour-Management-Dokumentation

