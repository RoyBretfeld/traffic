# Audit: 500 Internal Server Error bei `/api/tour/optimize`

**Datum:** 2025-01-10  
**Status:** KRITISCH - Alle Optimierungs-Requests schlagen fehl  
**Betroffene Endpoints:** `POST /api/tour/optimize`

---

## Problembeschreibung

Alle 5 Touren (W-07.00, W-09.00, W-11.00, W-14.00, W-16.00 Uhr Tour) erhalten einen **500 Internal Server Error** beim Aufruf von `/api/tour/optimize`.

### Symptome:
- **Frontend:** Browser-Konsole zeigt `500 (Internal Server Error)` für alle Touren
- **Backend:** Keine detaillierten Fehlermeldungen im Browser (errorDetail: null)
- **Betroffen:** Alle Touren mit > 4 Kunden (24, 38, 49, 40, 15 Stopps)
- **Fehler:** `Keine Sub-Routen generiert: API-Fehler bei allen 5 Tour(en)`

### Browser-Konsole (Frontend):
```
❌ Failed to load resource: the server :8111/api/tour/optimize:1 responded with a status of 500 (Internal Server Error)
► [SUB-ROUTES] API-Fehler für Tour W-07.00 Uhr Tour: {status: 500, error: 'Internal Server Error', errorDetail: null}
[SUB-ROUTES] Verarbeitung abgeschlossen: 0 erfolgreich, 5 Fehler
```

---

## Relevante Code-Stellen

### 1. Backend: `/api/tour/optimize` Endpoint

**Datei:** `routes/workflow_api.py` (Zeile 1885-2357)

```python
@router.post("/api/tour/optimize")
async def optimize_tour_with_ai(request: Request):
    try:
        try:
            body = await request.json()
        except Exception as json_error:
            print(f"[TOUR-OPTIMIZE] FEHLER beim Parsen des Request-Bodies: {json_error}")
            raise HTTPException(400, detail=f"Ungültiger Request-Body: {str(json_error)}")
        
        tour_id = body.get("tour_id", "Unbekannt")
        stops = body.get("stops", [])
        
        # Filtere Stopps mit Koordinaten
        valid_stops = []
        for s in stops:
            if s.get('lat') and s.get('lon'):
                valid_stops.append(s)
        
        # WICHTIG: Prüfe OSRM-Verfügbarkeit BEVOR optimiert wird
        osrm_client_check = get_osrm_client()
        osrm_health = osrm_client_check.check_health()
        
        if osrm_health["status"] != "ok":
            return JSONResponse({
                "success": False,
                "error": f"OSRM nicht verfügbar: {osrm_health['message']}",
            }, status_code=503)
        
        # AI-Optimierung: LLM oder Nearest-Neighbor
        try:
            if llm_optimizer.enabled:
                result = llm_optimizer.optimize_route(valid_stops, region="Dresden")
                optimized_indices = result.optimized_route
                reasoning = result.reasoning
                method = result.model_used
            else:
                # Nearest-Neighbor Fallback
                optimized_stops_list = optimize_tour_stops(valid_stops, use_llm=False)
                optimized_indices = [...]  # Index-Mapping
                method = "nearest_neighbor"
        except Exception as opt_error:
            print(f"[TOUR-OPTIMIZE] UNERWARTETER FEHLER: {opt_error}")
            raise HTTPException(500, detail=f"Optimierung fehlgeschlagen: {str(opt_error)[:200]}")
        
        # WICHTIG: Prüfe ob optimized_indices definiert ist
        if 'optimized_indices' not in locals() or optimized_indices is None:
            raise HTTPException(500, detail="Optimierung fehlgeschlagen: Keine optimierte Route generiert")
        
        # Erstelle optimierte Stopps-Liste
        optimized_stops = []
        for i in optimized_indices:
            optimized_stops.append(dict(valid_stops[i]))
        
        # Zeitberechnung
        estimated_driving_time = _calculate_tour_time(optimized_stops)
        estimated_service_time = len(valid_stops) * 2
        estimated_total_time = estimated_driving_time + estimated_service_time
        
        # KRITISCHE VALIDIERUNG: Tour MUSS ≤ 65 Min OHNE Rückfahrt sein!
        if estimated_total_time > TIME_BUDGET_WITHOUT_RETURN:
            try:
                split_tours = enforce_timebox(tour_id, optimized_stops, max_depth=3)
                # ... Aufteilung ...
            except Exception as split_error:
                print(f"[TOUR-OPTIMIZE] FEHLER beim Aufteilen: {split_error}")
                # Tour wird trotzdem zurückgegeben
        
        return JSONResponse({
            "success": True,
            "tour_id": tour_id,
            "optimized_stops": optimized_stops,
            "estimated_driving_time_minutes": round(estimated_driving_time, 1),
            # ...
        })
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[TOUR-OPTIMIZE] UNERWARTETER FEHLER: {e}")
        print(f"[TOUR-OPTIMIZE] Traceback:\n{error_trace}")
        raise HTTPException(500, detail=f"Tour-Optimierung fehlgeschlagen: {str(e)}")
```

