# -*- coding: utf-8 -*-
"""
LLM-Monitoring Service für FAMO TrafficApp 3.0

Überwacht Performance, Kosten und Qualität der LLM-Integration.
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from contextlib import contextmanager

@dataclass
class LLMInteraction:
    """Dataclass für LLM-Interaktionen"""
    timestamp: str
    model: str
    task_type: str
    prompt_length: int
    response_length: int
    tokens_used: int
    processing_time: float
    cost_usd: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceMetrics:
    """Dataclass für Performance-Metriken"""
    total_interactions: int
    successful_interactions: int
    failed_interactions: int
    success_rate: float
    total_tokens: int
    total_cost_usd: float
    avg_processing_time: float
    avg_tokens_per_call: float
    cost_per_token: float

class LLMMonitoringService:
    """Service für LLM-Monitoring und Performance-Tracking"""
    
    def __init__(self, db_path: str = "data/llm_monitoring.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
        # Token-Preise pro Modell (USD pro 1M Tokens)
        self.token_prices = {
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.6}
        }
    
    def _init_database(self):
        """Initialisiert SQLite-Datenbank für Monitoring"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    prompt_length INTEGER NOT NULL,
                    response_length INTEGER NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    processing_time REAL NOT NULL,
                    cost_usd REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            # Index für Performance-Queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON llm_interactions(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model ON llm_interactions(model)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_type ON llm_interactions(task_type)
            """)
    
    @contextmanager
    def _get_connection(self):
        """Context Manager für Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def log_interaction(self, 
                       model: str,
                       task_type: str,
                       prompt: str,
                       response: str,
                       tokens_used: Dict[str, int],
                       processing_time: float,
                       success: bool = True,
                       error_message: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Loggt eine LLM-Interaktion
        
        Args:
            model: Verwendetes Modell
            task_type: Art der Aufgabe (z.B. "route_optimization", "clustering")
            prompt: Eingabe-Prompt
            response: LLM-Response
            tokens_used: Token-Verbrauch {"prompt_tokens": x, "completion_tokens": y, "total_tokens": z}
            processing_time: Verarbeitungszeit in Sekunden
            success: Erfolg der Interaktion
            error_message: Fehlermeldung bei Fehlern
            metadata: Zusätzliche Metadaten
        """
        timestamp = datetime.now().isoformat()
        prompt_length = len(prompt)
        response_length = len(response)
        total_tokens = tokens_used.get("total_tokens", 0)
        
        # Berechne Kosten
        cost_usd = self._calculate_cost(model, tokens_used)
        
        # Erstelle Interaction-Objekt
        interaction = LLMInteraction(
            timestamp=timestamp,
            model=model,
            task_type=task_type,
            prompt_length=prompt_length,
            response_length=response_length,
            tokens_used=total_tokens,
            processing_time=processing_time,
            cost_usd=cost_usd,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        # Speichere in Datenbank
        self._save_interaction(interaction)
        
        # Log für Debugging
        self.logger.info(f"LLM Interaction logged: {model} - {task_type} - {total_tokens} tokens - ${cost_usd:.4f}")
    
    def _calculate_cost(self, model: str, tokens_used: Dict[str, int]) -> float:
        """Berechnet Kosten basierend auf Token-Verbrauch"""
        if model not in self.token_prices:
            model = "gpt-4"  # Fallback
        
        prices = self.token_prices[model]
        prompt_tokens = tokens_used.get("prompt_tokens", 0)
        completion_tokens = tokens_used.get("completion_tokens", 0)
        
        # Kosten in USD pro 1M Tokens
        prompt_cost = (prompt_tokens / 1_000_000) * prices["input"]
        completion_cost = (completion_tokens / 1_000_000) * prices["output"]
        
        return prompt_cost + completion_cost
    
    def _save_interaction(self, interaction: LLMInteraction):
        """Speichert Interaction in Datenbank"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO llm_interactions 
                (timestamp, model, task_type, prompt_length, response_length, 
                 tokens_used, processing_time, cost_usd, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction.timestamp,
                interaction.model,
                interaction.task_type,
                interaction.prompt_length,
                interaction.response_length,
                interaction.tokens_used,
                interaction.processing_time,
                interaction.cost_usd,
                interaction.success,
                interaction.error_message,
                json.dumps(interaction.metadata) if interaction.metadata else None
            ))
    
    def get_performance_metrics(self, 
                              days: int = 7,
                              model: Optional[str] = None,
                              task_type: Optional[str] = None) -> PerformanceMetrics:
        """
        Gibt Performance-Metriken zurück
        
        Args:
            days: Anzahl Tage für Analyse
            model: Filter nach Modell
            task_type: Filter nach Task-Typ
            
        Returns:
            PerformanceMetrics-Objekt
        """
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            # Base Query
            query = """
                SELECT COUNT(*) as total_interactions,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_interactions,
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_interactions,
                       SUM(tokens_used) as total_tokens,
                       SUM(cost_usd) as total_cost_usd,
                       AVG(processing_time) as avg_processing_time,
                       AVG(tokens_used) as avg_tokens_per_call
                FROM llm_interactions
                WHERE timestamp >= ?
            """
            params = [since_date]
            
            # Filter hinzufügen
            if model:
                query += " AND model = ?"
                params.append(model)
            
            if task_type:
                query += " AND task_type = ?"
                params.append(task_type)
            
            result = conn.execute(query, params).fetchone()
            
            total_interactions = result["total_interactions"] or 0
            successful_interactions = result["successful_interactions"] or 0
            failed_interactions = result["failed_interactions"] or 0
            total_tokens = result["total_tokens"] or 0
            total_cost_usd = result["total_cost_usd"] or 0.0
            avg_processing_time = result["avg_processing_time"] or 0.0
            avg_tokens_per_call = result["avg_tokens_per_call"] or 0.0
            
            # Berechne abgeleitete Metriken
            success_rate = successful_interactions / total_interactions if total_interactions > 0 else 0.0
            cost_per_token = total_cost_usd / total_tokens if total_tokens > 0 else 0.0
            
            return PerformanceMetrics(
                total_interactions=total_interactions,
                successful_interactions=successful_interactions,
                failed_interactions=failed_interactions,
                success_rate=success_rate,
                total_tokens=total_tokens,
                total_cost_usd=total_cost_usd,
                avg_processing_time=avg_processing_time,
                avg_tokens_per_call=avg_tokens_per_call,
                cost_per_token=cost_per_token
            )
    
    def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Gibt die letzten Interaktionen zurück"""
        with self._get_connection() as conn:
            query = """
                SELECT * FROM llm_interactions
                ORDER BY timestamp DESC
                LIMIT ?
            """
            results = conn.execute(query, [limit]).fetchall()
            
            interactions = []
            for row in results:
                interaction = dict(row)
                # Parse metadata JSON
                if interaction["metadata"]:
                    try:
                        interaction["metadata"] = json.loads(interaction["metadata"])
                    except json.JSONDecodeError:
                        interaction["metadata"] = {}
                interactions.append(interaction)
            
            return interactions
    
    def get_cost_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Gibt Kostenanalyse zurück"""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            # Kosten pro Modell
            model_costs = conn.execute("""
                SELECT model, SUM(cost_usd) as total_cost, COUNT(*) as calls
                FROM llm_interactions
                WHERE timestamp >= ? AND success = 1
                GROUP BY model
                ORDER BY total_cost DESC
            """, [since_date]).fetchall()
            
            # Kosten pro Task-Typ
            task_costs = conn.execute("""
                SELECT task_type, SUM(cost_usd) as total_cost, COUNT(*) as calls
                FROM llm_interactions
                WHERE timestamp >= ? AND success = 1
                GROUP BY task_type
                ORDER BY total_cost DESC
            """, [since_date]).fetchall()
            
            # Tägliche Kosten
            daily_costs = conn.execute("""
                SELECT DATE(timestamp) as date, SUM(cost_usd) as daily_cost
                FROM llm_interactions
                WHERE timestamp >= ? AND success = 1
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, [since_date]).fetchall()
            
            return {
                "period_days": days,
                "model_costs": [dict(row) for row in model_costs],
                "task_costs": [dict(row) for row in task_costs],
                "daily_costs": [dict(row) for row in daily_costs],
                "total_cost": sum(row["total_cost"] for row in model_costs)
            }
    
    def detect_anomalies(self, days: int = 7) -> List[Dict[str, Any]]:
        """Erkennt Anomalien in LLM-Performance"""
        anomalies = []
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            # Hohe Latenz
            high_latency = conn.execute("""
                SELECT * FROM llm_interactions
                WHERE timestamp >= ? AND processing_time > 10.0
                ORDER BY processing_time DESC
                LIMIT 5
            """, [since_date]).fetchall()
            
            for row in high_latency:
                anomalies.append({
                    "type": "high_latency",
                    "timestamp": row["timestamp"],
                    "model": row["model"],
                    "processing_time": row["processing_time"],
                    "severity": "warning" if row["processing_time"] < 30 else "critical"
                })
            
            # Hohe Token-Kosten
            high_cost = conn.execute("""
                SELECT * FROM llm_interactions
                WHERE timestamp >= ? AND cost_usd > 0.10
                ORDER BY cost_usd DESC
                LIMIT 5
            """, [since_date]).fetchall()
            
            for row in high_cost:
                anomalies.append({
                    "type": "high_cost",
                    "timestamp": row["timestamp"],
                    "model": row["model"],
                    "cost_usd": row["cost_usd"],
                    "tokens_used": row["tokens_used"],
                    "severity": "warning" if row["cost_usd"] < 0.50 else "critical"
                })
            
            # Fehlerrate
            error_rate = conn.execute("""
                SELECT model, 
                       COUNT(*) as total_calls,
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_calls,
                       CAST(SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as error_rate
                FROM llm_interactions
                WHERE timestamp >= ?
                GROUP BY model
                HAVING error_rate > 0.1
            """, [since_date]).fetchall()
            
            for row in error_rate:
                anomalies.append({
                    "type": "high_error_rate",
                    "model": row["model"],
                    "error_rate": row["error_rate"],
                    "total_calls": row["total_calls"],
                    "failed_calls": row["failed_calls"],
                    "severity": "critical"
                })
        
        return anomalies
    
    def export_metrics(self, file_path: str, days: int = 30):
        """Exportiert Metriken als JSON"""
        metrics = {
            "export_timestamp": datetime.now().isoformat(),
            "period_days": days,
            "performance_metrics": asdict(self.get_performance_metrics(days)),
            "cost_analysis": self.get_cost_analysis(days),
            "anomalies": self.detect_anomalies(days),
            "recent_interactions": self.get_recent_interactions(20)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Metrics exported to {file_path}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Bereinigt alte Monitoring-Daten"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        with self._get_connection() as conn:
            result = conn.execute("""
                DELETE FROM llm_interactions
                WHERE timestamp < ?
            """, [cutoff_date])
            
            deleted_count = result.rowcount
            self.logger.info(f"Cleaned up {deleted_count} old monitoring records")
            
            return deleted_count
