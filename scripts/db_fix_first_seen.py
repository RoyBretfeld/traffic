import sqlite3
import sys
import os

def fix_geo_fail_schema(db_path):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Add 'first_seen' column if it doesn't exist
        cur.execute("PRAGMA table_info(geo_fail)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'first_seen' not in columns:
            cur.execute("ALTER TABLE geo_fail ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Spalte 'first_seen' zu geo_fail hinzugefügt.")
        else:
            print("Spalte 'first_seen' existiert bereits in geo_fail.")

        # Add 'last_seen' column if it doesn't exist
        if 'last_seen' not in columns:
            cur.execute("ALTER TABLE geo_fail ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Spalte 'last_seen' zu geo_fail hinzugefügt.")
        else:
            print("Spalte 'last_seen' existiert bereits in geo_fail.")

        # Create index on 'first_seen' if it doesn't exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_geo_fail_first_seen'")
        if cur.fetchone() is None:
            cur.execute("CREATE INDEX idx_geo_fail_first_seen ON geo_fail(first_seen)")
            print("Index 'idx_geo_fail_first_seen' erstellt.")
        else:
            print("Index 'idx_geo_fail_first_seen' existiert bereits.")

        conn.commit()
        print(f"Datenbankschema für geo_fail in {db_path} erfolgreich repariert/verifiziert.")

    except sqlite3.OperationalError as e:
        print(f"Datenbankfehler: {e}")
        if "no such table: geo_fail" in str(e):
            print("Die Tabelle 'geo_fail' existiert nicht. Bitte stellen Sie sicher, dass das Hauptschema angewendet wurde.")
            print("Sie können versuchen, die Datenbankdatei 'app.db' zu löschen (wenn keine Produktionsdaten vorhanden sind) und den Server neu zu starten, um das Schema neu zu erstellen.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python db_fix_first_seen.py <path_to_db_file>")
        sys.exit(1)
    
    db_file = sys.argv[1]
    if not os.path.exists(db_file):
        print(f"Fehler: Datenbankdatei nicht gefunden unter {db_file}")
        sys.exit(1)

    fix_geo_fail_schema(db_file)