### 2. Frontend: `generateSubRoutes()` Funktion

**Datei:** `frontend/index.html` (Zeile 3146-3521)

```javascript
async function generateSubRoutes() {
    const toursToOptimize = workflowResult.tours.filter(t => {
        const stops = t.stops || [];
        return stops.length > 4 && t.tour_id && t.tour_id.toUpperCase().startsWith('W-');
    });
    
    for (const tour of toursToOptimize) {
        const stopsWithCoords = tour.stops.filter(s => s.lat && s.lon);
        
        const response = await fetch('/api/tour/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tour_id: tour.tour_id,
                is_bar_tour: tour.is_bar_tour || false,
                stops: stopsWithCoords.map(s => ({
                    customer_number: s.order_id || s.customer_number || '',
                    name: s.customer || s.name || 'Unbekannt',
                    address: s.address || '',
                    lat: s.lat,
                    lon: s.lon,
                    // ...
                }))
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[SUB-ROUTES] API-Fehler für Tour ${tour.tour_id}:`, {
                status: response.status,
                error: errorText.substring(0, 500),
                errorDetail: (() => {
                    try { return JSON.parse(errorText); } catch(e) { return null; }
                })()
            });
            errorCount++;
            continue;
        }
        
        const result = await response.json();
        // ... Verarbeitung ...
    }
}
```

### 3. OSRM Client

**Datei:** `services/osrm_client.py`

```python
class OSRMClient:
    def check_health(self) -> Dict[str, Any]:
        """Prüft ob OSRM-Server erreichbar ist"""
        try:
            # Test-Request
            r = await s.get(f"{self.base_url}/nearest/v1/driving/13.7373,51.0504?number=1")
            return {"status": "ok" if 200 <= r.status_code < 300 else "error", ...}
        except Exception as ex:
            return {"status": "error", "message": str(ex)}
    
    def get_route(self, coords: List[Tuple[float, float]], use_polyline6: bool = False) -> Dict:
        """Holt Route von OSRM"""
        # ...
```

### 4. AI Optimizer

**Datei:** `backend/services/ai_optimizer.py`

```python
class AIOptimizer:
    def optimize_route(self, stops: List[Dict], region: str = "Dresden") -> OptimizationResult:
        """Optimiert Route mit LLM"""
        # Erstellt System-Prompt
        # Ruft LLM auf
        # Parst Response
        # Gibt OptimizationResult zurück
