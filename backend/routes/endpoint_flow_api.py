"""API für Endpoint Flow Visualisierung"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Dict

router = APIRouter(prefix="/api/endpoint-flow", tags=["endpoint-flow"])

@router.get("/modules")
async def get_modules():
    """Gibt alle Module und ihre Endpoints zurück"""
    
    modules = [
        {
            "name": "Workflow API",
            "description": "Kompletter Workflow: Parse → Geocode → Optimize",
            "endpoints": [
                {"method": "POST", "path": "/api/workflow/upload", "description": "CSV-Upload + Workflow"},
                {"method": "POST", "path": "/api/workflow/complete", "description": "Workflow für Tourplaene-Datei"},
                {"method": "GET", "path": "/api/workflow/status", "description": "System-Status"}
            ],
            "dependencies": ["Workflow Engine", "Cached Geocoder", "LLM Optimizer"]
        },
        {
            "name": "Geocoding Services",
            "description": "Adress-zu-Koordinaten Konvertierung",
            "endpoints": [
                {"method": "GET", "path": "/api/tourplan/match", "description": "Tourplan gegen DB matchen"},
                {"method": "POST", "path": "/api/tourplan/geofill", "description": "Fehlende Koordinaten geokodieren"},
                {"method": "GET", "path": "/api/address-recognition/status", "description": "Erkennungsrate"}
            ],
            "dependencies": ["geo_cache", "Geocoder"]
        },
        {
            "name": "Manual Queue",
            "description": "Manuelle Adress-Korrektur",
            "endpoints": [
                {"method": "GET", "path": "/api/manual/list", "description": "Offene Einträge"},
                {"method": "GET", "path": "/api/manual/stats", "description": "Statistiken"},
                {"method": "POST", "path": "/api/manual/resolve", "description": "Eintrag auflösen"}
            ],
            "dependencies": ["manual_queue"]
        },
        {
            "name": "System Status",
            "description": "Health & Monitoring",
            "endpoints": [
                {"method": "GET", "path": "/health", "description": "Server Health"},
                {"method": "GET", "path": "/health/db", "description": "Datenbank Status"},
                {"method": "GET", "path": "/summary", "description": "Zusammenfassung"},
                {"method": "GET", "path": "/api/tests/status", "description": "Test-Status"}
            ],
            "dependencies": []
        },
        {
            "name": "LLM Services",
            "description": "AI-basierte Optimierung",
            "endpoints": [
                {"method": "POST", "path": "/api/llm/optimize", "description": "Route optimieren"},
                {"method": "GET", "path": "/api/llm/monitoring", "description": "LLM-Monitoring"},
                {"method": "GET", "path": "/api/llm/templates", "description": "Prompt-Templates"}
            ],
            "dependencies": ["OpenAI API", "OSRM"]
        }
    ]
    
    return JSONResponse({"modules": modules})

@router.get("/flow")
async def get_data_flow():
    """Gibt typische Datenflüsse zurück"""
    
    flows = [
        {
            "name": "CSV Upload → Workflow",
            "steps": [
                {"from": "Frontend", "to": "/api/workflow/upload", "action": "CSV hochladen"},
                {"from": "/api/workflow/upload", "to": "Workflow Engine", "action": "CSV parsen"},
                {"from": "Workflow Engine", "to": "Cached Geocoder", "action": "Adressen geokodieren"},
                {"from": "Cached Geocoder", "to": "geo_cache", "action": "Koordinaten abfragen"},
                {"from": "Cached Geocoder", "to": "Nominatim", "action": "Neue Adressen geokodieren"},
                {"from": "Workflow Engine", "to": "LLM Optimizer", "action": "Route optimieren"},
                {"from": "LLM Optimizer", "to": "OSRM", "action": "Distanzen holen"},
                {"from": "LLM Optimizer", "to": "OpenAI API", "action": "Route optimieren"},
                {"from": "Workflow Engine", "to": "Frontend", "action": "Touren zurückgeben"}
            ]
        },
        {
            "name": "Tourplan Matching",
            "steps": [
                {"from": "Frontend", "to": "/api/tourplan/match", "action": "Tourplan auswählen"},
                {"from": "/api/tourplan/match", "to": "geo_cache", "action": "Adressen abgleichen"},
                {"from": "/api/tourplan/match", "to": "Frontend", "action": "Match-Ergebnisse"}
            ]
        },
        {
            "name": "LLM-Routenoptimierung",
            "steps": [
                {"from": "Frontend", "to": "/api/llm/optimize", "action": "Route optimieren"},
                {"from": "/api/llm/optimize", "to": "LLM Optimizer", "action": "OSRM-Distanzen holen"},
                {"from": "LLM Optimizer", "to": "OSRM", "action": "Straßen-Distanzen"},
                {"from": "LLM Optimizer", "to": "OpenAI API", "action": "Route optimieren"},
                {"from": "/api/llm/optimize", "to": "Frontend", "action": "Optimierte Route"}
            ]
        }
    ]
    
    return JSONResponse({"flows": flows})

