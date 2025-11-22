"""
API-Endpunkte für Tour-Import & Vorladen
Batch-Import von Tourplänen mit automatischem Geocoding
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import logging
import zipfile
import tempfile
import shutil
import json

from db.core import ENGINE
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/import", tags=["tour-import"])


# ==========================================
# Pydantic Models
# ==========================================

class ImportBatchRequest(BaseModel):
    name: str
    source: Optional[str] = None
    created_by: Optional[str] = None


class ImportBatchResponse(BaseModel):
    id: int
    name: str
    source: Optional[str]
    created_by: Optional[str]
    created_at: str
    status: str
    total_tours: int
    total_stops: int
    geocoded_ok: int
    geocoded_failed: int
    geocoded_pending: int


class ImportStatsResponse(BaseModel):
    total_customers: int
    customers_geocoded_ok: int
    customers_geocoded_failed: int
    customers_geocoded_pending: int
    total_stops: int
    stops_geocoded_ok: int
    stops_geocoded_failed: int
    stops_geocoded_pending: int
    open_geocoding_jobs: int


# ==========================================
# Helper Functions
# ==========================================

def apply_migration_020():
    """Wendet Migration 020 an (Import-Batches Tabellen)"""
    migration_file = Path(__file__).parent.parent.parent / "db" / "migrations" / "020_import_batches.sql"
    if not migration_file.exists():
        logger.warning("Migration 020 nicht gefunden")
        return False
    
    try:
        with ENGINE.begin() as conn:
            sql = migration_file.read_text(encoding="utf-8")
            statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
            
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    # Tabellen/Indizes können bereits existieren
                    logger.debug(f"Migration 020 Statement ignoriert (möglicherweise bereits vorhanden): {e}")
        
        logger.info("Migration 020 angewendet: Import-Batches Tabellen")
        return True
    except Exception as e:
        logger.error(f"Migration 020 fehlgeschlagen: {e}")
        return False


# Stelle sicher, dass Migration 020 angewendet wurde
try:
    apply_migration_020()
except Exception as e:
    logger.warning(f"Migration 020 konnte nicht automatisch angewendet werden: {e}")


# ==========================================
# API Endpoints
# ==========================================

@router.post("/batch", response_model=ImportBatchResponse)
async def create_import_batch(request: ImportBatchRequest):
    """
    Erstellt einen neuen Import-Batch
    """
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO import_batches (name, source, created_by, status)
                    VALUES (:name, :source, :created_by, 'pending')
                    RETURNING id, name, source, created_by, created_at, status, 
                              total_tours, total_stops, geocoded_ok, geocoded_failed, geocoded_pending
                """),
                {
                    "name": request.name,
                    "source": request.source or "Manueller Upload",
                    "created_by": request.created_by or "admin"
                }
            )
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=500, detail="Batch konnte nicht erstellt werden")
            
            return ImportBatchResponse(
                id=row[0],
                name=row[1],
                source=row[2],
                created_by=row[3],
                created_at=row[4].isoformat() if row[4] else datetime.now().isoformat(),
                status=row[5],
                total_tours=row[6] or 0,
                total_stops=row[7] or 0,
                geocoded_ok=row[8] or 0,
                geocoded_failed=row[9] or 0,
                geocoded_pending=row[10] or 0
            )
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Import-Batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches", response_model=List[ImportBatchResponse])
async def list_import_batches(limit: int = 50):
    """
    Listet alle Import-Batches (neueste zuerst)
    """
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("""
                    SELECT id, name, source, created_by, created_at, status,
                           total_tours, total_stops, geocoded_ok, geocoded_failed, geocoded_pending
                    FROM import_batches
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            
            batches = []
            for row in result:
                batches.append(ImportBatchResponse(
                    id=row[0],
                    name=row[1],
                    source=row[2],
                    created_by=row[3],
                    created_at=row[4].isoformat() if row[4] else "",
                    status=row[5],
                    total_tours=row[6] or 0,
                    total_stops=row[7] or 0,
                    geocoded_ok=row[8] or 0,
                    geocoded_failed=row[9] or 0,
                    geocoded_pending=row[10] or 0
                ))
            
            return batches
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Import-Batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}", response_model=ImportBatchResponse)
async def get_import_batch(batch_id: int):
    """
    Ruft einen spezifischen Import-Batch ab
    """
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("""
                    SELECT id, name, source, created_by, created_at, status,
                           total_tours, total_stops, geocoded_ok, geocoded_failed, geocoded_pending
                    FROM import_batches
                    WHERE id = :batch_id
                """),
                {"batch_id": batch_id}
            )
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Batch nicht gefunden")
            
            return ImportBatchResponse(
                id=row[0],
                name=row[1],
                source=row[2],
                created_by=row[3],
                created_at=row[4].isoformat() if row[4] else "",
                status=row[5],
                total_tours=row[6] or 0,
                total_stops=row[7] or 0,
                geocoded_ok=row[8] or 0,
                geocoded_failed=row[9] or 0,
                geocoded_pending=row[10] or 0
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Import-Batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ImportStatsResponse)
async def get_import_stats():
    """
    Ruft globale Import-Statistiken ab (Kunden, Stops, Geocoding-Status)
    """
    try:
        with ENGINE.begin() as conn:
            # Prüfe ob customers Tabelle existiert
            try:
                # Kunden-Statistiken
                customers_result = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN geocode_status = 'ok' THEN 1 ELSE 0 END) as ok,
                            SUM(CASE WHEN geocode_status = 'failed' THEN 1 ELSE 0 END) as failed,
                            SUM(CASE WHEN geocode_status = 'pending' OR geocode_status IS NULL THEN 1 ELSE 0 END) as pending
                        FROM customers
                    """)
                )
                customers_row = customers_result.fetchone()
                
                total_customers = customers_row[0] or 0 if customers_row else 0
                customers_ok = customers_row[1] or 0 if customers_row else 0
                customers_failed = customers_row[2] or 0 if customers_row else 0
                customers_pending = customers_row[3] or 0 if customers_row else 0
            except Exception as e:
                logger.warning(f"Kunden-Statistiken konnten nicht abgerufen werden: {e}")
                total_customers = 0
                customers_ok = 0
                customers_failed = 0
                customers_pending = 0
            
            # Tour-Stops Statistiken (aus tour_stops Tabelle, falls vorhanden)
            try:
                stops_result = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 ELSE 0 END) as ok,
                            SUM(CASE WHEN lat IS NULL OR lon IS NULL THEN 1 ELSE 0 END) as pending
                        FROM tour_stops
                    """)
                )
                stops_row = stops_result.fetchone()
                
                total_stops = stops_row[0] or 0 if stops_row else 0
                stops_ok = stops_row[1] or 0 if stops_row else 0
                stops_pending = stops_row[2] or 0 if stops_row else 0
                stops_failed = 0  # tour_stops hat kein failed-Flag
            except Exception as e:
                logger.warning(f"Tour-Stops Statistiken konnten nicht abgerufen werden: {e}")
                # Fallback: Verwende customers als Basis für Stops
                total_stops = total_customers
                stops_ok = customers_ok
                stops_failed = customers_failed
                stops_pending = customers_pending
            
            # Offene Geocoding-Jobs (pending Kunden)
            open_jobs = customers_pending
            
            return ImportStatsResponse(
                total_customers=total_customers,
                customers_geocoded_ok=customers_ok,
                customers_geocoded_failed=customers_failed,
                customers_geocoded_pending=customers_pending,
                total_stops=total_stops,
                stops_geocoded_ok=stops_ok,
                stops_geocoded_failed=stops_failed,
                stops_geocoded_pending=stops_pending,
                open_geocoding_jobs=open_jobs
            )
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Import-Statistiken: {e}")
        # Fallback: Leere Statistiken zurückgeben
        return ImportStatsResponse(
            total_customers=0,
            customers_geocoded_ok=0,
            customers_geocoded_failed=0,
            customers_geocoded_pending=0,
            total_stops=0,
            stops_geocoded_ok=0,
            stops_geocoded_failed=0,
            stops_geocoded_pending=0,
            open_geocoding_jobs=0
        )


@router.post("/upload")
async def upload_tour_files(
    files: List[UploadFile] = File(...),
    batch_id: Optional[int] = Form(None),
    name: Optional[str] = Form(None),
    source: Optional[str] = Form(None)
):
    """
    Lädt Tour-Dateien hoch (CSV oder ZIP mit mehreren CSVs)
    Parst CSV, extrahiert Kunden, speichert in DB und startet Geocoding
    """
    import tempfile
    import zipfile
    from pathlib import Path
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    from datetime import datetime
    
    try:
        # Erstelle Batch, falls nicht vorhanden
        if not batch_id:
            batch_name = name or f"Import_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            batch_request = ImportBatchRequest(
                name=batch_name,
                source=source or "Manueller Upload",
                created_by="admin"
            )
            batch_response = await create_import_batch(batch_request)
            batch_id = batch_response.id
            logger.info(f"[IMPORT] Neuer Batch erstellt: {batch_id} ({batch_name})")
        
        total_tours = 0
        total_stops = 0
        total_customers = 0
        processed_files = []
        
        # Verarbeite jede Datei
        for file in files:
            try:
                # Temporäre Datei speichern
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_path = Path(tmp_file.name)
                
                logger.info(f"[IMPORT] Verarbeite Datei: {file.filename}")
                
                # Prüfe ob ZIP
                if tmp_path.suffix.lower() == '.zip':
                    # ZIP entpacken und alle CSVs verarbeiten
                    with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                        for zip_info in zip_ref.namelist():
                            if zip_info.lower().endswith('.csv'):
                                # CSV aus ZIP extrahieren
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as csv_tmp:
                                    csv_tmp.write(zip_ref.read(zip_info))
                                    csv_path = Path(csv_tmp.name)
                                
                                # CSV parsen
                                tours, customers = await _process_csv_file(csv_path, batch_id)
                                total_tours += tours
                                total_customers += customers
                                
                                # Temporäre CSV löschen
                                csv_path.unlink()
                else:
                    # Direkt CSV parsen
                    tours, customers = await _process_csv_file(tmp_path, batch_id)
                    total_tours += tours
                    total_customers += customers
                
                # Temporäre Datei löschen
                tmp_path.unlink()
                
                processed_files.append({
                    "filename": file.filename,
                    "tours": tours,
                    "customers": customers
                })
                
            except Exception as e:
                logger.error(f"[IMPORT] Fehler bei Datei {file.filename}: {e}", exc_info=True)
                processed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        # Batch-Statistiken aktualisieren
        with ENGINE.begin() as conn:
            conn.execute(
                text("""
                    UPDATE import_batches
                    SET total_tours = :tours,
                        total_stops = :stops,
                        geocoded_pending = :customers,
                        status = 'running'
                    WHERE id = :batch_id
                """),
                {
                    "batch_id": batch_id,
                    "tours": total_tours,
                    "stops": total_stops,
                    "customers": total_customers
                }
            )
        
        logger.info(f"[IMPORT] Batch {batch_id}: {total_tours} Touren, {total_customers} Kunden verarbeitet")
        
        return JSONResponse({
            "success": True,
            "message": f"{len(processed_files)} Dateien verarbeitet",
            "batch_id": batch_id,
            "total_tours": total_tours,
            "total_customers": total_customers,
            "files": processed_files
        })
        
    except Exception as e:
        logger.error(f"[IMPORT] Fehler beim Upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der Dateien: {str(e)}")


async def _process_csv_file(csv_path: Path, batch_id: int) -> tuple[int, int]:
    """
    Verarbeitet eine CSV-Datei: Parst, extrahiert Kunden, speichert in DB.
    
    Returns:
        (anzahl_touren, anzahl_kunden)
    """
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    
    # CSV parsen
    parsed_data = parse_tour_plan_to_dict(str(csv_path))
    tours_data = parsed_data.get('tours', [])
    
    tours_count = 0
    customers_count = 0
    customers_seen = set()  # Verhindere Duplikate
    
    with ENGINE.begin() as conn:
        for tour_data in tours_data:
            tour_id = tour_data.get('tour_id') or tour_data.get('name', 'UNKNOWN')
            is_bar = tour_data.get('is_bar', False)
            customers_list = tour_data.get('customers', [])
            
            # Tour in DB speichern (touren Tabelle)
            # Prüfe ob touren Tabelle existiert und welches Schema sie hat
            try:
                # Versuche mit datum (falls vorhanden)
                from datetime import date
                today = date.today().isoformat()
                
                # Prüfe ob Tabelle existiert
                table_check = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='touren'")
                ).fetchone()
                
                if table_check:
                    # Tabelle existiert - speichere Tour
                    conn.execute(
                        text("""
                            INSERT OR IGNORE INTO touren (tour_id, datum, kunden_ids)
                            VALUES (:tour_id, :datum, :kunden_ids)
                        """),
                        {
                            "tour_id": tour_id,
                            "datum": today,
                            "kunden_ids": json.dumps([c.get('customer_number') for c in customers_list])
                        }
                    )
                    tours_count += 1
                else:
                    logger.warning(f"[IMPORT] Tabelle 'touren' existiert nicht - Tour wird nicht gespeichert")
            except Exception as e:
                logger.warning(f"[IMPORT] Fehler beim Speichern der Tour {tour_id}: {e}")
            
            # Kunden extrahieren und speichern
            for customer in customers_list:
                customer_number = customer.get('customer_number', '')
                name = customer.get('name', '')
                street = customer.get('street', '')
                postal_code = customer.get('postal_code', '')
                city = customer.get('city', '')
                
                # Eindeutiger Key für Duplikat-Erkennung
                customer_key = f"{customer_number}|{name}|{street}|{city}".lower()
                if customer_key in customers_seen:
                    continue
                customers_seen.add(customer_key)
                
                # Kunde in customers Tabelle speichern
                try:
                    conn.execute(
                        text("""
                            INSERT OR REPLACE INTO customers 
                            (external_id, name, street, zip, city, country, geocode_status, last_used_at)
                            VALUES (:external_id, :name, :street, :zip, :city, :country, 'pending', CURRENT_TIMESTAMP)
                        """),
                        {
                            "external_id": customer_number or None,
                            "name": name,
                            "street": street,
                            "zip": postal_code,
                            "city": city,
                            "country": "Deutschland"
                        }
                    )
                    customers_count += 1
                except Exception as e:
                    logger.warning(f"[IMPORT] Fehler beim Speichern des Kunden {name}: {e}")
    
    return tours_count, customers_count


@router.post("/batch/{batch_id}/start")
async def start_import_batch(batch_id: int, background_tasks: BackgroundTasks):
    """
    Startet die Verarbeitung eines Import-Batches (Geocoding im Hintergrund)
    """
    from backend.services.geocoding_worker import process_batch_geocoding
    
    try:
        # Prüfe ob Batch existiert
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("SELECT id, status FROM import_batches WHERE id = :batch_id"),
                {"batch_id": batch_id}
            )
            batch = result.fetchone()
            
            if not batch:
                raise HTTPException(status_code=404, detail=f"Batch {batch_id} nicht gefunden")
            
            # Starte Geocoding im Hintergrund
            background_tasks.add_task(process_batch_geocoding, batch_id, limit=100)
            
            # Aktualisiere Status
            conn.execute(
                text("UPDATE import_batches SET status = 'running' WHERE id = :batch_id"),
                {"batch_id": batch_id}
            )
        
        logger.info(f"[IMPORT] Geocoding für Batch {batch_id} gestartet")
        
        return JSONResponse({
            "success": True,
            "message": "Geocoding-Worker gestartet",
            "batch_id": batch_id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[IMPORT] Fehler beim Starten des Batches {batch_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/geocoding/process")
async def process_geocoding(limit: int = 10, batch_id: Optional[int] = None):
    """
    Startet Geocoding-Worker für pending Kunden.
    
    Args:
        limit: Maximale Anzahl zu verarbeitender Kunden (Standard: 10)
        batch_id: Optional - Spezifischer Batch-ID
    """
    try:
        from backend.services.geocoding_worker import process_batch_geocoding
        
        result = process_batch_geocoding(batch_id, limit)
        
        return JSONResponse({
            "success": True,
            "result": result,
            "message": f"{result['processed']} Kunden verarbeitet ({result['ok']} OK, {result['failed']} fehlgeschlagen)"
        })
    except Exception as e:
        logger.error(f"Fehler beim Geocoding-Worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geocoding/pending")
async def get_pending_geocoding_count():
    """
    Gibt die Anzahl der Kunden mit pending Geocoding-Status zurück.
    """
    try:
        from backend.services.geocoding_worker import get_pending_count
        
        count = get_pending_count()
        
        return JSONResponse({
            "success": True,
            "pending_count": count
        })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der pending Count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

