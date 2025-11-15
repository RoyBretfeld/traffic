"""
API-Endpunkte für Live-Traffic-Daten
Ermöglicht Abfrage und Verwaltung von Baustellen, Unfällen und Sperrungen
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from backend.services.live_traffic_data import get_live_traffic_service, TrafficIncident, SpeedCamera
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.get("/incidents")
async def get_incidents(
    min_lat: float = Query(..., description="Minimale Breitengrad"),
    min_lon: float = Query(..., description="Minimale Längengrad"),
    max_lat: float = Query(..., description="Maximale Breitengrad"),
    max_lon: float = Query(..., description="Maximale Längengrad"),
    types: Optional[str] = Query(None, description="Komma-getrennte Liste: construction,accident,closure")
):
    """
    Holt Verkehrshindernisse in einem bestimmten Gebiet.
    
    Args:
        min_lat, min_lon, max_lat, max_lon: Gebietsgrenzen
        types: Optional: Filter nach Typen (construction,accident,closure)
    """
    try:
        traffic_service = get_live_traffic_service()
        bounds = (min_lat, min_lon, max_lat, max_lon)
        
        incident_types = None
        if types:
            incident_types = [t.strip() for t in types.split(",")]
        
        incidents = traffic_service.get_incidents_in_area(bounds, incident_types)
        
        # Konvertiere zu JSON-serialisierbarem Format
        result = []
        for inc in incidents:
            result.append({
                "incident_id": inc.incident_id,
                "type": inc.type,
                "lat": inc.lat,
                "lon": inc.lon,
                "severity": inc.severity,
                "description": inc.description,
                "delay_minutes": inc.delay_minutes,
                "radius_km": inc.radius_km,
                "affected_roads": inc.affected_roads or []
            })
        
        return JSONResponse({"incidents": result, "count": len(result)})
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Abrufen von Verkehrshindernissen: {str(e)}")


@router.post("/incidents")
async def create_incident(incident: dict):
    """
    Erstellt ein neues Verkehrshindernis in der Datenbank.
    
    Body:
        {
            "incident_id": "unique_id",
            "type": "construction|accident|closure",
            "lat": 51.05,
            "lon": 13.73,
            "severity": "low|medium|high|critical",
            "description": "Beschreibung",
            "delay_minutes": 5,
            "radius_km": 2.0,
            "start_time": "2025-01-10T08:00:00",
            "end_time": "2025-01-10T18:00:00"
        }
    """
    try:
        with ENGINE.begin() as conn:
            # Erstelle Tabelle falls nicht vorhanden
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS traffic_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    delay_minutes INTEGER DEFAULT 0,
                    radius_km REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """))
            
            # Füge Incident hinzu
            conn.execute(text("""
                INSERT OR REPLACE INTO traffic_incidents 
                (incident_id, type, lat, lon, severity, description, 
                 start_time, end_time, delay_minutes, radius_km, updated_at)
                VALUES (:incident_id, :type, :lat, :lon, :severity, :description,
                        :start_time, :end_time, :delay_minutes, :radius_km, datetime('now'))
            """), {
                "incident_id": incident.get("incident_id"),
                "type": incident.get("type"),
                "lat": incident.get("lat"),
                "lon": incident.get("lon"),
                "severity": incident.get("severity", "medium"),
                "description": incident.get("description", ""),
                "start_time": incident.get("start_time"),
                "end_time": incident.get("end_time"),
                "delay_minutes": incident.get("delay_minutes", 0),
                "radius_km": incident.get("radius_km", 0.5)
            })
        
        return JSONResponse({"success": True, "message": "Incident erstellt"})
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Erstellen des Incidents: {str(e)}")


