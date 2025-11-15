"""
Kosten-Tracker für KI-Code-Verbesserungen.
Überwacht API-Kosten, Token-Verbrauch und Ressourcenverbrauch.
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from backend.config import cfg

class CostTracker:
    """Trackt Kosten für KI-API-Aufrufe und Ressourcenverbrauch."""
    
    def __init__(self):
        self.db_path = Path("data/code_fixes_cost.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        # Konfiguration
        self.daily_limit_eur = float(cfg("ki_codechecker:costs:daily_limit_eur", 5.0))
        self.daily_api_calls_limit = int(cfg("ki_codechecker:costs:daily_api_calls_limit", 50))
        self.daily_improvements_limit = int(cfg("ki_codechecker:costs:daily_improvements_limit", 10))
        self.track_costs = cfg("ki_codechecker:costs:track_costs", True)
        
        # Modell-Preise (Stand: 2025, in EUR pro 1000 Tokens)
        # GPT-4o-mini ist unser Standard-Modell (günstig und schnell)
        self.model_prices = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # Standard-Modell
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
        }
        
        # Standard-Modell für Code-Verbesserungen
        self.default_model = "gpt-4o-mini"
    
    def _init_db(self):
        """Initialisiert Datenbank."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_eur REAL NOT NULL,
                    file_path TEXT,
                    operation TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_totals (
                    date TEXT PRIMARY KEY,
                    total_cost_eur REAL NOT NULL,
                    total_api_calls INTEGER NOT NULL,
                    total_improvements INTEGER NOT NULL
                )
            """)
            conn.commit()
    
    def track_api_call(self, model: str, input_tokens: int, output_tokens: int, 
                      file_path: Optional[str] = None, operation: Optional[str] = None) -> float:
        """
        Trackt API-Aufruf und berechnet Kosten.
        
        Returns:
            Kosten in EUR
        """
        if not self.track_costs:
            return 0.0
        
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cost_entries 
                (timestamp, model, input_tokens, output_tokens, cost_eur, file_path, operation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                model,
                input_tokens,
                output_tokens,
                cost,
                file_path,
                operation
            ))
            conn.commit()
        
        # Update daily totals
        self._update_daily_totals(cost, 1, 0)
        
        return cost
    
    def track_improvement(self, file_path: str):
        """Trackt Code-Verbesserung (ohne API-Kosten)."""
        if not self.track_costs:
            return
        
        self._update_daily_totals(0.0, 0, 1)
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Berechnet Kosten basierend auf Modell-Preisen."""
        # Verwende gpt-4o-mini als Fallback (unser Standard-Modell)
        prices = self.model_prices.get(model, self.model_prices["gpt-4o-mini"])
        
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        
        return input_cost + output_cost
    
    def _update_daily_totals(self, cost: float, api_calls: int, improvements: int):
        """Aktualisiert Tages-Totals."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            # Prüfe ob Eintrag existiert
            cursor = conn.execute("SELECT total_cost_eur, total_api_calls, total_improvements FROM daily_totals WHERE date = ?", (today,))
            row = cursor.fetchone()
            
            if row:
                # Update
                conn.execute("""
                    UPDATE daily_totals 
                    SET total_cost_eur = total_cost_eur + ?,
                        total_api_calls = total_api_calls + ?,
                        total_improvements = total_improvements + ?
                    WHERE date = ?
                """, (cost, api_calls, improvements, today))
            else:
                # Insert
                conn.execute("""
                    INSERT INTO daily_totals (date, total_cost_eur, total_api_calls, total_improvements)
                    VALUES (?, ?, ?, ?)
                """, (today, cost, api_calls, improvements))
            conn.commit()
    
    def get_daily_costs(self, date: Optional[str] = None) -> float:
        """Gibt Kosten für Tag zurück."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT total_cost_eur FROM daily_totals WHERE date = ?", (date,))
            row = cursor.fetchone()
            return row[0] if row else 0.0
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """Gibt Tages-Statistiken zurück."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT total_cost_eur, total_api_calls, total_improvements 
                FROM daily_totals 
                WHERE date = ?
            """, (date,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "date": date,
                    "total_cost_eur": row[0],
                    "total_api_calls": row[1],
                    "total_improvements": row[2],
                    "cost_limit_eur": self.daily_limit_eur,
                    "api_calls_limit": self.daily_api_calls_limit,
                    "improvements_limit": self.daily_improvements_limit
                }
            else:
                return {
                    "date": date,
                    "total_cost_eur": 0.0,
                    "total_api_calls": 0,
                    "total_improvements": 0,
                    "cost_limit_eur": self.daily_limit_eur,
                    "api_calls_limit": self.daily_api_calls_limit,
                    "improvements_limit": self.daily_improvements_limit
                }
    
    def can_improve_code(self) -> tuple[bool, str]:
        """Prüft ob Code-Verbesserung erlaubt ist."""
        stats = self.get_daily_stats()
        
        if stats["total_improvements"] >= self.daily_improvements_limit:
            return False, f"Tages-Limit erreicht: {self.daily_improvements_limit} Verbesserungen"
        
        if stats["total_api_calls"] >= self.daily_api_calls_limit:
            return False, f"API-Limit erreicht: {self.daily_api_calls_limit} Aufrufe"
        
        if stats["total_cost_eur"] >= self.daily_limit_eur:
            return False, f"Kosten-Limit erreicht: {self.daily_limit_eur}€"
        
        return True, "OK"
    
    def get_cost_per_file(self, days: int = 7) -> List[Dict]:
        """Gibt Kosten pro Datei zurück (letzte N Tage)."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT file_path, SUM(cost_eur) as total_cost, COUNT(*) as call_count
                FROM cost_entries
                WHERE timestamp >= ? AND file_path IS NOT NULL
                GROUP BY file_path
                ORDER BY total_cost DESC
                LIMIT 20
            """, (since,))
            
            return [
                {"file": row[0], "cost_eur": row[1], "call_count": row[2]}
                for row in cursor.fetchall()
            ]
    
    def get_cost_trend(self, days: int = 7) -> List[Dict]:
        """Gibt Kosten-Trend zurück (letzte N Tage)."""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, total_cost_eur, total_api_calls, total_improvements
                FROM daily_totals
                WHERE date >= ?
                ORDER BY date ASC
            """, (since,))
            
            return [
                {
                    "date": row[0],
                    "cost_eur": row[1],
                    "api_calls": row[2],
                    "improvements": row[3]
                }
                for row in cursor.fetchall()
            ]

# Singleton-Instanz
_cost_tracker = None

def get_cost_tracker() -> CostTracker:
    """Gibt Singleton-Instanz zurück."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

