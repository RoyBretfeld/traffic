"""
API-Endpoints für KI-Code-Verbesserungen und Benachrichtigungen.
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List
import json
import asyncio
from backend.services.notification_service import get_notification_service

router = APIRouter()

# WebSocket-Verbindungen (für Live-Updates)
websocket_connections: List[WebSocket] = []

@router.get("/api/ki-improvements/recent")
async def get_recent_improvements(limit: int = Query(10, ge=1, le=100)):
    """Gibt letzte Verbesserungen zurück."""
    service = get_notification_service()
    improvements = service.get_recent_improvements(limit=limit)
    return JSONResponse(improvements)

@router.get("/api/ki-improvements/stats")
async def get_improvement_stats():
    """Gibt Statistiken zurück."""
    service = get_notification_service()
    stats = service.get_improvement_stats()
    return JSONResponse(stats)

@router.get("/api/ki-improvements/costs")
async def get_costs(period: str = Query("today", regex="^(today|week|month)$")):
    """Gibt Kosten-Übersicht zurück."""
    from backend.services.cost_tracker import get_cost_tracker
    
    tracker = get_cost_tracker()
    
    if period == "today":
        stats = tracker.get_daily_stats()
        trend = tracker.get_cost_trend(days=7)
        cost_per_file = tracker.get_cost_per_file(days=7)
        
        return JSONResponse({
            "period": "today",
            "stats": stats,
            "trend": trend,
            "cost_per_file": cost_per_file
        })
    elif period == "week":
        trend = tracker.get_cost_trend(days=7)
        cost_per_file = tracker.get_cost_per_file(days=7)
        
        return JSONResponse({
            "period": "week",
            "trend": trend,
            "cost_per_file": cost_per_file
        })
    else:  # month
        trend = tracker.get_cost_trend(days=30)
        cost_per_file = tracker.get_cost_per_file(days=30)
        
        return JSONResponse({
            "period": "month",
            "trend": trend,
            "cost_per_file": cost_per_file
        })

@router.get("/api/ki-improvements/performance")
async def get_performance(period: str = Query("today", regex="^(today|week|month)$")):
    """Gibt Performance-Übersicht zurück."""
    from backend.services.performance_tracker import get_performance_tracker
    
    tracker = get_performance_tracker()
    
    if period == "today":
        averages = tracker.get_daily_averages()
        slowest_files = tracker.get_slowest_files(days=7, limit=10)
        trend = tracker.get_performance_trend(days=7)
        
        return JSONResponse({
            "period": "today",
            "averages": averages,
            "slowest_files": slowest_files,
            "trend": trend
        })
    elif period == "week":
        slowest_files = tracker.get_slowest_files(days=7, limit=10)
        trend = tracker.get_performance_trend(days=7)
        
        return JSONResponse({
            "period": "week",
            "slowest_files": slowest_files,
            "trend": trend
        })
    else:  # month
        slowest_files = tracker.get_slowest_files(days=30, limit=10)
        trend = tracker.get_performance_trend(days=30)
        
        return JSONResponse({
            "period": "month",
            "slowest_files": slowest_files,
            "trend": trend
        })

@router.get("/api/ki-improvements/limits")
async def get_limits():
    """Gibt aktuelle Limits und Status zurück."""
    from backend.services.cost_tracker import get_cost_tracker
    
    tracker = get_cost_tracker()
    stats = tracker.get_daily_stats()
    can_improve, message = tracker.can_improve_code()
    
    return JSONResponse({
        "can_improve": can_improve,
        "message": message,
        "limits": {
            "daily_cost_limit_eur": tracker.daily_limit_eur,
            "daily_api_calls_limit": tracker.daily_api_calls_limit,
            "daily_improvements_limit": tracker.daily_improvements_limit
        },
        "current": {
            "daily_cost_eur": stats["total_cost_eur"],
            "daily_api_calls": stats["total_api_calls"],
            "daily_improvements": stats["total_improvements"]
        },
        "remaining": {
            "cost_eur": max(0, tracker.daily_limit_eur - stats["total_cost_eur"]),
            "api_calls": max(0, tracker.daily_api_calls_limit - stats["total_api_calls"]),
            "improvements": max(0, tracker.daily_improvements_limit - stats["total_improvements"])
        }
    })

@router.websocket("/ws/ki-improvements")
async def websocket_improvements(websocket: WebSocket):
    """WebSocket für Live-Updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Sende initiale Daten
        service = get_notification_service()
        stats = service.get_improvement_stats()
        await websocket.send_json({"type": "stats", "data": stats})
        
        # Halte Verbindung offen und sende Updates
        while True:
            # Prüfe auf neue Verbesserungen (alle 5 Sekunden)
            await asyncio.sleep(5)
            
            # Sende Heartbeat
            await websocket.send_json({"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        print(f"[WEBSOCKET] Fehler: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

async def broadcast_improvement(improvement_result: dict):
    """Sendet Verbesserung an alle WebSocket-Clients."""
    message = {
        "type": "improvement",
        "data": improvement_result
    }
    
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception as e:
            print(f"[WEBSOCKET] Fehler beim Senden: {e}")
            disconnected.append(ws)
    
    # Entferne getrennte Verbindungen
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)

# Export für NotificationService
async def broadcast_improvement_to_websockets(improvement_result: dict):
    """Sendet Verbesserung an alle WebSocket-Clients (wird von NotificationService aufgerufen)."""
    await broadcast_improvement(improvement_result)

async def broadcast_activity_to_websockets(message: str, level: str = "info"):
    """Sendet Activity-Update an alle WebSocket-Clients."""
    activity_message = {
        "type": "activity",
        "message": message,
        "level": level,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(activity_message)
        except Exception as e:
            print(f"[WEBSOCKET] Fehler beim Senden von Activity: {e}")
            disconnected.append(ws)
    
    # Entferne getrennte Verbindungen
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)

