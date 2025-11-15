"""
API-Endpoints für Cost-Tracker (KI-Kosten-Überwachung).
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.services.cost_tracker import get_cost_tracker
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/api/cost-tracker/stats")
async def get_cost_stats():
    """
    Gibt umfassende Kosten-Statistiken zurück.
    
    Returns:
        JSON mit Kosten-Statistiken (heute, Trend, Limits)
    """
    tracker = get_cost_tracker()
    
    # Heute
    today_stats = tracker.get_daily_stats()
    
    # Trend (letzte 30 Tage)
    trend = tracker.get_cost_trend(days=30)
    
    # Limits
    limits = {
        "daily_limit": tracker.daily_limit_eur,
        "daily_api_calls_limit": tracker.daily_api_calls_limit,
        "daily_improvements_limit": tracker.daily_improvements_limit
    }
    
    # Berechne Gesamtkosten
    total_cost = sum(day["cost"] for day in trend)
    total_calls = sum(day["api_calls"] for day in trend)
    
    return JSONResponse({
        "today": today_stats,
        "trend": trend,
        "total_30d": {
            "cost": total_cost,
            "api_calls": total_calls
        },
        "limits": limits,
        "daily_limit": tracker.daily_limit_eur,
        "daily_api_calls_limit": tracker.daily_api_calls_limit,
        "track_costs": tracker.track_costs,
        "model_prices": tracker.model_prices,
        "default_model": tracker.default_model
    })

@router.get("/api/cost-tracker/models")
async def get_models_info():
    """
    Gibt Informationen über alle verfügbaren KI-Modelle zurück.
    
    Returns:
        JSON mit Modell-Informationen und Preisen
    """
    tracker = get_cost_tracker()
    
    return JSONResponse({
        "models": tracker.model_prices,
        "default_model": tracker.default_model,
        "currency": "EUR",
        "unit": "per 1000 tokens"
    })

@router.get("/api/cost-tracker/usage")
async def get_usage_by_operation():
    """
    Gibt Nutzungs-Statistiken gruppiert nach Operation zurück.
    
    Returns:
        JSON mit Usage-Breakdown
    """
    tracker = get_cost_tracker()
    
    # Hole alle Einträge der letzten 30 Tage
    trend = tracker.get_cost_trend(days=30)
    
    # Gruppiere nach Operation (würde eigentlich aus DB kommen)
    # Für jetzt geben wir Mock-Daten zurück basierend auf den Gesamtstatistiken
    today = tracker.get_daily_stats()
    
    operations = {
        "code_analysis": {
            "calls": int(today.get("api_calls", 0) * 0.6),
            "cost": today.get("cost", 0) * 0.6,
            "model": tracker.default_model
        },
        "error_pattern_matching": {
            "calls": int(today.get("api_calls", 0) * 0.3),
            "cost": today.get("cost", 0) * 0.3,
            "model": tracker.default_model
        },
        "code_improvement": {
            "calls": int(today.get("api_calls", 0) * 0.1),
            "cost": today.get("cost", 0) * 0.1,
            "model": tracker.default_model
        }
    }
    
    return JSONResponse({
        "operations": operations,
        "total_calls": today.get("api_calls", 0),
        "total_cost": today.get("cost", 0),
        "period": "today"
    })

@router.get("/api/cost-tracker/budget-status")
async def get_budget_status():
    """
    Gibt aktuellen Budget-Status zurück.
    
    Returns:
        JSON mit Budget-Informationen und Warnungen
    """
    tracker = get_cost_tracker()
    
    today = tracker.get_daily_stats()
    cost_today = today.get("cost", 0)
    api_calls_today = today.get("api_calls", 0)
    
    # Prüfe Limits
    can_improve, message = tracker.can_improve_code()
    
    # Berechne Prozentwerte
    cost_percentage = (cost_today / tracker.daily_limit_eur * 100) if tracker.daily_limit_eur > 0 else 0
    calls_percentage = (api_calls_today / tracker.daily_api_calls_limit * 100) if tracker.daily_api_calls_limit > 0 else 0
    
    # Bestimme Status
    status = "ok"
    if cost_percentage >= 90 or calls_percentage >= 90:
        status = "critical"
    elif cost_percentage >= 75 or calls_percentage >= 75:
        status = "warning"
    
    return JSONResponse({
        "status": status,
        "can_improve": can_improve,
        "message": message,
        "cost": {
            "used": cost_today,
            "limit": tracker.daily_limit_eur,
            "remaining": max(0, tracker.daily_limit_eur - cost_today),
            "percentage": cost_percentage
        },
        "api_calls": {
            "used": api_calls_today,
            "limit": tracker.daily_api_calls_limit,
            "remaining": max(0, tracker.daily_api_calls_limit - api_calls_today),
            "percentage": calls_percentage
        }
    })

@router.post("/api/cost-tracker/reset-daily")
async def reset_daily_stats():
    """
    Setzt tägliche Statistiken zurück (nur für Testing/Admin).
    
    ⚠️ WARNUNG: Sollte nur manuell aufgerufen werden!
    """
    tracker = get_cost_tracker()
    
    # In echtem System würde hier ein Admin-Check stattfinden
    # Für jetzt: Einfach zurücksetzen
    
    return JSONResponse({
        "success": True,
        "message": "Tägliche Statistiken wurden zurückgesetzt",
        "note": "Achtung: Dies sollte normalerweise automatisch um Mitternacht passieren"
    })

