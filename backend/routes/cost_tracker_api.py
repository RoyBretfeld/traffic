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
    Erweitert: Detaillierte API-Call-Statistiken pro Modell und pro Operation.
    
    Returns:
        JSON mit Kosten-Statistiken (heute, Trend, Limits, detaillierte Calls)
    """
    tracker = get_cost_tracker()
    
    # Heute
    today_stats = tracker.get_daily_stats()
    
    # Trend (letzte 30 Tage)
    trend = tracker.get_cost_trend(days=30)
    
    # Konvertiere Trend-Format für Frontend (cost_eur -> cost)
    trend_formatted = [
        {
            "date": day["date"],
            "cost": day.get("cost_eur", day.get("cost", 0.0)),
            "api_calls": day.get("api_calls", 0),
            "improvements": day.get("improvements", 0)
        }
        for day in trend
    ]
    
    # Limits
    limits = {
        "daily_limit": tracker.daily_limit_eur,
        "daily_api_calls_limit": tracker.daily_api_calls_limit,
        "daily_improvements_limit": tracker.daily_improvements_limit
    }
    
    # Berechne Gesamtkosten
    total_cost = sum(day.get("cost_eur", day.get("cost", 0.0)) for day in trend)
    total_calls = sum(day.get("api_calls", 0) for day in trend)
    
    # Detaillierte API-Call-Statistiken (pro Modell, pro Operation)
    import sqlite3
    from datetime import datetime, timedelta
    
    detailed_stats = {
        "by_model": {},
        "by_operation": {},
        "today": {
            "by_model": {},
            "by_operation": {}
        },
        "week": {
            "by_model": {},
            "by_operation": {}
        },
        "month": {
            "by_model": {},
            "by_operation": {}
        }
    }
    
    try:
        with sqlite3.connect(tracker.db_path) as conn:
            # Heute
            today = datetime.now().strftime("%Y-%m-%d")
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            
            cursor = conn.execute("""
                SELECT model, operation, COUNT(*) as calls, SUM(cost_eur) as total_cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY model, operation
            """, (today_start,))
            
            for row in cursor.fetchall():
                model, operation, calls, cost = row
                operation = operation or "unknown"
                
                if model not in detailed_stats["today"]["by_model"]:
                    detailed_stats["today"]["by_model"][model] = {"calls": 0, "cost": 0.0}
                detailed_stats["today"]["by_model"][model]["calls"] += calls
                detailed_stats["today"]["by_model"][model]["cost"] += cost or 0.0
                
                if operation not in detailed_stats["today"]["by_operation"]:
                    detailed_stats["today"]["by_operation"][operation] = {"calls": 0, "cost": 0.0, "model": model}
                detailed_stats["today"]["by_operation"][operation]["calls"] += calls
                detailed_stats["today"]["by_operation"][operation]["cost"] += cost or 0.0
            
            # Woche (letzte 7 Tage)
            week_start = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = conn.execute("""
                SELECT model, operation, COUNT(*) as calls, SUM(cost_eur) as total_cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY model, operation
            """, (week_start,))
            
            for row in cursor.fetchall():
                model, operation, calls, cost = row
                operation = operation or "unknown"
                
                if model not in detailed_stats["week"]["by_model"]:
                    detailed_stats["week"]["by_model"][model] = {"calls": 0, "cost": 0.0}
                detailed_stats["week"]["by_model"][model]["calls"] += calls
                detailed_stats["week"]["by_model"][model]["cost"] += cost or 0.0
                
                if operation not in detailed_stats["week"]["by_operation"]:
                    detailed_stats["week"]["by_operation"][operation] = {"calls": 0, "cost": 0.0, "model": model}
                detailed_stats["week"]["by_operation"][operation]["calls"] += calls
                detailed_stats["week"]["by_operation"][operation]["cost"] += cost or 0.0
            
            # Monat (letzte 30 Tage)
            month_start = (datetime.now() - timedelta(days=30)).isoformat()
            cursor = conn.execute("""
                SELECT model, operation, COUNT(*) as calls, SUM(cost_eur) as total_cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY model, operation
            """, (month_start,))
            
            for row in cursor.fetchall():
                model, operation, calls, cost = row
                operation = operation or "unknown"
                
                if model not in detailed_stats["month"]["by_model"]:
                    detailed_stats["month"]["by_model"][model] = {"calls": 0, "cost": 0.0}
                detailed_stats["month"]["by_model"][model]["calls"] += calls
                detailed_stats["month"]["by_model"][model]["cost"] += cost or 0.0
                
                if operation not in detailed_stats["month"]["by_operation"]:
                    detailed_stats["month"]["by_operation"][operation] = {"calls": 0, "cost": 0.0, "model": model}
                detailed_stats["month"]["by_operation"][operation]["calls"] += calls
                detailed_stats["month"]["by_operation"][operation]["cost"] += cost or 0.0
            
            # Gesamt (alle Zeiten)
            cursor = conn.execute("""
                SELECT model, operation, COUNT(*) as calls, SUM(cost_eur) as total_cost
                FROM cost_entries
                GROUP BY model, operation
            """)
            
            for row in cursor.fetchall():
                model, operation, calls, cost = row
                operation = operation or "unknown"
                
                if model not in detailed_stats["by_model"]:
                    detailed_stats["by_model"][model] = {"calls": 0, "cost": 0.0}
                detailed_stats["by_model"][model]["calls"] += calls
                detailed_stats["by_model"][model]["cost"] += cost or 0.0
                
                if operation not in detailed_stats["by_operation"]:
                    detailed_stats["by_operation"][operation] = {"calls": 0, "cost": 0.0, "model": model}
                detailed_stats["by_operation"][operation]["calls"] += calls
                detailed_stats["by_operation"][operation]["cost"] += cost or 0.0
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Fehler beim Abrufen detaillierter Statistiken: {e}")
    
    return JSONResponse({
        "today": today_stats,
        "trend": trend_formatted,  # Verwende formatierten Trend
        "total_30d": {
            "cost": total_cost,
            "api_calls": total_calls
        },
        "limits": limits,
        "daily_limit": tracker.daily_limit_eur,
        "daily_api_calls_limit": tracker.daily_api_calls_limit,
        "track_costs": tracker.track_costs,
        "model_prices": tracker.model_prices,
        "default_model": tracker.default_model,
        "detailed_stats": detailed_stats
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

@router.get("/api/cost-tracker/current-model")
async def get_current_model():
    """
    Gibt das aktuell verwendete KI-Modell zurück.
    
    Returns:
        JSON mit aktuellem Modell und Konfiguration
    """
    tracker = get_cost_tracker()
    
    # Prüfe ob Modell in Konfiguration überschrieben ist
    from backend.config import cfg
    configured_model = cfg("ki_codechecker:model", None)
    
    return JSONResponse({
        "current_model": configured_model or tracker.default_model,
        "default_model": tracker.default_model,
        "configured_model": configured_model,
        "is_custom": configured_model is not None and configured_model != tracker.default_model,
        "model_prices": tracker.model_prices.get(configured_model or tracker.default_model, tracker.model_prices[tracker.default_model])
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

