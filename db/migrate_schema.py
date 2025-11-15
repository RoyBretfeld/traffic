from sqlalchemy import text
from db.core import ENGINE

def migrate_geo_cache_schema():
    """Fügt source und by_user Spalten zur geo_cache Tabelle hinzu."""
    with ENGINE.begin() as conn:
        # Prüfe ob Tabelle existiert
        cursor = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='geo_cache'"))
        if not cursor.fetchone():
            print("[MIGRATION] geo_cache Tabelle existiert nicht - Schema wird erstellt")
            return
        
        # Prüfe ob Spalten bereits existieren
        cursor = conn.execute(text("PRAGMA table_info(geo_cache)"))
        columns = [row[1] for row in cursor.fetchall()]
        
        # Füge source Spalte hinzu falls nicht vorhanden
        if 'source' not in columns:
            conn.execute(text("ALTER TABLE geo_cache ADD COLUMN source TEXT DEFAULT 'geocoded'"))
            print("[MIGRATION] Spalte 'source' hinzugefügt")
        
        # Füge by_user Spalte hinzu falls nicht vorhanden
        if 'by_user' not in columns:
            conn.execute(text("ALTER TABLE geo_cache ADD COLUMN by_user TEXT"))
            print("[MIGRATION] Spalte 'by_user' hinzugefügt")
        
        print("[MIGRATION] geo_cache Schema aktualisiert")
