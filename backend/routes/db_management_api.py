#!/usr/bin/env python3
"""
DB-Verwaltungs-API für den Admin-Bereich
Ermöglicht Batch-Geocoding und DB-Statistiken
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import sqlite3
import logging
from pydantic import BaseModel
from sqlalchemy import text

# Geocode wird jetzt asynchron verwendet (siehe batch_geocode_tourplan)
from repositories.geo_repo import upsert as geo_upsert
from backend.utils.safe_print import safe_print
from backend.routes.auth_api import require_admin

router = APIRouter()
logger = logging.getLogger(__name__)

# Tourenpläne-Verzeichnis
TOURPLAENE_DIR = Path("Tourplaene")
TOURPLAENE_DIR.mkdir(exist_ok=True)


class GeocodeFileRequest(BaseModel):
    filename: str


@router.post("/api/tourplan/batch-geocode")
async def batch_geocode_tourplan(file: UploadFile = File(...), session: dict = Depends(require_admin)):
    """
    Lädt einen Tourplan hoch, geocodiert alle Adressen und speichert sie in die DB.
    Trackt Cache-Hit-Rate (wie viele waren bereits im Cache vs. neu geocodiert).
    
    WICHTIG: Verwendet den korrekten Tourplan-Parser (parse_tour_plan_to_dict),
    nicht pd.read_csv, da Tourplan-CSVs eine spezielle Struktur mit Tour-Headern haben.
    """
    safe_print(f"[DB-API] Batch-Geocode Upload: {file.filename}")
    
    try:
        from backend.db.dao import geocache_get
        from repositories.geo_repo import get as geo_repo_get
        from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
        from common.normalize import normalize_address
        import tempfile
        import os
        
        # WICHTIG: Tourplaene-Verzeichnis ist READ-ONLY! Dateien sind bereits dort.
        # Prüfe zuerst, ob Datei bereits im Tourplaene-Verzeichnis existiert
        file_path = TOURPLAENE_DIR / file.filename
        
        if file_path.exists():
            # Datei existiert bereits - verwende sie direkt (kein Schreibzugriff nötig)
            safe_print(f"[DB-API] Datei bereits vorhanden, verwende: {file_path}")
            tmp_path = str(file_path.resolve())
        else:
            # Datei existiert nicht - speichere temporär (Parser benötigt Dateipfad)
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            safe_print(f"[DB-API] Datei temporär gespeichert: {tmp_path}")
        
        try:
            # Verwende den korrekten Tourplan-Parser (wie im Workflow)
            safe_print(f"[DB-API] Parse Tourplan mit parse_tour_plan_to_dict: {file.filename}")
            tour_data = parse_tour_plan_to_dict(tmp_path)
            
            # Extrahiere alle Kunden aus allen Touren
            all_customers = []
            for tour in tour_data.get('tours', []):
                for customer in tour.get('customers', []):
                    all_customers.append(customer)
            
            safe_print(f"[DB-API] {len(all_customers)} Kunden aus {len(tour_data.get('tours', []))} Touren extrahiert")
            
        except Exception as parse_error:
            safe_print(f"[DB-API] Parser-Fehler für {file.filename}: {parse_error}")
            import traceback
            safe_print(f"[DB-API] Traceback: {traceback.format_exc()}")
            return JSONResponse({
                "success": False,
                "error": f"Parser-Fehler: {str(parse_error)}",
                "total_customers": 0,
                "geocoded_count": 0,
                "cached_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "cache_hit_rate": 0.0
            }, status_code=400)
        finally:
            # Temporäre Datei löschen (nur wenn es eine temporäre Datei war, nicht die Original-Datei)
            if not file_path.exists() or str(tmp_path) != str(file_path.resolve()):
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except Exception:
                    pass
        
        # Prüfe ob Kunden gefunden wurden
        if not all_customers:
            safe_print(f"[DB-API] Warnung: Keine Kunden in {file.filename} gefunden")
            return JSONResponse({
                "success": True,
                "total_customers": 0,
                "geocoded_count": 0,
                "cached_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "cache_hit_rate": 0.0,
                "warning": "Keine Kunden gefunden"
            })
        
        # Statistiken
        stats = {
            "total_customers": len(all_customers),
            "geocoded_count": 0,  # Neu geocodiert
            "cached_count": 0,     # Bereits im Cache
            "skipped_count": 0,
            "error_count": 0,
            "failed_addresses": []  # Für manuelle Bearbeitung (Synonyme/Barkunden)
        }
        
        # Geocodiere jede Adresse ASYNCHRON (verhindert Blocking)
        import httpx
        from services.geocode_fill import _geocode_one
        
        async with httpx.AsyncClient(timeout=20.0) as geocode_client:
            for customer in all_customers:
                try:
                    name = customer.get('name', '').strip()
                    street = customer.get('street', '').strip()
                    postal_code = customer.get('postal_code', '').strip()
                    city = customer.get('city', '').strip()
                    
                    # Prüfe ob bereits Koordinaten vorhanden (aus Synonymen)
                    if customer.get('lat') and customer.get('lon'):
                        # Koordinaten bereits vorhanden - überspringe
                        stats["cached_count"] += 1
                        safe_print(f"[DB-API] Koordinaten bereits vorhanden (Synonym): {name}")
                        continue
                    
                    # Prüfe ob Adresse vollständig ist
                    if not street or not postal_code or not city:
                        stats["skipped_count"] += 1
                        safe_print(f"[DB-API] Unvollständige Adresse übersprungen: {name} ({street}, {postal_code} {city})")
                        continue
                    
                    # Adresse zusammenbauen (Parser liefert bereits normalisierte Adresse in 'address' Feld)
                    address = customer.get('address', '')
                    if not address:
                        # Fallback: Baue Adresse manuell
                        address = f"{street}, {postal_code} {city}"
                    
                    # Normalisiere Adresse für Cache-Suche (wichtig für Matching!)
                    address_normalized = normalize_address(address, customer_name=name, postal_code=postal_code)
                    
                    # Prüfe zuerst Cache (ohne Geocoding) - mit normalisierter Adresse
                    cached = geo_repo_get(address_normalized)
                    if cached and cached.get('lat') and cached.get('lon'):
                        # Bereits im Cache - Cache-Hit!
                        # WICHTIG: Speichere Kunde trotzdem in kunden-Tabelle (falls noch nicht vorhanden)
                        try:
                            from backend.db.dao import upsert_kunden, Kunde
                            kunde = Kunde(name=name, adresse=address, lat=cached['lat'], lon=cached['lon'])
                            upsert_kunden([kunde])
                        except Exception as kunde_error:
                            safe_print(f"[DB-API] Warnung: Kunde konnte nicht gespeichert werden (ignoriert): {kunde_error}")
                        
                        stats["cached_count"] += 1
                        safe_print(f"[DB-API] Cache-Hit: {name} @ {address}")
                        continue
                    
                    # Nicht im Cache - versuche ASYNCHRONE Geocodierung (mit originaler Adresse)
                    result = await _geocode_one(address, geocode_client, company_name=name)
                    
                    if result and result.get('lat') and result.get('lon'):
                        # Erfolgreich geocodiert
                        # WICHTIG: _geocode_one speichert bereits automatisch in DB über write_result
                        # Zusätzlich in geo_cache speichern (mit normalisierter Adresse für besseres Matching)
                        try:
                            geo_upsert(address_normalized, result['lat'], result['lon'])
                        except Exception as upsert_error:
                            # Ignoriere Fehler beim Upsert (kann bereits vorhanden sein)
                            safe_print(f"[DB-API] Warnung: geo_upsert fehlgeschlagen (ignoriert): {upsert_error}")
                        
                        # WICHTIG: Speichere Kunde auch in kunden-Tabelle
                        try:
                            from backend.db.dao import upsert_kunden, Kunde
                            kunde = Kunde(name=name, adresse=address, lat=result['lat'], lon=result['lon'])
                            upsert_kunden([kunde])
                        except Exception as kunde_error:
                            safe_print(f"[DB-API] Warnung: Kunde konnte nicht gespeichert werden (ignoriert): {kunde_error}")
                        
                        stats["geocoded_count"] += 1
                        safe_print(f"[DB-API] Neu geocodiert: {name} @ {address} -> ({result['lat']}, {result['lon']})")
                    else:
                        # Fehlgeschlagen - für manuelle Bearbeitung markieren (Synonyme/Barkunden)
                        stats["error_count"] += 1
                        stats["failed_addresses"].append({
                            "name": name,
                            "address": address,
                            "customer_number": customer.get('customer_number', '')
                        })
                        safe_print(f"[DB-API] Geocoding fehlgeschlagen (manuelle Bearbeitung nötig): {name} @ {address}")
                        
                except Exception as e:
                    stats["error_count"] += 1
                    safe_print(f"[DB-API] Fehler bei Kunde {customer.get('name', 'Unbekannt')}: {e}")
        
        # Cache-Hit-Rate berechnen
        total_processed = stats["cached_count"] + stats["geocoded_count"] + stats["error_count"]
        cache_hit_rate = (stats["cached_count"] / total_processed * 100) if total_processed > 0 else 0.0
        
        safe_print(f"[DB-API] Batch-Geocode abgeschlossen: {stats}")
        safe_print(f"[DB-API] Cache-Hit-Rate: {cache_hit_rate:.1f}% ({stats['cached_count']}/{total_processed})")
        
        return JSONResponse({
            "success": True,
            "total_customers": stats["total_customers"],
            "geocoded_count": stats["geocoded_count"],
            "cached_count": stats["cached_count"],
            "skipped_count": stats["skipped_count"],
            "error_count": stats["error_count"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "failed_addresses": stats["failed_addresses"][:50]  # Max. 50 für Response (Rest für manuelle Bearbeitung)
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Batch-Geocoding: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "total_customers": 0,
            "geocoded_count": 0,
            "cached_count": 0,
            "skipped_count": 0,
            "error_count": 0,
            "cache_hit_rate": 0.0
        }, status_code=500)


@router.get("/api/tourplan/list-legacy")
async def list_tourplans_legacy(session: dict = Depends(require_admin)):
    """
    LEGACY: Gibt eine Liste aller verfügbaren Tourenpläne zurück (nur CSV-Dateien).
    DEPRECATED: Verwenden Sie /api/tourplan/list stattdessen (kombiniert DB + Dateien).
    """
    try:
        tourplans = []
        
        for file_path in TOURPLAENE_DIR.glob("*.csv"):
            try:
                # Lese CSV
                df = pd.read_csv(file_path, sep=';', encoding='cp850', on_bad_lines='skip')
                
                # Zähle Kunden
                customer_count = len(df)
                
                # Zähle geocodierte Kunden (grobe Schätzung)
                geocoded_count = 0
                if 'Latitude' in df.columns and 'Longitude' in df.columns:
                    geocoded_count = df[['Latitude', 'Longitude']].notna().all(axis=1).sum()
                
                geocode_rate = round((geocoded_count / customer_count * 100) if customer_count > 0 else 0, 1)
                
                tourplans.append({
                    "filename": file_path.name,
                    "customer_count": customer_count,
                    "geocoded_count": geocoded_count,
                    "geocode_rate": geocode_rate
                })
                
            except Exception as e:
                safe_print(f"[DB-API] Fehler beim Lesen von {file_path.name}: {e}")
        
        return JSONResponse({
            "success": True,
            "tourplans": sorted(tourplans, key=lambda x: x['filename'])
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Tourenpläne: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tourplans": []
        }, status_code=500)


@router.post("/api/tourplan/geocode-file")
async def geocode_single_file(request: GeocodeFileRequest, session: dict = Depends(require_admin)):
    """
    Geocodiert einen einzelnen Tourplan (aus dem Tourplaene-Verzeichnis).
    """
    filename = request.filename
    file_path = TOURPLAENE_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Tourplan nicht gefunden: {filename}")
    
    safe_print(f"[DB-API] Geocode File: {filename}")
    
    try:
        # Lese CSV
        df = pd.read_csv(file_path, sep=';', encoding='cp850', on_bad_lines='skip')
        
        # Statistiken
        stats = {
            "total_customers": len(df),
            "geocoded_count": 0,
            "skipped_count": 0,
            "error_count": 0
        }
        
        # Geocodiere jede Adresse
        for idx, row in df.iterrows():
            try:
                name = str(row.get('Name', '')).strip()
                street = str(row.get('Straße', '')).strip()
                plz = str(row.get('PLZ', '')).strip()
                ort = str(row.get('Ort', '')).strip()
                
                if not all([name, street, plz, ort]):
                    stats["skipped_count"] += 1
                    continue
                
                # Adresse
                address = f"{street}, {plz} {ort}"
                
                # Versuche Geocodierung
                result = geocode_address(address)
                
                if result and result.get('lat') and result.get('lon'):
                    # Speichere in DB
                    geo_upsert(address, result['lat'], result['lon'])
                    stats["geocoded_count"] += 1
                else:
                    stats["error_count"] += 1
                    
            except Exception as e:
                stats["error_count"] += 1
                safe_print(f"[DB-API] Fehler bei Zeile {idx}: {e}")
        
        safe_print(f"[DB-API] Geocode File abgeschlossen: {stats}")
        
        return JSONResponse({
            "success": True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Fehler bei File-Geocoding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/db/info")
async def get_db_info(session: dict = Depends(require_admin)):
    """
    Gibt DB-Info zurück (Pfad, Größe, Anzahl Tabellen, Schema-Version).
    """
    try:
        from pathlib import Path
        from db.core import ENGINE
        from settings import SETTINGS
        import os
        import re
        
        # Extrahiere DB-Pfad aus database_url (z.B. "sqlite:///app.db" -> "app.db")
        db_path = None
        if "sqlite" in SETTINGS.database_url.lower():
            # SQLite URL-Format: sqlite:///path/to/db.db oder sqlite:///:memory:
            match = re.search(r'sqlite:///(.+?)(?:\?|$)', SETTINGS.database_url)
            if match:
                db_path_str = match.group(1)
                if db_path_str != ":memory:":
                    db_path = Path(db_path_str)
        
        if not db_path:
            # Fallback: Versuche Standard-Pfade
            for default_path in ["app.db", "traffic.db", "db/app.db"]:
                test_path = Path(default_path)
                if test_path.exists():
                    db_path = test_path
                    break
            
            if not db_path:
                db_path = Path("app.db")  # Default
        
        # DB-Größe
        size_bytes = 0
        if db_path.exists():
            size_bytes = os.path.getsize(db_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        
        # Anzahl Tabellen
        table_count = 0
        table_names = []
        try:
            with ENGINE.connect() as conn:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
                table_names = [row[0] for row in result.fetchall()]
                table_count = len(table_names)
        except Exception as e:
            logger.warning(f"Fehler beim Zählen der Tabellen: {e}")
        
        # Schema-Version (aus app_settings, falls vorhanden)
        schema_version = "N/A"
        try:
            with ENGINE.connect() as conn:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='app_settings'
                """))
                if result.fetchone():
                    result = conn.execute(text("""
                        SELECT value FROM app_settings 
                        WHERE key = 'schema_version'
                    """))
                    row = result.fetchone()
                    if row:
                        schema_version = row[0]
        except Exception:
            pass
        
        return JSONResponse({
            "success": True,
            "db_path": str(db_path),
            "db_name": db_path.name,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "table_count": table_count,
            "table_names": table_names,
            "schema_version": schema_version
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der DB-Info: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/api/db/tables")
async def get_db_tables(session: dict = Depends(require_admin)):
    """
    Gibt eine Liste aller Tabellen mit Beschreibungen und Row-Counts zurück.
    """
    try:
        from db.core import ENGINE
        
        # Tabellen-Beschreibungen (aus Dokumentation)
        table_descriptions = {
            "tours": "Alle Touren (Plan + Ergebnis)",
            "tour_stops": "Stops pro Tour",
            "tour_events": "Ereignisse/Probleme während Touren",
            "stats_daily": "Aggregierte Tagesstatistiken",
            "system_logs": "System- und Fehlerlogs",
            "app_settings": "Globale Einstellungen",
            "route_embeddings": "KI-Embeddings für Touren",
            "touren": "Touren (Legacy-Tabelle)",
            "kunden": "Kunden (Legacy-Tabelle)",
            "geo_cache": "Geocodierte Adressen (Cache)",
            "geo_fail": "Fehlgeschlagene Geocodierungen"
        }
        
        tables = []
        
        try:
            with ENGINE.connect() as conn:
                # Hole alle Tabellen
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
                
                rows = result.fetchall()
                logger.info(f"[DB-API] Gefundene Tabellen: {len(rows)}")
                
                # Debug: Logge erste Tabellennamen
                if rows:
                    logger.info(f"[DB-API] Erste Tabellen: {[r[0] for r in rows[:5]]}")
                else:
                    logger.warning("[DB-API] Keine Tabellen gefunden in sqlite_master")
                
                for row in rows:
                    table_name = row[0]
                    
                    # Row-Count (mit besserer Fehlerbehandlung)
                    row_count = 0
                    try:
                        # SQLite verwendet keine Backticks, sondern Anführungszeichen oder direkt den Namen
                        # Für Sicherheit: Escapen des Tabellennamens
                        safe_table_name = table_name.replace('"', '""')  # Escape für SQLite
                        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{safe_table_name}"'))
                        row_count = count_result.scalar() or 0
                    except Exception as count_error:
                        logger.warning(f"Fehler beim Zählen von {table_name}: {count_error}")
                        row_count = -1  # -1 = Fehler beim Zählen
                    
                    # Beschreibung
                    description = table_descriptions.get(table_name, "Keine Beschreibung verfügbar")
                    
                    tables.append({
                        "name": table_name,
                        "description": description,
                        "row_count": row_count
                    })
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Tabellen: {e}", exc_info=True)
        
        return JSONResponse({
            "success": True,
            "tables": tables
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tabellenliste: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tables": []
        }, status_code=500)


@router.get("/api/db/table/{table_name}")
async def get_table_details(table_name: str, session: dict = Depends(require_admin)):
    """
    Gibt Details zu einer Tabelle zurück (Spalten, Indizes, Vorschau).
    """
    try:
        from db.core import ENGINE
        
        # Prüfe ob Tabelle existiert
        with ENGINE.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name = :table_name
            """), {"table_name": table_name})
            
            if not result.fetchone():
                raise HTTPException(status_code=404, detail=f"Tabelle '{table_name}' nicht gefunden")
            
            # Spalten-Info
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = []
            for row in result.fetchall():
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "default": row[4],
                    "primary_key": bool(row[5])
                })
            
            # Indizes
            result = conn.execute(text(f"PRAGMA index_list({table_name})"))
            indexes = []
            for row in result.fetchall():
                index_name = row[1]
                # Hole Index-Spalten
                idx_result = conn.execute(text(f"PRAGMA index_info({index_name})"))
                index_columns = [r[2] for r in idx_result.fetchall()]
                indexes.append({
                    "name": index_name,
                    "columns": index_columns,
                    "unique": bool(row[2])
                })
            
            # Vorschau (erste 10 Zeilen)
            preview = []
            try:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 10"))
                rows = result.fetchall()
                column_names = [desc[0] for desc in result.description] if result.description else []
                
                for row in rows:
                    preview.append(dict(zip(column_names, row)))
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Vorschau: {e}")
        
        return JSONResponse({
            "success": True,
            "table_name": table_name,
            "columns": columns,
            "indexes": indexes,
            "preview": preview
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tabellen-Details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/db/stats")
async def get_db_stats(session: dict = Depends(require_admin)):
    """
    Gibt DB-Statistiken zurück (Geocodes, Touren, Events, Embeddings).
    """
    try:
        from sqlalchemy import text
        from db.core import ENGINE
        
        stats = {
            "total_customers": 0,
            "geocoded_customers": 0,
            "missing_geocodes": 0,
            "geocode_rate": 0,
            "tours_count": 0,
            "stops_count": 0,
            "events_count": 0,
            "embeddings_count": 0
        }
        
        try:
            with ENGINE.connect() as conn:
                # Zähle Einträge in geo_cache (gecachte Geocodes)
                result = conn.execute(text("SELECT COUNT(*) FROM geo_cache"))
                stats["geocoded_customers"] = result.scalar() or 0
                
                # Zähle fehlgeschlagene Geocodes in geo_fail
                try:
                    result = conn.execute(text("SELECT COUNT(*) FROM geo_fail"))
                    failed_count = result.scalar() or 0
                except Exception:
                    failed_count = 0
                
                # Total = Erfolgreiche + Fehlgeschlagene
                stats["total_customers"] = stats["geocoded_customers"] + failed_count
                stats["missing_geocodes"] = failed_count
                
                # Berechne Rate
                if stats["total_customers"] > 0:
                    stats["geocode_rate"] = round((stats["geocoded_customers"] / stats["total_customers"]) * 100, 1)
                
                # Tour-Statistiken (falls Tabellen existieren)
                try:
                    # Prüfe ob touren-Tabelle existiert
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='touren'
                    """))
                    if result.fetchone():
                        # Zähle Touren
                        result = conn.execute(text("SELECT COUNT(*) FROM touren"))
                        stats["tours_count"] = result.scalar() or 0
                        
                        # Zähle Tour-Stops (aus kunden_ids JSON-Array)
                        # Vereinfacht: Zähle alle Einträge in touren mit nicht-leeren kunden_ids
                        result = conn.execute(text("""
                            SELECT COUNT(*) FROM touren 
                            WHERE kunden_ids IS NOT NULL AND kunden_ids != '' AND kunden_ids != '[]'
                        """))
                        stats["stops_count"] = result.scalar() or 0
                except Exception as tour_error:
                    logger.debug(f"Tour-Statistiken nicht verfügbar: {tour_error}")
                
                # Tour-Events (falls Tabelle existiert)
                try:
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='tour_events'
                    """))
                    if result.fetchone():
                        result = conn.execute(text("SELECT COUNT(*) FROM tour_events"))
                        stats["events_count"] = result.scalar() or 0
                except Exception:
                    pass
                
                # Route-Embeddings (falls Tabelle existiert)
                try:
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='route_embeddings'
                    """))
                    if result.fetchone():
                        result = conn.execute(text("SELECT COUNT(*) FROM route_embeddings"))
                        stats["embeddings_count"] = result.scalar() or 0
                except Exception:
                    pass
                
        except Exception as db_error:
            safe_print(f"[DB-API] DB-Fehler: {db_error}")
            # Versuche alternatives Schema (traffic.db customers)
            try:
                import sqlite3
                db_path = Path("traffic.db")
                if db_path.exists():
                    conn_sqlite = sqlite3.connect(db_path)
                    cursor = conn_sqlite.cursor()
                    
                    # Zähle Kunden in traffic.db
                    cursor.execute("SELECT COUNT(*) FROM customers")
                    stats["total_customers"] = cursor.fetchone()[0]
                    
                    # Zähle mit Koordinaten
                    cursor.execute("SELECT COUNT(*) FROM customers WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
                    stats["geocoded_customers"] = cursor.fetchone()[0]
                    
                    stats["missing_geocodes"] = stats["total_customers"] - stats["geocoded_customers"]
                    
                    if stats["total_customers"] > 0:
                        stats["geocode_rate"] = round((stats["geocoded_customers"] / stats["total_customers"]) * 100, 1)
                    
                    conn_sqlite.close()
            except Exception as fallback_error:
                safe_print(f"[DB-API] Fallback-Fehler: {fallback_error}")
        
        return JSONResponse({
            "success": True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der DB-Statistiken: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "total_customers": 0,
            "geocoded_customers": 0,
            "missing_geocodes": 0,
            "geocode_rate": 0,
            "tours_count": 0,
            "stops_count": 0,
            "events_count": 0,
            "embeddings_count": 0
        }, status_code=500)

