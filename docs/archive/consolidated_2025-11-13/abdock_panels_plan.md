# Plan: Abdockbare Panels (Phase 2)

**Status:** Plan-Stub für Phase 2  
**Erstellt:** 2025-01-10  
**Priorität:** Phase 2 (Kurzfristig)

---

## Ziel

Karte und Tour-Übersicht sollen in separate, abdockbare Fenster ausgelagert werden können. Dies ermöglicht Multi-Monitor-Setups und bessere Übersicht.

---

## Technische Umsetzung (Vanilla JS)

### 1. Fenster-Management

**Technologie:** `window.open()` + `BroadcastChannel` / `postMessage`

```javascript
// Hauptfenster öffnet Panel-Fenster
const panelWindow = window.open('/panel-map.html', 'mapPanel', 'width=800,height=600');

// Kommunikation via BroadcastChannel
const channel = new BroadcastChannel('trafficapp-panels');
channel.postMessage({ type: 'route-update', data: routeData });
```

### 2. Layout-Persistenz

**Speicherung:** `localStorage`

```javascript
// Speichere Panel-Positionen
localStorage.setItem('panel-layout', JSON.stringify({
    map: { x: 100, y: 100, width: 800, height: 600 },
    tours: { x: 920, y: 100, width: 400, height: 600 }
}));
```

### 3. IPC-Schema

**Nachrichten-Typen:**

- `route-update`: Route-Daten aktualisieren
- `tour-select`: Tour auswählen
- `map-zoom`: Karten-Zoom ändern
- `panel-close`: Panel schließen

---

## Risiken & Tests

### Risiken:

1. **Browser-Popup-Blocker:** Kann `window.open()` blockieren
   - **Lösung:** User-Interaktion erforderlich (Button-Klick)

2. **Cross-Origin:** Wenn Panel auf anderer Domain
   - **Lösung:** Gleiche Domain verwenden

3. **Opener-Policy:** Sicherheitsrisiko bei `window.opener`
   - **Lösung:** `rel="noopener"` oder `window.opener = null`

4. **Fenster-Verlust:** Panel-Fenster kann geschlossen werden
   - **Lösung:** Warnung + Reopen-Button

### Tests:

- [ ] Panel öffnet sich korrekt
- [ ] Kommunikation funktioniert (Hauptfenster ↔ Panel)
- [ ] Layout wird gespeichert und wiederhergestellt
- [ ] Panel schließt sich sauber
- [ ] Multi-Panel (Karte + Tours) funktioniert

---

## Security-Hinweise

1. **Opener-Policy:** `window.opener = null` nach Öffnen setzen
2. **Content-Security-Policy:** Erlaube `window.open` in CSP
3. **XSS-Schutz:** Keine unsicheren Daten in `postMessage`

---

## Implementierung (Phase 2)

### Dateien:

- `frontend/panel-map.html` (neue Datei)
- `frontend/panel-tours.html` (neue Datei)
- `frontend/js/panel-ipc.js` (neue Datei)
- `frontend/index.html` (erweitern: Panel-Buttons)

### Schritte:

1. Panel-HTML-Seiten erstellen
2. IPC-Kommunikation implementieren
3. Layout-Persistenz hinzufügen
4. Button zum Abdocken in Hauptseite
5. Tests schreiben

---

**Status:** 🟡 Geplant für Phase 2