```

---

## Mögliche Ursachen

### 1. **`optimized_indices` nicht definiert**
- **Problem:** Wenn LLM-Optimierung fehlschlägt UND Nearest-Neighbor auch fehlschlägt, ist `optimized_indices` nicht definiert
- **Lösung:** Prüfung hinzugefügt (Zeile 2131-2134), aber Fehler kommt wahrscheinlich VORHER

### 2. **Fehler in `enforce_timebox()`**
- **Problem:** Wenn Tour > 65 Min ist, wird `enforce_timebox()` aufgerufen, könnte fehlschlagen
- **Lösung:** Exception-Handling hinzugefügt, aber Fehler kommt wahrscheinlich VORHER

### 3. **Fehler in `_calculate_tour_time()`**
- **Problem:** Funktion könnte fehlschlagen wenn OSRM nicht verfügbar oder Stopps ungültig
- **Lösung:** Fallback vorhanden, aber könnte trotzdem fehlschlagen

### 4. **LLM-Optimierung fehlschlägt**
- **Problem:** `llm_optimizer.optimize_route()` könnte Exception werfen
- **Lösung:** Exception wird gefangen, aber Nearest-Neighbor könnte auch fehlschlagen

### 5. **Nearest-Neighbor fehlschlägt**
- **Problem:** `optimize_tour_stops()` oder Index-Mapping könnte fehlschlagen
- **Lösung:** Exception wird gefangen, aber dann ist `optimized_indices` nicht definiert

### 6. **OSRM-Problem**
- **Problem:** OSRM könnte nicht verfügbar sein, aber Health-Check könnte trotzdem "ok" zurückgeben
- **Lösung:** Health-Check vorhanden, aber könnte Race-Condition haben

---

## Nächste Schritte

### 1. **Server-Logs prüfen**
- **Wo:** Server-Terminal (wo `python start_server.py` läuft)
- **Suchen nach:** `[TOUR-OPTIMIZE] FEHLER` oder `[TOUR-OPTIMIZE] Traceback`
- **Erwartung:** Vollständiger Python-Traceback mit genauer Fehlerstelle

### 2. **Debug-Logging aktivieren**
- **Datei:** `routes/workflow_api.py`
- **Hinzufügen:** Mehr `print()` Statements vor kritischen Stellen
- **Zweck:** Genau sehen, wo der Fehler auftritt

### 3. **Minimal-Test erstellen**
- **Zweck:** Isolieren des Problems
- **Test:** Einfache Tour mit 2-3 Stopps testen
- **Erwartung:** Sollte funktionieren, wenn Problem touren-spezifisch ist

### 4. **OSRM-Verfügbarkeit prüfen**
- **Test:** `curl http://127.0.0.1:8111/health/osrm` oder Browser
- **Erwartung:** Sollte `{"status": "ok"}` zurückgeben

### 5. **LLM-Status prüfen**
- **Test:** Prüfen ob `llm_optimizer.enabled` True ist
- **Erwartung:** Sollte True sein, oder Nearest-Neighbor sollte funktionieren

---

## Vollständige Code-Ausschnitte

### 1. Backend: `optimize_tour_with_ai()` - Vollständige Funktion

**Datei:** `routes/workflow_api.py` (Zeile 1885-2362)

