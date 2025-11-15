"""
Performance-Tracker für KI-Code-Verbesserungen.
Überwacht Analyse-Zeit, API-Latenz und Ressourcenverbrauch.
"""
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from contextlib import contextmanager
from backend.config import cfg

class PerformanceTracker:
    """Trackt Performance-Metriken für Code-Analyse und Verbesserungen."""
    
    def __init__(self):
        self.db_path = Path("data/code_fixes_performance.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
        # Konfiguration
        self.track_performance = cfg("ki_codechecker:performance:track_performance", True)
        self.log_slow_operations = cfg("ki_codechecker:performance:log_slow_operations", True)
        self.slow_operation_threshold = float(cfg("ki_codechecker:performance:slow_operation_threshold_seconds", 10.0))
    
    def _init_db(self):
        """Initialisiert Datenbank."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    file_path TEXT,
                    duration_seconds REAL NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_averages (
                    date TEXT PRIMARY KEY,
                    avg_analysis_time REAL,
                    avg_api_call_time REAL,
                    avg_test_time REAL,
                    total_operations INTEGER
                )
            """)
            conn.commit()
    
    @contextmanager
    def track_operation(self, operation_name: str, file_path: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Context Manager zum Tracken von Operationen.
        
        Usage:
            with tracker.track_operation("code_analysis", "routes/upload_csv.py"):
                # Code-Analyse hier
                pass
        """
        if not self.track_performance:
            yield
            return
        
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._save_performance_entry(operation_name, file_path, duration, metadata)
            
            # Log langsame Operationen
            if self.log_slow_operations and duration > self.slow_operation_threshold:
                print(f"[PERFORMANCE] Langsame Operation: {operation_name} ({duration:.2f}s) - {file_path or 'N/A'}")
    
    def _save_performance_entry(self, operation: str, file_path: Optional[str], duration: float, metadata: Optional[Dict]):
        """Speichert Performance-Eintrag."""
        metadata_json = None
        if metadata:
            import json
            metadata_json = json.dumps(metadata)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_entries 
                (timestamp, operation, file_path, duration_seconds, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                operation,
                file_path,
                duration,
                metadata_json
            ))
            conn.commit()
        
        # Update daily averages
        self._update_daily_averages(operation, duration)
    
    def _update_daily_averages(self, operation: str, duration: float):
        """Aktualisiert Tages-Durchschnitte."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            # Prüfe ob Eintrag existiert
            cursor = conn.execute("SELECT * FROM daily_averages WHERE date = ?", (today,))
            row = cursor.fetchone()
            
            if row:
                # Update (gleitender Durchschnitt)
                # Hole aktuelle Werte
                cursor = conn.execute("""
                    SELECT avg_analysis_time, avg_api_call_time, avg_test_time, total_operations
                    FROM daily_averages WHERE date = ?
                """, (today,))
                current = cursor.fetchone()
                
                total_ops = current[3] + 1
                
                # Update basierend auf Operation-Typ
                if operation == "code_analysis":
                    new_avg = ((current[0] * current[3]) + duration) / total_ops if current[0] else duration
                    conn.execute("""
                        UPDATE daily_averages 
                        SET avg_analysis_time = ?, total_operations = ?
                        WHERE date = ?
                    """, (new_avg, total_ops, today))
                elif operation == "api_call":
                    new_avg = ((current[1] * current[3]) + duration) / total_ops if current[1] else duration
                    conn.execute("""
                        UPDATE daily_averages 
                        SET avg_api_call_time = ?, total_operations = ?
                        WHERE date = ?
                    """, (new_avg, total_ops, today))
                elif operation == "test_execution":
                    new_avg = ((current[2] * current[3]) + duration) / total_ops if current[2] else duration
                    conn.execute("""
                        UPDATE daily_averages 
                        SET avg_test_time = ?, total_operations = ?
                        WHERE date = ?
                    """, (new_avg, total_ops, today))
                else:
                    conn.execute("""
                        UPDATE daily_averages 
                        SET total_operations = ?
                        WHERE date = ?
                    """, (total_ops, today))
            else:
                # Insert
                avg_analysis = duration if operation == "code_analysis" else None
                avg_api = duration if operation == "api_call" else None
                avg_test = duration if operation == "test_execution" else None
                
                conn.execute("""
                    INSERT INTO daily_averages 
                    (date, avg_analysis_time, avg_api_call_time, avg_test_time, total_operations)
                    VALUES (?, ?, ?, ?, 1)
                """, (today, avg_analysis, avg_api, avg_test))
            conn.commit()
    
    def get_daily_averages(self, date: Optional[str] = None) -> Dict:
        """Gibt Tages-Durchschnitte zurück."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT avg_analysis_time, avg_api_call_time, avg_test_time, total_operations
                FROM daily_averages
                WHERE date = ?
            """, (date,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "date": date,
                    "avg_analysis_time": row[0] or 0.0,
                    "avg_api_call_time": row[1] or 0.0,
                    "avg_test_time": row[2] or 0.0,
                    "total_operations": row[3] or 0
                }
            else:
                return {
                    "date": date,
                    "avg_analysis_time": 0.0,
                    "avg_api_call_time": 0.0,
                    "avg_test_time": 0.0,
                    "total_operations": 0
                }
    
    def get_slowest_files(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Gibt langsamste Dateien zurück."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT file_path, AVG(duration_seconds) as avg_duration, COUNT(*) as operation_count
                FROM performance_entries
                WHERE timestamp >= ? AND file_path IS NOT NULL
                GROUP BY file_path
                ORDER BY avg_duration DESC
                LIMIT ?
            """, (since, limit))
            
            return [
                {
                    "file": row[0],
                    "avg_duration": row[1],
                    "operation_count": row[2]
                }
                for row in cursor.fetchall()
            ]
    
    def get_performance_trend(self, days: int = 7) -> List[Dict]:
        """Gibt Performance-Trend zurück."""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, avg_analysis_time, avg_api_call_time, avg_test_time, total_operations
                FROM daily_averages
                WHERE date >= ?
                ORDER BY date ASC
            """, (since,))
            
            return [
                {
                    "date": row[0],
                    "avg_analysis_time": row[1] or 0.0,
                    "avg_api_call_time": row[2] or 0.0,
                    "avg_test_time": row[3] or 0.0,
                    "total_operations": row[4] or 0
                }
                for row in cursor.fetchall()
            ]

# Singleton-Instanz
_performance_tracker = None

def get_performance_tracker() -> PerformanceTracker:
    """Gibt Singleton-Instanz zurück."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker

