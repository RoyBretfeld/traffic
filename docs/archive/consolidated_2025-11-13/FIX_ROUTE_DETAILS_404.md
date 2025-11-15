# TrafficApp: Route-Details 404 – Fix & Test-Plan (für Cursor)

Diese Anleitung ist so strukturiert, dass du sie 1:1 im **Cursor**-Editor nutzen kannst: klare Schritte, Copy‑Paste‑Snippets, minimale Patches und Tests (HTTP/PowerShell/curl).

---

## 1) Problemzusammenfassung (kurz & präzise)

**Hauptproblem**

* `POST /api/tour/route-details` liefert **404**.
* Router wird laut Logs registriert, Endpoint ist aber nicht erreichbar.
* Vermutung: **Auto‑Reload / Import‑Reihenfolge / Prefix** sorgt dafür, dass der Pfad nicht im finalen App‑Objekt landet.

**Sekundärproblem**

* OSRM liefert Geometrie (Polyline) korrekt, Frontend bekommt diese aber **nicht**, weil 404 ⇒ Fallback auf **Haversine‑Geraden**.

**Ziel**

* Endpoint stabil verfügbar machen (200), OSRM‑Polyline (`polyline6`) ans Frontend geben, Frontend dekodiert wieder **Straßengeometrien**.

---

## 2) Quick‑Checklist (DoD)