```python
@router.post("/api/tour/optimize")
async def optimize_tour_with_ai(request: Request):
    try:
        try:
            body = await request.json()
        except Exception as json_error:
            print(f"[TOUR-OPTIMIZE] FEHLER beim Parsen des Request-Bodies: {json_error}")
            raise HTTPException(400, detail=f"Ungültiger Request-Body: {str(json_error)}")
        
        tour_id = body.get("tour_id", "Unbekannt")
        stops = body.get("stops", [])
        
        # Filtere Stopps mit Koordinaten
        valid_stops = []
        for s in stops:
            if s.get('lat') and s.get('lon'):
                valid_stops.append(s)
        
        # OSRM-Check
        osrm_client_check = get_osrm_client()
        osrm_health = osrm_client_check.check_health()
        if osrm_health["status"] != "ok":
            return JSONResponse({"success": False, "error": f"OSRM nicht verfügbar"}, status_code=503)
        
        # AI-Optimierung
        try:
            if llm_optimizer.enabled:
                result = llm_optimizer.optimize_route(valid_stops, region="Dresden")
                optimized_indices = result.optimized_route
            else:
                optimized_stops_list = optimize_tour_stops(valid_stops, use_llm=False)
                optimized_indices = [...]  # Index-Mapping
        except Exception as opt_error:
            raise HTTPException(500, detail=f"Optimierung fehlgeschlagen: {str(opt_error)[:200]}")
        
        # Prüfe ob optimized_indices definiert ist
        if 'optimized_indices' not in locals() or optimized_indices is None:
            raise HTTPException(500, detail="Optimierung fehlgeschlagen: Keine optimierte Route generiert")
        
        # Erstelle optimierte Stopps-Liste
        optimized_stops = []
        for i in optimized_indices:
            optimized_stops.append(dict(valid_stops[i]))
        
        # Zeitberechnung
        estimated_driving_time = _calculate_tour_time(optimized_stops)
        estimated_service_time = len(valid_stops) * 2
        estimated_total_time = estimated_driving_time + estimated_service_time
        
        # Zeit-Constraint-Prüfung
        if estimated_total_time > TIME_BUDGET_WITHOUT_RETURN:
            try:
                split_tours = enforce_timebox(tour_id, optimized_stops, max_depth=3)
                # ... Aufteilung ...
            except Exception as split_error:
                print(f"[TOUR-OPTIMIZE] FEHLER beim Aufteilen: {split_error}")
        
        return JSONResponse({
            "success": True,
            "tour_id": tour_id,
            "optimized_stops": optimized_stops,
            "estimated_driving_time_minutes": round(estimated_driving_time, 1),
            # ...
        })
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[TOUR-OPTIMIZE] UNERWARTETER FEHLER: {e}")
        print(f"[TOUR-OPTIMIZE] Traceback:\n{error_trace}")
        raise HTTPException(500, detail=f"Tour-Optimierung fehlgeschlagen: {str(e)}")
```

### 2. Frontend: `generateSubRoutes()` - Vollständige Funktion

**Datei:** `frontend/index.html` (Zeile 3146-3521)

```javascript
async function generateSubRoutes() {
    const toursToOptimize = workflowResult.tours.filter(t => {
        const stops = t.stops || [];
        return stops.length > 4 && t.tour_id && t.tour_id.toUpperCase().startsWith('W-');
    });
    
    for (const tour of toursToOptimize) {
        const stopsWithCoords = tour.stops.filter(s => s.lat && s.lon);
        
        const response = await fetch('/api/tour/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tour_id: tour.tour_id,
                is_bar_tour: tour.is_bar_tour || false,
                stops: stopsWithCoords.map(s => ({
                    customer_number: s.order_id || s.customer_number || '',
                    name: s.customer || s.name || 'Unbekannt',
                    address: s.address || '',
                    lat: s.lat,
                    lon: s.lon,
                    // ...
                }))
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[SUB-ROUTES] API-Fehler für Tour ${tour.tour_id}:`, {
                status: response.status,
                error: errorText.substring(0, 500),
                errorDetail: (() => {
                    try { return JSON.parse(errorText); } catch(e) { return null; }
                })()
            });
            errorCount++;
            continue;
        }
        
        const result = await response.json();
        // ... Verarbeitung ...
    }
}
```

### 3. Backend: `enforce_timebox()` - Vollständige Funktion

**Datei:** `routes/workflow_api.py` (Zeile 347-423)

```python
def enforce_timebox(tour_name: str, stops: List[Dict], max_depth: int = 3) -> List[Dict]:
    """Validiert hart gegen 65/90 und splittet ggf. automatisch."""
    if not stops:
        return []
    
    if max_depth <= 0:
        est_no_return = _estimate_tour_time_without_return(stops, use_osrm=True)
        back_minutes = _estimate_back_to_depot_minutes(stops[-1]) if stops else 0.0
        return [materialize_tour(tour_name, stops, est_no_return, back_minutes)]
    
    # Berechne Zeit OHNE Rückfahrt
    est_no_return = _estimate_tour_time_without_return(stops, use_osrm=True)
    back_minutes = _estimate_back_to_depot_minutes(stops[-1]) if stops else 0.0
    
    # Prüfe gegen Limits
    if est_no_return > TIME_BUDGET_WITHOUT_RETURN or (est_no_return + back_minutes) > TIME_BUDGET_WITH_RETURN:
        split_tours = _split_large_tour_in_workflow(tour_name, stops, TIME_BUDGET_WITHOUT_RETURN)
        validated_subs = []
        for sub_tour in split_tours:
            sub_stops = sub_tour.get("stops", [])
            if sub_stops:
                est_no_return = sub_tour.get("estimated_time_minutes", 
                    _estimate_tour_time_without_return(sub_stops, use_osrm=True))
                back_minutes = _estimate_back_to_depot_minutes(sub_stops[-1]) if sub_stops else 0.0
                validated_subs.append(materialize_tour(sub_tour["tour_id"], sub_stops, est_no_return, back_minutes))
        return validated_subs
    
    # Route ist OK → materialisiere
    tour_dict = materialize_tour(tour_name, stops, est_no_return, back_minutes)
    return [tour_dict]
