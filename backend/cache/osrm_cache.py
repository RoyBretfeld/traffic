"""
OSRM-Cache (persistiert in SQLite) für Phase 2 Runbook.
"""
from __future__ import annotations
import sqlite3
import os
import time
import logging

logger = logging.getLogger(__name__)

# Konfiguration
DB_PATH = os.getenv("DB_PATH", "data/traffic.db")
TTL = int(os.getenv("ROUTING_CACHE_TTL_SEC", 86400))  # 24 Stunden


class OsrmCache:
    """Persistenter Cache für OSRM-Routing-Ergebnisse."""
    
    @staticmethod
    def _ensure_table():
        """Stellt sicher, dass die Cache-Tabelle existiert."""
        con = sqlite3.connect(DB_PATH)
        try:
            con.execute("""
                CREATE TABLE IF NOT EXISTS osrm_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    params_hash TEXT NOT NULL,
                    geometry_polyline6 TEXT NOT NULL,
                    distance_m INTEGER NOT NULL,
                    duration_s INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            con.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_osrm_cache_params_hash 
                ON osrm_cache(params_hash)
            """)
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_osrm_cache_created_at 
                ON osrm_cache(created_at)
            """)
            con.commit()
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der OSRM-Cache-Tabelle: {e}")
        finally:
            con.close()
    
    @staticmethod
    def get(key: str) -> dict | None:
        """
        Holt gecachtes Routing-Ergebnis.
        
        Args:
            key: params_hash (SHA256-Hash der Request-Parameter)
        
        Returns:
            Dict mit geometry_polyline6, distance_m, duration_s oder None
        """
        OsrmCache._ensure_table()
        
        con = sqlite3.connect(DB_PATH)
        try:
            cur = con.execute(
                "SELECT geometry_polyline6, distance_m, duration_s, strftime('%s', created_at) FROM osrm_cache WHERE params_hash=?",
                (key,)
            )
            row = cur.fetchone()
            
            if not row:
                return None
            
            geom, dist, dur, created = row
            created_ts = int(created)
            now_ts = int(time.time())
            
            # Prüfe TTL
            if (now_ts - created_ts) > TTL:
                # Abgelaufen → entfernen
                con.execute("DELETE FROM osrm_cache WHERE params_hash=?", (key,))
                con.commit()
                return None
            
            return {
                "geometry_polyline6": geom,
                "distance_m": dist,
                "duration_s": dur
            }
        except Exception as e:
            logger.error(f"Fehler beim Lesen aus OSRM-Cache: {e}")
            return None
        finally:
            con.close()
    
    @staticmethod
    def put(key: str, result: dict):
        """
        Speichert Routing-Ergebnis im Cache.
        
        Args:
            key: params_hash (SHA256-Hash der Request-Parameter)
            result: Dict mit geometry_polyline6, distance_m, duration_s
        """
        OsrmCache._ensure_table()
        
        con = sqlite3.connect(DB_PATH)
        try:
            con.execute(
                "INSERT OR REPLACE INTO osrm_cache(params_hash, geometry_polyline6, distance_m, duration_s) VALUES(?,?,?,?)",
                (key, result["geometry_polyline6"], result["distance_m"], result["duration_s"])
            )
            con.commit()
        except Exception as e:
            logger.error(f"Fehler beim Schreiben in OSRM-Cache: {e}")
        finally:
            con.close()
    
    @staticmethod
    def cleanup_old_entries():
        """Entfernt abgelaufene Cache-Einträge."""
        OsrmCache._ensure_table()
        
        con = sqlite3.connect(DB_PATH)
        try:
            now_ts = int(time.time())
            cutoff_ts = now_ts - TTL
            
            cur = con.execute(
                "DELETE FROM osrm_cache WHERE strftime('%s', created_at) < ?",
                (cutoff_ts,)
            )
            deleted = cur.rowcount
            con.commit()
            
            if deleted > 0:
                logger.info(f"OSRM-Cache: {deleted} abgelaufene Einträge entfernt")
            
            return deleted
        except Exception as e:
            logger.error(f"Fehler beim Cleanup des OSRM-Caches: {e}")
            return 0
        finally:
            con.close()

