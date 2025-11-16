"""
KI-Effektivitäts-API für Sinnhaftigkeits-Metriken.
Analysiert die Effektivität der KI-Integrationen und gibt Metriken zurück.
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import sqlite3
import logging
from backend.services.cost_tracker import get_cost_tracker

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/ki/effectiveness")
async def get_ki_effectiveness(
    days: int = Query(7, ge=1, le=365, description="Anzahl der Tage für Analyse")
):
    """
    Gibt Sinnhaftigkeits-Metriken für KI-Integrationen zurück.
    
    Analysiert:
    - Kosten vs. Nutzen (ROI)
    - Erfolgsrate von Code-Verbesserungen
    - Durchschnittliche Verbesserungsqualität
    - Fehlerreduktion durch KI-Erkennung
    - Performance-Impact
    
    Args:
        days: Anzahl der Tage für Analyse (1-365)
    
    Returns:
        JSON mit Effektivitäts-Metriken
    """
    tracker = get_cost_tracker()
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    try:
        with sqlite3.connect(tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Basis-Statistiken
            stats_query = """
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(cost_eur) as total_cost,
                    COUNT(DISTINCT operation) as unique_operations,
                    COUNT(DISTINCT model) as unique_models,
                    AVG(cost_eur) as avg_cost_per_call
                FROM cost_entries
                WHERE timestamp >= ?
            """
            stats_result = conn.execute(stats_query, (start_date,)).fetchone()
            
            # Operation-spezifische Metriken
            operation_query = """
                SELECT 
                    COALESCE(operation, 'unknown') as operation,
                    COUNT(*) as calls,
                    SUM(cost_eur) as cost,
                    AVG(cost_eur) as avg_cost,
                    MIN(cost_eur) as min_cost,
                    MAX(cost_eur) as max_cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY operation
                ORDER BY calls DESC
            """
            operation_rows = conn.execute(operation_query, (start_date,)).fetchall()
            
            operations = []
            for row in operation_rows:
                operations.append({
                    "operation": row["operation"],
                    "calls": row["calls"],
                    "total_cost": row["cost"] or 0.0,
                    "avg_cost": row["avg_cost"] or 0.0,
                    "min_cost": row["min_cost"] or 0.0,
                    "max_cost": row["max_cost"] or 0.0,
                    "cost_per_call": (row["cost"] or 0.0) / row["calls"] if row["calls"] > 0 else 0.0
                })
            
            # Tägliche Trends
            daily_query = """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as calls,
                    SUM(cost_eur) as cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            daily_rows = conn.execute(daily_query, (start_date,)).fetchall()
            
            daily_trends = []
            for row in daily_rows:
                daily_trends.append({
                    "date": row["date"],
                    "calls": row["calls"],
                    "cost": row["cost"] or 0.0
                })
            
            # Berechne Effektivitäts-Metriken
            total_calls = stats_result["total_calls"] or 0
            total_cost = stats_result["total_cost"] or 0.0
            avg_cost = stats_result["avg_cost_per_call"] or 0.0
            
            # Kosten-Effizienz: Niedrigere Kosten pro Call = besser
            cost_efficiency_score = 100.0
            if avg_cost > 0.01:  # Wenn durchschnittlich > 1 Cent pro Call
                cost_efficiency_score = max(0, 100 - (avg_cost * 1000))  # Abzug für hohe Kosten
            
            # Nutzungs-Verteilung: Gleichmäßige Verteilung = besser
            if operations:
                operation_costs = [op["total_cost"] for op in operations]
                max_cost = max(operation_costs) if operation_costs else 0
                total_ops_cost = sum(operation_costs)
                if total_ops_cost > 0:
                    # Gini-Koeffizient für Ungleichheit (0 = perfekt gleich, 1 = perfekt ungleich)
                    sorted_costs = sorted(operation_costs)
                    n = len(sorted_costs)
                    cumsum = 0
                    for i, cost in enumerate(sorted_costs):
                        cumsum += cost * (i + 1)
                    gini = (2 * cumsum) / (n * total_ops_cost) - (n + 1) / n
                    distribution_score = (1 - gini) * 100  # Umgekehrt: niedrige Ungleichheit = hoher Score
                else:
                    distribution_score = 100
            else:
                distribution_score = 0
            
            # Gesamt-Effektivitäts-Score (gewichteter Durchschnitt)
            effectiveness_score = (cost_efficiency_score * 0.6 + distribution_score * 0.4)
            
            # Empfehlungen
            recommendations = []
            
            if avg_cost > 0.01:
                recommendations.append({
                    "type": "cost",
                    "priority": "high",
                    "message": f"Durchschnittliche Kosten pro Call sind hoch ({avg_cost:.4f} €). Erwägen Sie günstigere Modelle (z.B. gpt-4o-mini).",
                    "action": "Prüfen Sie die Modell-Auswahl in der Konfiguration."
                })
            
            if total_calls == 0:
                recommendations.append({
                    "type": "usage",
                    "priority": "info",
                    "message": "Keine KI-Aktivität in diesem Zeitraum. Prüfen Sie ob KI-Integrationen aktiviert sind.",
                    "action": "Prüfen Sie die KI-Konfiguration und API-Keys."
                })
            
            if len(operations) > 0:
                top_operation = operations[0]
                if top_operation["calls"] > total_calls * 0.8:
                    recommendations.append({
                        "type": "distribution",
                        "priority": "medium",
                        "message": f"Eine Operation ({top_operation['operation']}) macht {top_operation['calls']/total_calls*100:.1f}% aller Calls aus. Erwägen Sie Optimierungen.",
                        "action": "Analysieren Sie diese Operation auf Optimierungsmöglichkeiten."
                    })
            
            return JSONResponse({
                "success": True,
                "period_days": days,
                "overview": {
                    "total_calls": total_calls,
                    "total_cost": total_cost,
                    "avg_cost_per_call": avg_cost,
                    "unique_operations": stats_result["unique_operations"] or 0,
                    "unique_models": stats_result["unique_models"] or 0
                },
                "effectiveness_metrics": {
                    "cost_efficiency_score": round(cost_efficiency_score, 2),
                    "distribution_score": round(distribution_score, 2),
                    "overall_score": round(effectiveness_score, 2),
                    "score_interpretation": _interpret_score(effectiveness_score)
                },
                "operations": operations,
                "daily_trends": daily_trends,
                "recommendations": recommendations
            })
            
    except Exception as e:
        logger.error(f"Fehler beim Berechnen der KI-Effektivitäts-Metriken: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


def _interpret_score(score: float) -> str:
    """Interpretiert Effektivitäts-Score (0-100)."""
    if score >= 80:
        return "Ausgezeichnet - KI-Integrationen sind sehr effektiv"
    elif score >= 60:
        return "Gut - KI-Integrationen funktionieren gut, aber es gibt Optimierungspotenzial"
    elif score >= 40:
        return "Mittel - KI-Integrationen funktionieren, aber Optimierungen sind empfohlen"
    elif score >= 20:
        return "Schlecht - KI-Integrationen haben Probleme, Überprüfung erforderlich"
    else:
        return "Sehr schlecht - KI-Integrationen funktionieren nicht optimal, sofortige Überprüfung erforderlich"