```

### 4. Backend: `_calculate_tour_time()` - Vollständige Funktion

**Datei:** `routes/workflow_api.py` (Zeile 2313-2350)

```python
def _calculate_tour_time(stops: List[Dict]) -> float:
    """Berechnet geschätzte Fahrzeit für eine Tour (in Minuten) - verwendet OSRM wenn verfügbar"""
    if len(stops) <= 1:
        return 0.0
    
    # Versuche OSRM wenn verfügbar
    client = get_osrm_client()
    if client.available:
        try:
            depot_lat = 51.0111988
            depot_lon = 13.7016485
            
            # Erstelle Koordinaten-Liste: Depot + alle Stopps
            coords = [(depot_lat, depot_lon)]
            for stop in stops:
                if stop.get('lat') and stop.get('lon'):
                    coords.append((stop.get('lat'), stop.get('lon')))
            
            if len(coords) >= 2:
                # Hole Route vom Depot über alle Stopps
                route = client.get_route(coords)
                if route and route.get("source") == "osrm":
                    return route.get("duration_min", 0.0)
        except Exception as e:
            logger.warning(f"[TOUR-TIME] OSRM-Berechnung fehlgeschlagen: {e}, verwende Fallback")
    
    # Fallback: Haversine
    # ...
```

### 5. Backend: `optimize_tour_stops()` - Funktion

**Datei:** `routes/workflow_api.py` (Zeile 900-960)

```python
def optimize_tour_stops(stops, use_llm: bool = True):
    """Optimiert die Reihenfolge der Stops in einer Tour"""
    if not stops or len(stops) <= 1:
        return stops
    
    # Filtere Stops mit Koordinaten
    valid_stops = [stop for stop in stops if stop.get('lat') and stop.get('lon')]
    if len(valid_stops) <= 1:
        return stops
    
    # LLM-Optimierung falls verfügbar
    if use_llm and llm_optimizer.enabled:
        try:
            result = llm_optimizer.optimize_route(valid_stops, region="Dresden")
            if result.confidence_score > 0.7:
                return [valid_stops[i] for i in result.optimized_route]
        except Exception as e:
            print(f"LLM optimization failed, using fallback: {e}")
    
    # Fallback: Nearest-Neighbor Optimierung
    # ...
```

### 6. Backend: `AIOptimizer.optimize_route()` - Methode

**Datei:** `backend/services/ai_optimizer.py` (Zeile 46-76)

```python
async def optimize_route(
    self,
    stops: List[Stop],
    depot_lat: float,
    depot_lon: float,
    rules: OptimizationRules = None,
) -> RulesOptimizationResult:
    """Optimiert eine Route mit KI basierend auf definierten Regeln"""
    if rules is None:
        rules = default_rules
    
    # Konvertiere Stopps für Prompt
    stops_data = [
        {"name": s.name, "address": s.address, "lat": s.lat, "lon": s.lon}
        for s in stops
    ]
    
    # Regelbasierter Prompt erstellen
    prompt = create_optimization_prompt(rules, stops_data, current_sequence)
    
    if self.use_local:
        response = await self._call_ollama(prompt, require_json=True)
    else:
        response = await self._call_cloud_api(prompt)
    
    return self._parse_ai_response(response, stops, rules)
