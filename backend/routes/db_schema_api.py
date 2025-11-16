"""
DB-Schema-API für Admin-Bereich.
Ermöglicht Schema-Informationen aller Datenbanken abzurufen (nur lesend).
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Dict, Optional
import sqlite3
import logging
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter()
logger = logging.getLogger(__name__)

# Bekannte Datenbanken im Projekt
KNOWN_DATABASES = [
    {"name": "traffic.db", "path": "data/traffic.db", "description": "Haupt-Datenbank (Touren, Kunden, Geo-Cache)"},
    {"name": "code_fixes_cost.db", "path": "data/code_fixes_cost.db", "description": "KI-Kosten-Tracking"},
    {"name": "code_fixes_performance.db", "path": "data/code_fixes_performance.db", "description": "Performance-Tracking"},
    {"name": "llm_monitoring.db", "path": "data/llm_monitoring.db", "description": "LLM-Monitoring"},
    {"name": "customers.db", "path": "data/customers.db", "description": "Kunden-Datenbank"},
    {"name": "address_corrections.sqlite3", "path": "data/address_corrections.sqlite3", "description": "Adress-Korrekturen"},
]


def get_db_size(db_path: Path) -> Optional[int]:
    """Gibt Größe der Datenbank in Bytes zurück."""
    try:
        if db_path.exists():
            return db_path.stat().st_size
    except Exception as e:
        logger.debug(f"Fehler beim Ermitteln der DB-Größe für {db_path}: {e}")
    return None


def get_db_status(db_path: Path) -> Dict:
    """Prüft Status einer Datenbank (online/offline, Größe)."""
    status = {
        "path": str(db_path),
        "exists": db_path.exists(),
        "status": "offline",
        "size_bytes": None,
        "size_mb": None,
        "error": None
    }
    
    if not db_path.exists():
        status["error"] = "Datenbank-Datei nicht gefunden"
        return status
    
    # Prüfe Größe
    size = get_db_size(db_path)
    if size is not None:
        status["size_bytes"] = size
        status["size_mb"] = round(size / (1024 * 1024), 2)
    
    # Prüfe ob DB erreichbar ist
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        status["status"] = "online"
    except Exception as e:
        status["status"] = "offline"
        status["error"] = str(e)
    
    return status


def get_table_info(conn: sqlite3.Connection, table_name: str) -> Dict:
    """Holt Schema-Informationen für eine Tabelle."""
    try:
        # Spalten-Informationen
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default_value": row[4],
                "pk": bool(row[5])
            })
        
        # Indizes
        cursor = conn.execute(f"PRAGMA index_list({table_name})")
        indexes = []
        for idx_row in cursor.fetchall():
            idx_name = idx_row[1]
            cursor_idx = conn.execute(f"PRAGMA index_info({idx_name})")
            idx_columns = [col[2] for col in cursor_idx.fetchall()]
            indexes.append({
                "name": idx_name,
                "unique": bool(idx_row[2]),
                "columns": idx_columns
            })
        
        # Anzahl Zeilen (optional, kann bei großen Tabellen langsam sein)
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
        except Exception:
            row_count = None
        
        return {
            "name": table_name,
            "columns": columns,
            "column_count": len(columns),
            "indexes": indexes,
            "index_count": len(indexes),
            "row_count": row_count
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tabellen-Info für {table_name}: {e}")
        return {
            "name": table_name,
            "error": str(e)
        }


@router.get("/api/db/list")
async def list_databases():
    """
    Gibt Liste aller verfügbaren Datenbanken zurück.
    """
    databases = []
    
    for db_info in KNOWN_DATABASES:
        db_path = Path(db_info["path"])
        status = get_db_status(db_path)
        
        databases.append({
            "name": db_info["name"],
            "description": db_info["description"],
            **status
        })
    
    return JSONResponse({
        "success": True,
        "databases": databases,
        "total": len(databases)
    })


@router.get("/api/db/schemas")
async def get_schemas(
    dbs: Optional[str] = Query(None, description="Komma-getrennte Liste von DB-Namen (z.B. 'traffic.db,code_fixes_cost.db')")
):
    """
    Gibt Schema-Informationen für angegebene Datenbanken zurück.
    
    Args:
        dbs: Komma-getrennte Liste von DB-Namen. Wenn nicht angegeben, werden alle verfügbaren DBs zurückgegeben.
    """
    # Parse DB-Liste
    if dbs:
        requested_dbs = [db.strip() for db in dbs.split(",")]
    else:
        # Alle verfügbaren DBs
        requested_dbs = [db["name"] for db in KNOWN_DATABASES]
    
    schemas = {}
    
    for db_name in requested_dbs:
        # Finde DB-Info
        db_info = next((db for db in KNOWN_DATABASES if db["name"] == db_name), None)
        if not db_info:
            schemas[db_name] = {
                "error": f"Datenbank '{db_name}' nicht gefunden"
            }
            continue
        
        db_path = Path(db_info["path"])
        if not db_path.exists():
            schemas[db_name] = {
                "error": "Datenbank-Datei nicht gefunden",
                "path": str(db_path)
            }
            continue
        
        # Status
        status = get_db_status(db_path)
        
        # Tabellen-Liste
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            table_names = [row[0] for row in cursor.fetchall()]
            
            # Schema-Informationen für jede Tabelle
            tables = []
            for table_name in table_names:
                table_info = get_table_info(conn, table_name)
                tables.append(table_info)
            
            conn.close()
            
            schemas[db_name] = {
                "name": db_name,
                "description": db_info["description"],
                "path": str(db_path),
                "status": status["status"],
                "size_bytes": status["size_bytes"],
                "size_mb": status["size_mb"],
                "tables": tables,
                "table_count": len(tables)
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Schemas für {db_name}: {e}")
            schemas[db_name] = {
                "name": db_name,
                "error": str(e),
                "path": str(db_path)
            }
    
    return JSONResponse({
        "success": True,
        "schemas": schemas,
        "requested": requested_dbs,
        "returned": len(schemas)
    })