* [ ] Server „kalt" neu gestartet (keine Zombie‑Reloader)
* [ ] `openapi.json` listet **/api/tour/route-details**
* [ ] `POST /api/tour/route-details` liefert 200 + `geometry` (polyline6)
* [ ] Frontend zeigt reale Routen (keine Geraden)
* [ ] Keine SQLite‑Fehler („database disk image is malformed")
* [ ] Geocoding läuft ohne Stau (ggf. Parallelität limitiert)

---

## 3) Clean Restart (ohne Auto‑Reload)

### PowerShell (Windows)

```powershell
# 1) Prozesse hart beenden
Get-Process python, uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force

# 2) Port freigeben prüfen
netstat -ano | findstr :8111

# 3) Py-Caches löschen
Get-ChildItem -Recurse -Force -Include __pycache__,*.pyc | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 4) Server ohne Reload starten (Variante A: dein Wrapper)
python start_server.py --no-reload

# (Variante B: direkt uvicorn, wenn zutreffend)
# uvicorn app:app --host 127.0.0.1 --port 8111 --log-level info
```

### Bash (optional)

```bash
pkill -f "uvicorn|python .*start_server.py" || true
lsof -i :8111 || true
find . -name __pycache__ -o -name "*.pyc" -print0 | xargs -0 rm -rf
python start_server.py --no-reload
```

> **Hinweis:** Für die Fehlersuche **Auto‑Reload aus** lassen.

---

## 4) Endpoint validieren (OpenAPI + Smoke‑Tests)

### 4.1 OpenAPI prüfen

* Browser: `http://127.0.0.1:8111/docs`
* `http://127.0.0.1:8111/openapi.json` muss **/api/tour/route-details** enthalten.

### 4.2 REST‑Client (.http) – in Cursor nutzen

```http
### OpenAPI
GET http://127.0.0.1:8111/openapi.json

### Gesund?
GET http://127.0.0.1:8111/health/db

### Route-Details (Minimalbeispiel mit 2 Stops)
POST http://127.0.0.1:8111/api/tour/route-details
Content-Type: application/json

{
  "tour_name": "W-07.00 Uhr Tour",
  "profile": "driving",
  "overview": "full",
  "include_depot": true,
  "stops": [
    { "id": "A", "lat": 51.0902263, "lon": 13.7049531 },
    { "id": "B", "lat": 51.0608641, "lon": 13.6872374 }
  ]
}
```

### 4.3 curl‑Variante (Bash/PowerShell)

```bash
curl -s http://127.0.0.1:8111/openapi.json | jq '.paths | keys'

curl -s -X POST http://127.0.0.1:8111/api/tour/route-details \
  -H "Content-Type: application/json" \
  -d '{
    "tour_name": "W-07.00 Uhr Tour",
    "profile": "driving",
    "overview": "full",
    "include_depot": true,
    "stops": [
      { "id": "A", "lat": 51.0902263, "lon": 13.7049531 },
      { "id": "B", "lat": 51.0608641, "lon": 13.6872374 }
    ]
  }' | jq '{distance_m:.distance_m, duration_s:.duration_s, geometry:(.geometry|type)}'
```

> **Erwartung:** `geometry` ist ein **String** (encoded `polyline6`), `distance_m`/`duration_s` sind Zahlen.

---

## 5) Wenn trotzdem 404: typische Ursachen & Fixes

1. **Router nicht inkludiert**

   ```python
   # app.py
   from fastapi import FastAPI
   from workflow_api import router as workflow_router

   app = FastAPI()
   app.include_router(workflow_router, prefix="/api")
   ```

2. **Falscher Routen‑Dekorator oder Präfix**

   * In `workflow_api.py` muss der Dekorator **ohne** `/api` lauten:

     ```python
     @router.post("/tour/route-details")
     ```
   * Das **Prefix** kommt nur in `app.include_router(..., prefix="/api")`.

3. **HTTP‑Methode**

   * Frontend nutzt **POST** ⇒ Backend muss `@router.post(...)` nutzen.
   * 404 ≠ 405: Bei 404 liegt es i. d. R. an Import/Prefix, nicht an der Methode.

4. **Reloader‑Ghost**

   * Zwei Prozesse, nur einer mit Route ⇒ **Reload aus**, s. Abschnitt 3.

---

## 6) Minimal‑Patch für den Endpoint (robust & klar)

> Falls du den Endpoint absichern möchtest, hier ein schlanker Referenz‑Handler (nutzt `polyline6`). Passe `get_osrm_client` ggf. an deinen Code an.

```python
# workflow_api.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Stop(BaseModel):
    id: str
    lat: float
    lon: float

class RouteDetailsRequest(BaseModel):
    tour_name: str | None = None
    stops: List[Stop]
    profile: str = "driving"
    overview: str = "full"
    include_depot: bool = True

# Placeholder: an deine Factory/DI anpassen
async def get_osrm_client():
    from services.osrm_client import OSRMClient
    return OSRMClient(base_url="http://router.project-osrm.org")

@router.post("/tour/route-details")
async def route_details(req: RouteDetailsRequest, osrm=Depends(get_osrm_client)):
    if not req.stops or len(req.stops) < 2:
        raise HTTPException(status_code=400, detail="mind. 2 Stops nötig")

    coords = ";".join(f"{s.lon},{s.lat}" for s in req.stops)

    # geometries=polyline6 ⇒ kompaktes Encoding, Frontend dekodiert es bereits
    res = await osrm.get_route(coords, overview=req.overview, geometries="polyline6")
    if not res or not res.get("routes"):
        raise HTTPException(status_code=502, detail="OSRM lieferte keine Route")

    route = res["routes"][0]
    return {
        "distance_m": route.get("distance"),
        "duration_s": route.get("duration"),
        "geometry": route.get("geometry"),  # encoded polyline6
        "waypoints": res.get("waypoints", []),
        "profile": req.profile,
        "overview": req.overview,
    }
```

---

## 7) OSRM‑Geometrie separat validieren

```powershell
Invoke-RestMethod -Uri "http://router.project-osrm.org/route/v1/driving/13.7049531,51.0902263;13.6872374,51.0608641?overview=full&geometries=polyline6" | ConvertTo-Json -Depth 10
```

```bash
curl -s "http://router.project-osrm.org/route/v1/driving/13.7049531,51.0902263;13.6872374,51.0608641?overview=full&geometries=polyline6" \
 | jq '.routes[0] | {distance, duration, geometry_type:(.geometry|type)}'
```

> **Erwartung:** `.routes[0].geometry` ist ein **String** (encoded polyline6).

---

## 8) Performance‑Fixes ("es geht weiter, aber langsam")

### 8.1 SQLite: "database disk image is malformed"

Das erzeugt massiven Overhead bei jeder Insert‑Operation (z. B. `manual_queue`).

**Sanierung (Variante A: Dump & Rebuild)**

```powershell
# Server stoppen
Get-Process python, uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force

# DB lokalisieren (Name/Pfad ggf. anpassen)
# Beispiel: .\data\manual_queue.db

# Dump & Rebuild (wenn sqlite3 verfügbar ist)
sqlite3 .\data\manual_queue.db ".mode insert" ".output dump.sql" ".dump" ".quit"
Move-Item .\data\manual_queue.db .\data\manual_queue.db.bak
sqlite3 .\data\manual_queue.db ".read dump.sql"
```

**Sanierung (Variante B: Neu anlegen)**

```powershell
Move-Item .\data\manual_queue.db .\data\manual_queue.db.bak
# Beim nächsten Start legt dein Schema-Init die Tabellen neu an.
```

### 8.2 Geocoding‑Parallelität drosseln

* Temporär per Env/Config reduzieren, z. B. `GEOCODE_MAX_PARALLEL=5`.
* Bis die DB wieder stabil ist.

### 8.3 Upload‑Encoding stabilisieren

* Tourpläne **immer** über den vorgesehenen Upload/Workflow‑Endpoint schicken, damit der Guard korrekt `cp850` vs `utf-8` erkennt.

---

## 9) Frontend‑Seite: Polyline‑Dekodierung

* Frontend dekodiert `polyline6` bereits.
* Sobald `/api/tour/route-details` stabil 200 liefert, fallen Haversine‑Geraden automatisch weg.

**Schnelltest**

* Network‑Tab prüfen: Request/Response auf `/api/tour/route-details`.
* Response enthält `geometry` (string, mehrere hundert Zeichen).

---

## 10) Troubleshooting‑Matrix

| Symptom                           | Prüfung                          | Fix                                                                |
| --------------------------------- | -------------------------------- | ------------------------------------------------------------------ |
| 404 auf `/api/tour/route-details` | `openapi.json` ⇒ Pfad vorhanden? | Router‑Import + `include_router(..., prefix="/api")`, Reload aus   |
| 405 (Method Not Allowed)          | Methode passt?                   | `@router.post(...)` sicherstellen                                  |
| 200 aber `geometry` fehlt         | OSRM‑Antwort inspizieren         | `geometries=polyline6`, `overview=full` setzen, erste Route prüfen |
| Frontend weiterhin Linien         | Network‑Response checken         | Response hat `geometry`? Frontend‑Decoder aktiviert? Cache leeren  |
| Geocoding sehr langsam            | Logs, DB‑Fehler                  | SQLite sanieren, Parallelität drosseln                             |

---

## 11) Copy‑Paste Snippets (für Cursor)

### 11.1 `route_details_test.http`

```http
### OpenAPI
GET http://127.0.0.1:8111/openapi.json

### Health
GET http://127.0.0.1:8111/health/db

### Route-Details Test
POST http://127.0.0.1:8111/api/tour/route-details
Content-Type: application/json

{
  "tour_name": "W-07.00 Uhr Tour",
  "profile": "driving",
  "overview": "full",
  "include_depot": true,
  "stops": [
    { "id": "A", "lat": 51.0902263, "lon": 13.7049531 },
    { "id": "B", "lat": 51.0608641, "lon": 13.6872374 }
  ]
}
```

### 11.2 `route_details_payload.json`

```json
{
  "tour_name": "W-07.00 Uhr Tour",
  "profile": "driving",
  "overview": "full",
  "include_depot": true,
  "stops": [
    { "id": "A", "lat": 51.0902263, "lon": 13.7049531 },
    { "id": "B", "lat": 51.0608641, "lon": 13.6872374 }
  ]
}
```

### 11.3 `powershell_tests.ps1`

```powershell
# OpenAPI
Invoke-RestMethod -Uri http://127.0.0.1:8111/openapi.json | ConvertTo-Json -Depth 5

# Route-Details
$payload = Get-Content -Raw -Path .\route_details_payload.json
Invoke-RestMethod -Uri http://127.0.0.1:8111/api/tour/route-details -Method Post -ContentType 'application/json' -Body $payload | ConvertTo-Json -Depth 10
```

---

## 12) Nächste Schritte (empfohlene Reihenfolge)

1. **Clean Restart** (Abschnitt 3)
2. **OpenAPI prüfen** (4.1) ⇒ Pfad muss existieren
3. **Smoke‑Test POST** (4.2/4.3) ⇒ 200 + `geometry`
4. **Falls 404** ⇒ Abschnitt 5/6 Patches anwenden
5. **OSRM direkt validieren** (7)
6. **Performance‑Sanierung** (8) bis Logs „grün" sind
7. **Frontend reloaden** ⇒ echte Routengeometrien sichtbar

---

## 13) Hinweise zur ZIP‑Akte (OSRM_POLYGONE_PROBLEM_…)

* Lege relevante Skripte/Configs aus der ZIP direkt neben diese Datei ins Repo/Workspace und nutze die Snippets oben für reproduzierbare Tests.
* Falls die ZIP Beispiel‑Payloads enthält, kannst du sie mit den `.http`/`ps1`‑Skripten kombinieren.

---

**Fertig.** Mit dieser Checkliste + Snippets solltest du den 404 isolieren, den Endpoint stabil registrieren und die OSRM‑Polyline wieder im Frontend sehen. Viel Erfolg! 💪

