"""Test DB-Verbindung"""
import sys
sys.path.insert(0, '.')

try:
    from db.core import ENGINE
    from sqlalchemy import text
    
    print("[TEST] Prüfe DB-Verbindung...")
    with ENGINE.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        result.fetchone()
    print("[OK] DB-Verbindung funktioniert!")
    
    # Prüfe Tabellen
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result.fetchall()]
    print(f"[OK] Tabellen gefunden: {len(tables)}")
    print(f"     {', '.join(tables[:5])}...")
    
except Exception as e:
    print(f"[FEHLER] DB-Verbindung: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

