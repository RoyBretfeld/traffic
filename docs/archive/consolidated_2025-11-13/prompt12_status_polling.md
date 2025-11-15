# Prompt 12 - Audit-Status + sanftes Polling

## Übersicht

Ein kleiner Status-Endpoint liefert Zähler für eine CSV-Datei, und die bestehende Seite pollt diesen Status alle 5 Sekunden sanft im Hintergrund.

## Implementierte Features

### ✅ **Status-Endpoint**

- **Route**: `/api/tourplan/status?file=...`
- **Zähler**: 
  - `total` - Gesamtanzahl Adressen
  - `cached` - Bereits gecachte Adressen
  - `missing` - Fehlende Adressen
  - `marker_hits` - Mojibake-Marker gefunden
  - `examples_missing` - Erste 5 fehlende Adressen

### ✅ **Polling-JavaScript**

- **Intervall**: 5 Sekunden (`POLL_MS = 5000`)
- **Trigger**: 
  - Bei Dateiwechsel (`#fileSelect` change)
  - Nach Laden (`#loadBtn` click)
  - Nach Geocoding (`#geoBtn` click)
- **Status-Update**: Aktualisiert `#statusBar` mit Zählern
- **Debug-HUD**: Zeigt Status-Updates in Echtzeit

### ✅ **JavaScript-Funktionen**

```javascript
async function refreshStatus()     // Holt Status von API
function startPolling()           // Startet 5s-Intervall
function stopPolling()            // Stoppt Polling
```

## Technische Details

### **Status-Endpoint**
```python
@router.get("/api/tourplan/status")
def api_tourplan_status(file: str = Query(...)):
    # CSV lesen über zentralen Ingest
    df = read_tourplan(p)
    
    # Adressen extrahieren und normalisieren
    col, offset = _addr_col(df)
    addrs = data.iloc[:, col].fillna("").astype(str).map(_norm).tolist()
    
    # DB-Lookup für bereits gecachte Adressen
    geo = bulk_get(addrs)
    
    # Zähler berechnen
    total = len(addrs)
    missing = [a for a in addrs if a and a not in geo]
    marks = sum(1 for a in addrs if any(m in a for m in BAD_MARKERS))
```

### **Polling-Integration**
```javascript
// Polling-Funktionen
const POLL_MS = 5000;
let pollTimer = null;

async function refreshStatus() {
    if (!CURRENT_FILE) return;
    const r = await fetch(`/api/tourplan/status?file=${encodeURIComponent(CURRENT_FILE)}`);
    const j = await r.json();
    const text = `Total ${j.total} • Cached ${j.cached} • Missing ${j.missing}` + 
                 (j.marker_hits ? ` • Marker ${j.marker_hits}` : '');
    document.querySelector('#statusBar').textContent = text;
    HUD.ok(`status: miss=${j.missing}`);
}

function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(refreshStatus, POLL_MS);
}
```

### **Event-Handler-Erweiterung**
```javascript
sel?.addEventListener('change', e => {
    CURRENT_FILE = e.target.value;
    startPolling(); // Polling bei Dateiwechsel starten
});

loadBtn?.addEventListener('click', () => {
    loadMatch().then(() => {
        startPolling(); // Polling nach Laden starten
    }).catch(HUD.err);
});
```

## Verwendung

### 1. **Seite öffnen**
```
http://127.0.0.1:8111/ui/tourplan-management
```

### 2. **Workflow**
1. **Automatisch**: Dateiliste wird geladen, erste CSV ausgewählt
2. **Polling startet**: Alle 5 Sekunden Status-Updates
3. **Status-Leiste**: Zeigt `Total X • Cached Y • Missing Z • Marker W`
4. **Debug-HUD**: Zeigt Status-Updates in Echtzeit

### 3. **Status-Anzeige**
- **Total**: Gesamtanzahl Adressen in der CSV
- **Cached**: Bereits in geo_cache vorhandene Adressen
- **Missing**: Fehlende Adressen (benötigen Geocoding)
- **Marker**: Mojibake-Marker gefunden (Encoding-Probleme)

## Akzeptanzkriterien

✅ **`/api/tourplan/status` liefert** alle benötigten Zähler  
✅ **Bestehende Seite pollt alle 5s** und aktualisiert Status-Leiste  
✅ **Keine Hintergrund-Jobs**; Polling ist unkritisch  
✅ **Unit-Tests bestehen** (4/4 bestanden)  

## Dateien

- **`routes/tourplan_status.py`** - Status-Endpoint
- **`frontend/tourplan-management.html`** - Polling-JavaScript integriert
- **`backend/app.py`** - Route registriert
- **`tests/test_status_api_simple.py`** - Tests (4/4 bestanden)

## Git-Commit

**Branch:** `fix/encoding-unification`  
**Commit:** `c5cf6f2` - "feat: Prompt 12 - Audit-Status + sanftes Polling"
