# Sub-Routen Generator - Dateien-Übersicht

## Frontend
- `frontend/index.html` - Haupt-Frontend mit Sub-Routen Generator UI und JavaScript-Funktionen

## Backend API
- `routes/workflow_api.py` - API-Endpunkte für Tour-Optimierung (`/api/tour/optimize`)
- `routes/schemas.py` - Pydantic-Schemas (`OptimizeTourRequest`, `StopModel`)

## Backend Services
- `backend/services/routing_optimizer.py` - Routing-Optimierung (Nearest-Neighbor, Haversine-Matrix)
- `services/llm_optimizer.py` - LLM-basierte Route-Optimierung
- `services/osrm_client_robust.py` - OSRM-Client mit Fallback-Mechanismen

## Tests
- `tests/test_subroutes_500_fix.py` - Tests für Sub-Routen-Fixes

## Dokumentation
- `docs/FEHLER_ZUSAMMENFASSUNG_500_ERROR.md` - Zusammenfassung der 500er-Fehler
- `docs/CHECKLIST_POST_FIX.md` - Checkliste nach Fixes
- `docs/FIXPLAN_500_ERROR_IMPLEMENTIERT.md` - Implementierter Fixplan
- `docs/STATUS_AKTUELL.md` - Aktueller Projekt-Status
- `docs/PROJECT_STATUS.md` - Projekt-Status-Übersicht
- `docs/ROUTENBILDUNG_DOKUMENTATION.md` - Dokumentation zur Routenbildung

## Wichtige Funktionen

### Frontend (index.html)
- `generateSubRoutes()` - Hauptfunktion für Sub-Routen-Generierung
- `splitTourIntoSubRoutes()` - Teilt Tour in Sub-Routen auf
- `updateToursWithSubRoutes()` - Aktualisiert Tour-Liste mit Sub-Routen
- `updateSubRouteButtonVisibility()` - Zeigt/versteckt Sub-Routen-Button

### Backend API (workflow_api.py)
- `POST /api/tour/optimize` - Optimiert Tour-Stopps (wird vom Frontend aufgerufen)
- `optimize_tour_stops()` - Optimiert Stop-Reihenfolge
- `enforce_timebox()` - Erzwingt Zeitbox-Constraints (65 Min ohne Rückfahrt)

### Backend Services
- `routing_optimizer.optimize_route()` - Haupt-Optimierungsfunktion
- `routing_optimizer.nearest_neighbor()` - Nearest-Neighbor-Heuristik
- `routing_optimizer.compute_local_haversine_matrix()` - Haversine-Distanz-Matrix

## API-Aufruf

```javascript
// Frontend ruft auf:
POST /api/tour/optimize
{
  "tour_id": "W-07.00",
  "stops": [
    {
      "name": "Kunde 1",
      "lat": 51.0504,
      "lon": 13.7373,
      "address": "Straße 1, 01067 Dresden"
    },
    ...
  ],
  "is_bar_tour": false,
  "profile": "car"
}
```

## Erstellt
2025-11-16 14:18:52
