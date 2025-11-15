"""
Direktes Script zum Erstellen der stats_monthly Tabelle.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.core import ENGINE
from sqlalchemy import text

def create_stats_monthly():
    """Erstellt die stats_monthly Tabelle direkt."""
    try:
        with ENGINE.begin() as conn:
            # Prüfe ob Tabelle bereits existiert
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='stats_monthly'
            """))
            if result.fetchone():
                print("[OK] Tabelle stats_monthly existiert bereits")
                return True
            
            # Erstelle Tabelle
            conn.execute(text("""
                CREATE TABLE stats_monthly (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,
                    tours_count INTEGER DEFAULT 0,
                    stops_count INTEGER DEFAULT 0,
                    total_km REAL DEFAULT 0.0,
                    avg_stops_per_tour REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(month)
                )
            """))
            
            # Erstelle Index
            conn.execute(text("""
                CREATE INDEX idx_stats_monthly_month ON stats_monthly(month)
            """))
            
            print("[OK] Tabelle stats_monthly erfolgreich erstellt")
            return True
    except Exception as e:
        print(f"[ERROR] Fehler beim Erstellen der Tabelle: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_stats_monthly()
    sys.exit(0 if success else 1)

