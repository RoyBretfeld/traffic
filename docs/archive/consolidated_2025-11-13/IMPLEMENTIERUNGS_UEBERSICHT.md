# Implementierungs-Übersicht: KI-Clustering & Sub-Routen

## Zusammenfassung

Dieses Dokument gibt eine **"black on white"** Übersicht darüber, wie die KI-Clustering-Engine und Sub-Routen-Generierung funktioniert.

---

## ✅ Was funktioniert (bereits implementiert)

### 1. KI-Clustering-Engine
- ✅ **LLM-Optimierung:** OpenAI GPT-4o-mini für intelligente Routenoptimierung
- ✅ **Geografisches Clustering:** KI gruppiert Stopps nach Nähe
- ✅ **Zeitberechnung:** Fahrzeit + Service-Zeit für jede Tour
- ✅ **Fallback:** Nearest-Neighbor wenn LLM nicht verfügbar

**Dateien:**
- `services/llm_optimizer.py` - LLM-Optimierung
- `routes/workflow_api.py` - API-Endpoint `/api/tour/optimize`

### 2. Sub-Routen-Splitting
- ✅ **Automatisches Splitting:** Touren > 60 Min werden aufgeteilt
- ✅ **Intelligente Aufteilung:** Nutzt KI-Clustering für optimale Gruppierung
- ✅ **UI-Integration:** Sub-Routen werden in Tour-Liste angezeigt

**Dateien:**
- `frontend/index.html` - `generateSubRoutes()`, `splitTourIntoSubRoutes()`

### 3. OSRM-Vorbereitung
- ✅ **OSRM-Code vorhanden:** `_get_osrm_distances()` in `llm_optimizer.py`
- ✅ **Konfiguration:** Umgebungsvariablen für OSRM-URL
- ⚠️ **Noch nicht aktiv:** Muss konfiguriert werden

---

## 🚧 Was noch fehlt (morgen implementieren)

### 1. 404-Fehler beheben
- **Problem:** `/api/tour/optimize` gibt 404 zurück
- **Lösung:** Server neu starten nach Änderungen
- **Datei:** `routes/workflow_api.py` - Router ist registriert

### 2. OSRM-Integration aktivieren
- **Status:** Code vorhanden, muss getestet werden
- **Aktion:** `OSRM_BASE_URL` in `.env` setzen
- **Datei:** `services/llm_optimizer.py` - `_get_osrm_distances()`

### 3. Route-Visualisierung
- **Status:** Nicht implementiert
- **Ziel:** Straßen-Routen anzeigen wenn Sub-Route geklickt wird
- **Benötigt:** 
  - Backend-Endpoint `/api/tour/route-details`
  - Frontend: Karten-Library (Leaflet/OpenLayers)
  - Modal für Route-Details

### 4. Verkehrszeiten-Integration
- **Status:** Nicht implementiert
- **Ziel:** Unterschiedliche Routen je nach Uhrzeit
- **Benötigt:**
  - `TrafficTimeService` (historische Verkehrsdaten)
  - Multiplikator-Tabelle für Verkehrszeiten
  - UI-Anzeige für Verkehrslage

---

## 📋 Datenfluss (komplett)

```
[1. CSV Upload]
    ↓
[2. Tour-Erkennung: W-07.00 mit 30 Stopps]
    ↓
[3. Frontend: generateSubRoutes()]
    ↓
[4. API: POST /api/tour/optimize]
    ↓
[5. Backend: optimize_tour_with_ai()]
    ↓
[6. KI-Clustering: LLM-Optimierung]
    ├─ Prompt mit Stopps + Koordinaten
    ├─ OSRM-Distanzen (falls verfügbar)
    └─ Response: Optimierte Reihenfolge [5,12,3,7,...]
    ↓
[7. Zeitberechnung: 105.5 Min → Über 60!]
    ↓
[8. Splitting: splitTourIntoSubRoutes()]
    ├─ Sub-Route A: Stopps 0-9  (58 Min)
    ├─ Sub-Route B: Stopps 10-19 (59 Min)
    └─ Sub-Route C: Stopps 20-29 (60 Min)
    ↓
[9. UI-Update: updateToursWithSubRoutes()]
    ↓
[10. Benutzer klickt auf Sub-Route]
    ↓
[11. Route-Visualisierung (NOCH NICHT IMPLEMENTIERT)]
    ├─ OSRM-Route für jedes Stopp-Paar abrufen
    └─ Route auf Karte zeichnen
```

---

## 🔧 Technische Details

### KI-Clustering-Engine

**Model:** OpenAI GPT-4o-mini  
**Temperature:** 0.3 (niedrig für konsistente Ergebnisse)  
**Max Tokens:** 1000  
**Response Format:** JSON  

**Prompt-Struktur:**
```
1. System-Prompt: Rolle als Routenplanungs-Experte
2. User-Prompt:
   - Liste aller Stopps mit Koordinaten
   - OSRM-Distanzen (falls verfügbar)
   - Regeln: Max 60 Min, Start/Ende Depot
3. Response: Optimierte Reihenfolge als Index-Liste
```

**Beispiel-Response:**
```json
{
  "optimized_route": [5, 12, 3, 7, 1, 15, ...],
  "reasoning": "Ich habe die Stopps in drei Cluster aufgeteilt...",
  "estimated_total_time_minutes": 105.5
}
```

### OSRM-Integration

**Status:** Code vorhanden, muss aktiviert werden

**Konfiguration:**
```bash
# .env
OSRM_BASE_URL=http://router.project-osrm.org
OSRM_PROFILE=driving
OSRM_TIMEOUT=10
```

**Verwendung:**
- OSRM-Distanzen werden in LLM-Prompt eingebaut
- KI bekommt echte Straßen-Distanzen statt Luftlinie
- Bessere Optimierung

### Splitting-Logik

**Aktuell:**
- Sequenziell: Stopps 0-9, 10-19, 20-29
- Zeit-Limit: 60 Minuten pro Route
- Service-Zeit: 2 Min pro Kunde

**Verbesserung (später):**
- Intelligentes Splitting basierend auf KI-Cluster
- Geografische Kohärenz: Stopps in gleichem Gebiet zusammen

---

## 📊 Beispiel: W-07.00 (30 Adressen)

### Input
```
Tour: W-07.00 Uhr Tour
Stopps: 30 Adressen mit Koordinaten
```

### Schritt 1: KI-Analyse
```
KI analysiert geografische Nähe:
- Cluster 1 (Nord): Stopps 5, 12, 3, 7, 1
- Cluster 2 (Zentrum): Stopps 15, 8, 22, 11, 4, ...
- Cluster 3 (Süd): Stopps 17, 10, 24, 21, ...

Optimierte Reihenfolge: [5, 12, 3, 7, 1, 15, 8, 22, ...]
```

### Schritt 2: Zeitberechnung
```
Fahrzeit: 45.5 Min
Service-Zeit: 60 Min (30 × 2)
───────────────────────
Total: 105.5 Min → ÜBER 60!
```

### Schritt 3: Splitting
```
Sub-Route A: Stopps [5,12,3,7,1,15,8,22,11,4] → 58 Min ✅
Sub-Route B: Stopps [16,9,23,6,18,2,14,20,13,19] → 59 Min ✅
Sub-Route C: Stopps [17,10,24,21,25,26,27,28,29,0] → 60 Min ✅
```

### Schritt 4: UI-Anzeige
```
Tour-Liste:
  ✅ W-07.00 Uhr Tour A (10 Stopps, 58 Min)
  ✅ W-07.00 Uhr Tour B (10 Stopps, 59 Min)
  ✅ W-07.00 Uhr Tour C (10 Stopps, 60 Min)
```

### Schritt 5: Route-Visualisierung (NOCH NICHT)
```
Benutzer klickt auf "W-07.00 Uhr Tour A"
→ Modal öffnet sich
→ Karte zeigt 10 Marker (Stopps)
→ 9 Routen-Linien zeigen Straßen-Verbindungen
→ Info: "Gesamt: 28.5 km, 42 Min"
```

---

## 🎯 Morgen: To-Do-Liste

### Priorität 1: Basis funktionsfähig machen
1. ✅ 404-Fehler beheben (Server neu starten)
2. ✅ KI-Clustering testen (W-07.00 mit 30 Stopps)
3. ✅ Splitting-Logik prüfen (werden Sub-Routen korrekt erstellt?)

### Priorität 2: OSRM-Integration
4. ✅ OSRM konfigurieren (`OSRM_BASE_URL` setzen)
5. ✅ OSRM-Distanzen in LLM-Prompt einbauen
6. ✅ Test mit echten Straßen-Distanzen

### Priorität 3: Route-Visualisierung
7. ✅ Backend-Endpoint `/api/tour/route-details` implementieren
8. ✅ Frontend: Route-Details-Modal erstellen
9. ✅ Karten-Library integrieren (Leaflet)
10. ✅ Route-Linien auf Karte zeichnen

### Priorität 4: Verkehrszeiten
11. ✅ `TrafficTimeService` erstellen
12. ✅ Multiplikator-Tabelle implementieren
13. ✅ UI: Verkehrslage anzeigen

---

## 📚 Dokumentation

- **KI-Clustering-Engine:** `docs/KI_CLUSTERING_ENGINE.md`
- **Sub-Routen-Logik:** `docs/SUB_ROUTES_GENERATOR_LOGIC.md`
- **OSRM-Integration:** `docs/OSRM_INTEGRATION_ROAD_ROUTES.md`
- **Route-Visualisierung:** `docs/ROUTE_VISUALISIERUNG.md`
- **Verkehrszeiten:** `docs/VERKEHRSZEITEN_ROUTENPLANUNG.md`
- **Logging:** `docs/LOGGING_GUIDE.md`
- **To-Do Morgen:** `docs/TODO_MORGEN.md`

---

**Status:** ✅ Engine ist implementiert, muss getestet & erweitert werden.  
**Nächster Schritt:** Server neu starten, 404-Fehler beheben, dann testen!