@router.delete("/incidents/{incident_id}")
async def delete_incident(incident_id: str):
    """Löscht ein Verkehrshindernis aus der Datenbank."""
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(text("""
                DELETE FROM traffic_incidents WHERE incident_id = :incident_id
            """), {"incident_id": incident_id})
            
            if result.rowcount == 0:
                raise HTTPException(404, detail=f"Incident nicht gefunden: {incident_id}")
        
        return JSONResponse({"success": True, "message": f"Incident {incident_id} gelöscht"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Löschen des Incidents: {str(e)}")


@router.get("/cameras")
async def get_cameras(
    min_lat: float = Query(..., description="Minimale Breitengrad"),
    min_lon: float = Query(..., description="Minimale Längengrad"),
    max_lat: float = Query(..., description="Maximale Breitengrad"),
    max_lon: float = Query(..., description="Maximale Längengrad"),
    types: Optional[str] = Query(None, description="Komma-getrennte Liste: fixed,mobile,section_control")
):
    """
    Holt Blitzer/Radar-Standorte in einem bestimmten Gebiet.
    
    WICHTIGER RECHTLICHER HINWEIS:
    Blitzer.de bietet keine öffentliche API. Diese Endpoint verwendet Daten aus
    der eigenen Datenbank, die manuell eingetragen oder importiert werden müssen.
    
    Bitte prüfen Sie die Nutzungsbedingungen von Blitzer.de und anderen Datenquellen
    vor der kommerziellen Nutzung.
    
    Args:
        min_lat, min_lon, max_lat, max_lon: Gebietsgrenzen
        types: Optional: Filter nach Typen (fixed,mobile,section_control)
    """
    try:
        traffic_service = get_live_traffic_service()
        bounds = (min_lat, min_lon, max_lat, max_lon)
        
        camera_types = None
        if types:
            camera_types = [t.strip() for t in types.split(",")]
        
        cameras = traffic_service.get_speed_cameras_in_area(bounds, camera_types)
        
        # Konvertiere zu JSON-serialisierbarem Format
        result = []
        for cam in cameras:
            result.append({
                "camera_id": cam.camera_id,
                "type": cam.type,
                "lat": cam.lat,
                "lon": cam.lon,
                "direction": cam.direction,
                "speed_limit": cam.speed_limit,
                "description": cam.description,
                "verified": cam.verified
            })
        
        return JSONResponse({
            "cameras": result,
            "count": len(result),
            "legal_notice": "Daten aus eigener Datenbank. Bitte prüfen Sie rechtliche Aspekte bei Nutzung externer Datenquellen."
        })
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Abrufen von Blitzer-Daten: {str(e)}")


@router.post("/cameras")
async def create_camera(camera: dict):
    """
    Erstellt einen neuen Blitzer-Eintrag in der Datenbank.
    
    WICHTIGER RECHTLICHER HINWEIS:
    Bitte stellen Sie sicher, dass Sie berechtigt sind, diese Daten zu speichern
    und zu nutzen. Prüfen Sie die Nutzungsbedingungen der Datenquelle.
    
    Body:
        {
            "camera_id": "unique_id",
            "type": "fixed|mobile|section_control",
            "lat": 51.05,
            "lon": 13.73,
            "direction": "north|south|east|west|both",
            "speed_limit": 50,
            "description": "Beschreibung",
            "verified": true
        }
    """
    try:
        with ENGINE.begin() as conn:
            # Erstelle Tabelle falls nicht vorhanden
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS speed_cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT UNIQUE NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    type TEXT NOT NULL,
                    direction TEXT,
                    speed_limit INTEGER,
                    description TEXT,
                    verified INTEGER DEFAULT 0,
                    last_seen TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """))
            
            # Füge Camera hinzu
            conn.execute(text("""
                INSERT OR REPLACE INTO speed_cameras 
                (camera_id, type, lat, lon, direction, speed_limit, description, verified, updated_at)
                VALUES (:camera_id, :type, :lat, :lon, :direction, :speed_limit, :description, :verified, datetime('now'))
            """), {
                "camera_id": camera.get("camera_id"),
                "type": camera.get("type"),
                "lat": camera.get("lat"),
                "lon": camera.get("lon"),
                "direction": camera.get("direction"),
                "speed_limit": camera.get("speed_limit"),
                "description": camera.get("description", ""),
                "verified": 1 if camera.get("verified", False) else 0
            })
        
        return JSONResponse({
            "success": True,
            "message": "Blitzer-Eintrag erstellt",
            "legal_notice": "Bitte prüfen Sie rechtliche Aspekte bei Nutzung externer Datenquellen."
        })
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Erstellen des Blitzer-Eintrags: {str(e)}")


@router.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Löscht einen Blitzer-Eintrag aus der Datenbank."""
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(text("""
                DELETE FROM speed_cameras WHERE camera_id = :camera_id
            """), {"camera_id": camera_id})
            
            if result.rowcount == 0:
                raise HTTPException(404, detail=f"Blitzer-Eintrag nicht gefunden: {camera_id}")
        
        return JSONResponse({"success": True, "message": f"Blitzer-Eintrag {camera_id} gelöscht"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Löschen des Blitzer-Eintrags: {str(e)}")