```

### 7. OSRM Client: `check_health()` - Methode

**Datei:** `services/osrm_client.py` (Zeile 100-150)

```python
def check_health(self) -> Dict[str, Any]:
    """Prüft ob OSRM-Server erreichbar ist"""
    try:
        # Test-Request
        url = f"{self.base_url}/nearest/v1/driving/13.7373,51.0504?number=1"
        with httpx.Client(timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)) as client:
            r = client.get(url)
            if 200 <= r.status_code < 300:
                return {"status": "ok", "url": self.base_url}
            else:
                return {"status": "error", "url": self.base_url, "message": f"HTTP {r.status_code}"}
    except Exception as ex:
        # Fallback prüfen
        if self.fallback_enabled:
            try:
                fallback_url = f"{self.fallback_url}/nearest/v1/driving/13.7373,51.0504?number=1"
                with httpx.Client(timeout=httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)) as client:
                    r = client.get(fallback_url)
                    if 200 <= r.status_code < 300:
                        return {"status": "ok", "url": self.fallback_url, "mode": "fallback"}
            except:
                pass
        return {"status": "error", "url": self.base_url, "message": str(ex)}
```

---

## Erwartetes Verhalten

1. **Request kommt an:** `POST /api/tour/optimize` mit Tour-Daten
2. **OSRM-Check:** Health-Check sollte "ok" zurückgeben
3. **Optimierung:** LLM oder Nearest-Neighbor sollte `optimized_indices` generieren
4. **Stopps-Liste:** `optimized_stops` sollte erstellt werden
5. **Zeitberechnung:** `estimated_driving_time` sollte berechnet werden
6. **Zeit-Constraint:** Wenn > 65 Min, sollte `enforce_timebox()` aufgerufen werden
7. **Response:** JSON-Response sollte zurückgegeben werden

---

## Aktuelles Verhalten

1. **Request kommt an:** ✅
2. **OSRM-Check:** ❓ (unbekannt, sollte im Server-Log stehen)
3. **Optimierung:** ❌ (500-Fehler)
4. **Stopps-Liste:** ❌ (wird nicht erreicht)
5. **Zeitberechnung:** ❌ (wird nicht erreicht)
6. **Zeit-Constraint:** ❌ (wird nicht erreicht)
7. **Response:** ❌ (500-Fehler)

---

## Fragen für Audit

1. **Wo genau tritt der Fehler auf?**
   - Beim JSON-Parsing?
   - Beim OSRM-Check?
   - Bei der LLM-Optimierung?
   - Beim Nearest-Neighbor?
   - Bei der Zeitberechnung?
   - Bei `enforce_timebox()`?

2. **Ist `optimized_indices` definiert?**
   - Wenn nein, warum nicht?
   - Fehlt die Initialisierung?
   - Wird Exception zu früh geworfen?

3. **Ist OSRM verfügbar?**
   - Health-Check gibt "ok" zurück?
   - Aber `get_route()` schlägt trotzdem fehl?

4. **Ist LLM verfügbar?**
   - `llm_optimizer.enabled` ist True?
   - API-Key ist gesetzt?
   - Aber `optimize_route()` schlägt fehl?

5. **Gibt es einen Race-Condition?**
   - Mehrere Requests gleichzeitig?
   - Shared State-Probleme?

---

## Empfehlungen

1. **Sofort:** Server-Logs prüfen für vollständigen Traceback
2. **Kurzfristig:** Debug-Logging hinzufügen
3. **Mittelfristig:** Minimal-Test erstellen
4. **Langfristig:** Besseres Error-Handling und Fallbacks

---

## Dateien für Audit

1. `routes/workflow_api.py` - Haupt-Endpoint
2. `frontend/index.html` - Frontend-Request
3. `services/osrm_client.py` - OSRM-Client
4. `backend/services/ai_optimizer.py` - LLM-Optimizer
5. `routes/health_check.py` - Health-Checks
6. `backend/services/optimization_rules.py` - Optimierungs-Regeln

---

**Ende des Audit-Dokuments**

