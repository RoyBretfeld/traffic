# Prompt 11 - Frontend-Integration & Debug-HUD

## Übersicht

Die bestehende Seite auf `http://127.0.0.1:8111` wurde um neue Backend-Endpoints erweitert, ohne das Layout zu ändern. Es wurde nur minimaler JavaScript-Code hinzugefügt.

## Implementierte Features

### ✅ **API-Endpoints**

- **`/api/tourplaene/list`** - Listet alle verfügbaren CSV-Dateien auf
- **`/api/tourplan/match`** - Matcht Adressen gegen geo_cache (bereits vorhanden)
- **`/api/tourplan/geocode-missing`** - Geokodiert fehlende Adressen (bereits vorhanden)

### ✅ **Frontend-Integration**

- **Neue Seite**: `/ui/tourplan-management`
- **Same-Origin**: API_BASE = "" (gleiche Origin)
- **CORS**: Bereits konfiguriert für alle Origins

### ✅ **UI-Elemente**

- **`#fileSelect`** - Dropdown für CSV-Auswahl
- **`#loadBtn`** - Button zum Laden der Match-Daten
- **`#geoBtn`** - Button für Geocoding fehlender Adressen
- **`#limitInput`** - Eingabe für Geocoding-Limit (1-100)
- **`#dryRun`** - Checkbox für Dry-Run-Modus
- **`#statusBar`** - Status-Anzeige (OK • WARN • BAD)
- **`#tableBody`** - Tabelle für Adress-Ergebnisse
- **`#map`** - Leaflet-Karte für Geo-Daten

### ✅ **Debug-HUD**

- **Position**: Oben rechts (fixed)
- **Features**:
  - Zeigt letzte API-Aufrufe
  - Erfolgreiche Operationen (grün)
  - Fehler (rot)
  - Zeitstempel
  - Begrenzt auf 10 Einträge

### ✅ **JavaScript-Funktionen**

```javascript
// API-Zugriff
async function apiList()           // Lädt CSV-Liste
async function apiMatch(filePath)  // Matcht Adressen
async function apiGeoFill(...)     // Geokodiert fehlende

// UI-Funktionen
async function refreshFiles()      // Aktualisiert Dateiliste
async function loadMatch()         // Lädt und zeigt Matches
async function runGeoFill()       // Führt Geocoding aus
```

### ✅ **Fehlerbehandlung**

- **HTTP 400**: "Encoding-Bug erkannt..." (Mojibake-Guard)
- **HTTP 503**: "DB nicht erreichbar"
- **JSON-Parse-Fehler**: Zeigt ersten Teil der Antwort
- **Globale Fehlerbehandlung**: `window.addEventListener('error')`

## Verwendung

### 1. **Seite öffnen**
```
http://127.0.0.1:8111/ui/tourplan-management
```

### 2. **Workflow**
1. **Automatisch**: Dateiliste wird geladen, erste CSV ausgewählt
2. **"Laden"**: Zeigt Match-Status aller Adressen
3. **"Geocode fehlende"**: Geokodiert fehlende Adressen (mit Limit & Dry-Run)

### 3. **Debug-HUD**
- Zeigt alle API-Aufrufe in Echtzeit
- Erfolgreiche Operationen: ✔ grün
- Fehler: ✖ rot
- Zeitstempel für jeden Eintrag

## Technische Details

### **API-Basis**
```javascript
const API_BASE = ""; // Same-Origin
```

### **CORS-Konfiguration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Alle Origins erlaubt
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Fehlerbehandlung**
- Alle API-Aufrufe mit `.catch(HUD.err)`
- Spezielle Behandlung für HTTP 400/503
- Globale JavaScript-Fehlerbehandlung

## Akzeptanzkriterien

✅ **Seite lädt Dateiliste** beim Start aus `/api/tourplaene/list`  
✅ **"Laden" ruft `/api/tourplan/match`** auf, zeigt ok/warn/bad  
✅ **"Geocode fehlende" ruft `/api/tourplan/geocode-missing`** auf  
✅ **Debug-HUD zeigt Aktionen/Fehler** in Echtzeit  
✅ **Keine Layout-Änderungen**, nur minimale IDs/JS ergänzt  
✅ **Tests bestehen** (4/4 bestanden)

## Dateien

- **`routes/tourplaene_list.py`** - Neuer API-Endpoint
- **`frontend/tourplan-management.html`** - Neue Frontend-Seite
- **`backend/app.py`** - Route registriert
- **`tests/test_prompt11_ui_bindings.py`** - Tests (4/4 bestanden)
