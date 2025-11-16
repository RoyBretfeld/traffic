"""
KI-Aktivitäts-API für detaillierte Aktivitäts-Logs.
Ermöglicht Abfrage von KI-Interaktionen mit Filtern und Pagination.
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import sqlite3
import logging
from backend.services.cost_tracker import get_cost_tracker

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/ki/activity-log")
async def get_ki_activity_log(
    limit: int = Query(100, ge=1, le=1000, description="Anzahl der Einträge"),
    offset: int = Query(0, ge=0, description="Offset für Pagination"),
    model: Optional[str] = Query(None, description="Filter nach Modell"),
    operation: Optional[str] = Query(None, description="Filter nach Operation"),
    start_date: Optional[str] = Query(None, description="Start-Datum (ISO-Format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End-Datum (ISO-Format: YYYY-MM-DD)"),
    file_path: Optional[str] = Query(None, description="Filter nach Dateipfad (teilweise Match)")
):
    """
    Gibt detailliertes KI-Aktivitäts-Log zurück.
    
    Args:
        limit: Anzahl der zurückgegebenen Einträge (1-1000)
        offset: Offset für Pagination
        model: Filter nach KI-Modell (z.B. "gpt-4o-mini")
        operation: Filter nach Operation (z.B. "code_analysis", "error_pattern_matching")
        start_date: Start-Datum für Zeitfilter (YYYY-MM-DD)
        end_date: End-Datum für Zeitfilter (YYYY-MM-DD)
        file_path: Teilstring-Match für Dateipfad
    
    Returns:
        JSON mit Aktivitäts-Log-Einträgen und Metadaten
    """
    tracker = get_cost_tracker()
    
    # Baue WHERE-Klausel dynamisch auf
    where_clauses = []
    params = []
    
    if model:
        where_clauses.append("model = ?")
        params.append(model)
    
    if operation:
        where_clauses.append("operation = ?")
        params.append(operation)
    
    if start_date:
        try:
            start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00").isoformat()
            where_clauses.append("timestamp >= ?")
            params.append(start_datetime)
        except ValueError:
            return JSONResponse({
                "success": False,
                "error": f"Ungültiges Start-Datum-Format: {start_date}. Erwartet: YYYY-MM-DD"
            }, status_code=400)
    
    if end_date:
        try:
            end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59").isoformat()
            where_clauses.append("timestamp <= ?")
            params.append(end_datetime)
        except ValueError:
            return JSONResponse({
                "success": False,
                "error": f"Ungültiges End-Datum-Format: {end_date}. Erwartet: YYYY-MM-DD"
            }, status_code=400)
    
    if file_path:
        where_clauses.append("file_path LIKE ?")
        params.append(f"%{file_path}%")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    try:
        with sqlite3.connect(tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Gesamtanzahl für Pagination
            count_query = f"SELECT COUNT(*) as total FROM cost_entries WHERE {where_sql}"
            count_result = conn.execute(count_query, params).fetchone()
            total_count = count_result["total"] if count_result else 0
            
            # Einträge abrufen
            query = f"""
                SELECT 
                    id,
                    timestamp,
                    model,
                    input_tokens,
                    output_tokens,
                    cost_eur,
                    file_path,
                    operation
                FROM cost_entries
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params_with_pagination = params + [limit, offset]
            
            cursor = conn.execute(query, params_with_pagination)
            rows = cursor.fetchall()
            
            # Konvertiere zu Dict-Liste
            entries = []
            for row in rows:
                entries.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "model": row["model"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_tokens": row["input_tokens"] + row["output_tokens"],
                    "cost_eur": row["cost_eur"],
                    "file_path": row["file_path"],
                    "operation": row["operation"] or "unknown"
                })
            
            # Berechne Aggregat-Statistiken für die gefilterten Einträge
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(cost_eur) as total_cost,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    AVG(cost_eur) as avg_cost_per_call
                FROM cost_entries
                WHERE {where_sql}
            """
            stats_result = conn.execute(stats_query, params).fetchone()
            
            stats = {
                "total_calls": stats_result["total_calls"] or 0,
                "total_cost": stats_result["total_cost"] or 0.0,
                "total_input_tokens": stats_result["total_input_tokens"] or 0,
                "total_output_tokens": stats_result["total_output_tokens"] or 0,
                "total_tokens": (stats_result["total_input_tokens"] or 0) + (stats_result["total_output_tokens"] or 0),
                "avg_cost_per_call": stats_result["avg_cost_per_call"] or 0.0
            }
            
            return JSONResponse({
                "success": True,
                "entries": entries,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                },
                "filters": {
                    "model": model,
                    "operation": operation,
                    "start_date": start_date,
                    "end_date": end_date,
                    "file_path": file_path
                },
                "stats": stats
            })
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des KI-Aktivitäts-Logs: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/api/ki/activity-summary")
async def get_ki_activity_summary(
    days: int = Query(7, ge=1, le=365, description="Anzahl der Tage für Zusammenfassung")
):
    """
    Gibt Zusammenfassung der KI-Aktivität für die letzten N Tage zurück.
    
    Args:
        days: Anzahl der Tage (1-365)
    
    Returns:
        JSON mit täglicher Zusammenfassung
    """
    tracker = get_cost_tracker()
    
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    try:
        with sqlite3.connect(tracker.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Tägliche Zusammenfassung
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as calls,
                    SUM(cost_eur) as cost,
                    SUM(input_tokens) as input_tokens,
                    SUM(output_tokens) as output_tokens,
                    COUNT(DISTINCT model) as unique_models,
                    COUNT(DISTINCT operation) as unique_operations
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            
            cursor = conn.execute(query, (start_date,))
            rows = cursor.fetchall()
            
            daily_summary = []
            for row in rows:
                daily_summary.append({
                    "date": row["date"],
                    "calls": row["calls"],
                    "cost": row["cost"] or 0.0,
                    "input_tokens": row["input_tokens"] or 0,
                    "output_tokens": row["output_tokens"] or 0,
                    "total_tokens": (row["input_tokens"] or 0) + (row["output_tokens"] or 0),
                    "unique_models": row["unique_models"],
                    "unique_operations": row["unique_operations"]
                })
            
            # Gesamt-Statistiken
            total_query = """
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(cost_eur) as total_cost,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    AVG(cost_eur) as avg_cost_per_call
                FROM cost_entries
                WHERE timestamp >= ?
            """
            total_result = conn.execute(total_query, (start_date,)).fetchone()
            
            # Top-Modelle
            model_query = """
                SELECT 
                    model,
                    COUNT(*) as calls,
                    SUM(cost_eur) as cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY cost DESC
                LIMIT 5
            """
            model_rows = conn.execute(model_query, (start_date,)).fetchall()
            top_models = [
                {"model": row["model"], "calls": row["calls"], "cost": row["cost"] or 0.0}
                for row in model_rows
            ]
            
            # Top-Operationen
            operation_query = """
                SELECT 
                    COALESCE(operation, 'unknown') as operation,
                    COUNT(*) as calls,
                    SUM(cost_eur) as cost
                FROM cost_entries
                WHERE timestamp >= ?
                GROUP BY operation
                ORDER BY cost DESC
                LIMIT 5
            """
            operation_rows = conn.execute(operation_query, (start_date,)).fetchall()
            top_operations = [
                {"operation": row["operation"], "calls": row["calls"], "cost": row["cost"] or 0.0}
                for row in operation_rows
            ]
            
            return JSONResponse({
                "success": True,
                "period_days": days,
                "daily_summary": daily_summary,
                "totals": {
                    "total_calls": total_result["total_calls"] or 0,
                    "total_cost": total_result["total_cost"] or 0.0,
                    "total_input_tokens": total_result["total_input_tokens"] or 0,
                    "total_output_tokens": total_result["total_output_tokens"] or 0,
                    "total_tokens": (total_result["total_input_tokens"] or 0) + (total_result["total_output_tokens"] or 0),
                    "avg_cost_per_call": total_result["avg_cost_per_call"] or 0.0
                },
                "top_models": top_models,
                "top_operations": top_operations
            })
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der KI-Aktivitäts-Zusammenfassung: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

