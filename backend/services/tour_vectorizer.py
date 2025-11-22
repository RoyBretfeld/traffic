"""
Tour-Vectorizer: Background-Job für Tour-Vektorisierung.
Läuft 5 Minuten nach Tour-Erstellung und speichert Embeddings in ChromaDB.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import text
from db.core import ENGINE
import logging
import json

from backend.services.tour_embedder import embed_and_store_tour
from backend.utils.enhanced_logging import get_enhanced_logger

logger = logging.getLogger(__name__)
enhanced_logger = get_enhanced_logger(__name__)

# Queue für Touren, die vektorisiert werden sollen
_vectorization_queue: List[Dict[str, Any]] = []


def queue_tour_for_vectorization(tour_id: str, datum: str, delay_minutes: int = 5):
    """
    Fügt eine Tour zur Vektorisierungs-Queue hinzu.
    
    Args:
        tour_id: Tour-Identifikator
        datum: Tour-Datum (YYYY-MM-DD)
        delay_minutes: Verzögerung in Minuten (Standard: 5)
    """
    vectorize_at = datetime.now() + timedelta(minutes=delay_minutes)
    
    _vectorization_queue.append({
        "tour_id": tour_id,
        "datum": datum,
        "vectorize_at": vectorize_at,
        "processed": False
    })
    
    logger.info(f"Tour {tour_id} ({datum}) zur Vektorisierung geplant (in {delay_minutes} Min)")


async def process_vectorization_queue():
    """
    Verarbeitet die Vektorisierungs-Queue.
    Wird periodisch aufgerufen (z.B. alle 30 Sekunden).
    """
    now = datetime.now()
    to_process = []
    
    # Finde Touren, die jetzt vektorisiert werden sollen
    for item in _vectorization_queue:
        if not item["processed"] and item["vectorize_at"] <= now:
            to_process.append(item)
    
    # Verarbeite jede Tour
    for item in to_process:
        try:
            tour_id = item["tour_id"]
            datum = item["datum"]
            
            # Lade Tour-Daten aus DB
            with ENGINE.begin() as conn:
                tour_row = conn.execute(text("""
                    SELECT 
                        tour_id,
                        datum,
                        kunden_ids,
                        distanz_km,
                        gesamtzeit_min,
                        fahrer
                    FROM touren
                    WHERE tour_id = :tour_id AND datum = :datum
                """), {
                    "tour_id": tour_id,
                    "datum": datum
                }).fetchone()
                
                if not tour_row:
                    logger.warning(f"Tour {tour_id} ({datum}) nicht in DB gefunden - überspringe Vektorisierung")
                    item["processed"] = True
                    continue
                
                # Bereite Metadaten vor
                tour_id_db, datum_db, kunden_ids, distanz_km, gesamtzeit_min, fahrer = tour_row
                
                # Berechne Anzahl Stops aus kunden_ids
                stops_count = 0
                if kunden_ids:
                    try:
                        ids = json.loads(kunden_ids)
                        if isinstance(ids, list):
                            stops_count = len(ids)
                    except (json.JSONDecodeError, TypeError):
                        stops_count = kunden_ids.count(',') + 1 if kunden_ids else 0
                
                # Extrahiere Sektor aus tour_id (falls vorhanden)
                sector = ""
                if "Nord" in tour_id or "N-" in tour_id:
                    sector = "N"
                elif "Ost" in tour_id or "O-" in tour_id:
                    sector = "O"
                elif "Süd" in tour_id or "S-" in tour_id:
                    sector = "S"
                elif "West" in tour_id or "W-" in tour_id:
                    sector = "W"
                
                # Extrahiere Tour-Typ
                tour_type = ""
                if tour_id.startswith("W-") or "W-" in tour_id:
                    tour_type = "W"
                elif "PIR" in tour_id.upper():
                    tour_type = "PIR"
                elif tour_id.startswith("T-") or "T-" in tour_id:
                    tour_type = "T"
                
                tour_metadata = {
                    "tour_id": tour_id_db,
                    "datum": datum_db,
                    "stops_count": stops_count,
                    "distance_km": float(distanz_km) if distanz_km else 0.0,
                    "total_time_min": int(gesamtzeit_min) if gesamtzeit_min else 0,
                    "sector": sector,
                    "tour_type": tour_type,
                    "fahrer": fahrer or ""
                }
                
                # Erstelle Embedding und speichere
                success = embed_and_store_tour(
                    tour_id=tour_id_db,
                    datum=datum_db,
                    tour_metadata=tour_metadata
                )
                
                if success:
                    enhanced_logger.success(f"Tour vektorisiert: {tour_id_db} ({datum_db})")
                else:
                    enhanced_logger.warning(f"Tour-Vektorisierung fehlgeschlagen: {tour_id_db} ({datum_db})")
                
                item["processed"] = True
                
        except Exception as e:
            logger.error(f"Fehler bei Vektorisierung von Tour {item.get('tour_id')}: {e}", exc_info=True)
            item["processed"] = True
    
    # Entferne verarbeitete Items (älter als 1 Stunde)
    cutoff_time = datetime.now() - timedelta(hours=1)
    _vectorization_queue[:] = [
        item for item in _vectorization_queue
        if not item["processed"] or item["vectorize_at"] > cutoff_time
    ]


async def vectorize_existing_tours(days: int = 7):
    """
    Vektorisiert bestehende Touren aus der letzten Woche.
    Nützlich für initiale Befüllung der Vektordatenbank.
    
    Args:
        days: Anzahl der Tage zurück (Standard: 7)
    """
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with ENGINE.begin() as conn:
            tours = conn.execute(text("""
                SELECT 
                    tour_id,
                    datum,
                    kunden_ids,
                    distanz_km,
                    gesamtzeit_min
                FROM touren
                WHERE datum >= :cutoff_date
                AND (distanz_km IS NOT NULL OR gesamtzeit_min IS NOT NULL)
                ORDER BY datum DESC, tour_id
            """), {"cutoff_date": cutoff_date}).fetchall()
            
            enhanced_logger.info(f"Vektorisierung von {len(tours)} bestehenden Touren gestartet...")
            
            for tour_row in tours:
                tour_id, datum, kunden_ids, distanz_km, gesamtzeit_min = tour_row
                
                # Bereite Metadaten vor (analog zu process_vectorization_queue)
                stops_count = 0
                if kunden_ids:
                    try:
                        ids = json.loads(kunden_ids)
                        if isinstance(ids, list):
                            stops_count = len(ids)
                    except (json.JSONDecodeError, TypeError):
                        stops_count = kunden_ids.count(',') + 1 if kunden_ids else 0
                
                sector = ""
                if "Nord" in tour_id or "N-" in tour_id:
                    sector = "N"
                elif "Ost" in tour_id or "O-" in tour_id:
                    sector = "O"
                elif "Süd" in tour_id or "S-" in tour_id:
                    sector = "S"
                elif "West" in tour_id or "W-" in tour_id:
                    sector = "W"
                
                tour_type = ""
                if tour_id.startswith("W-") or "W-" in tour_id:
                    tour_type = "W"
                elif "PIR" in tour_id.upper():
                    tour_type = "PIR"
                elif tour_id.startswith("T-") or "T-" in tour_id:
                    tour_type = "T"
                
                tour_metadata = {
                    "tour_id": tour_id,
                    "datum": datum,
                    "stops_count": stops_count,
                    "distance_km": float(distanz_km) if distanz_km else 0.0,
                    "total_time_min": int(gesamtzeit_min) if gesamtzeit_min else 0,
                    "sector": sector,
                    "tour_type": tour_type
                }
                
                embed_and_store_tour(tour_id, datum, tour_metadata)
                
                # Kleine Verzögerung um DB nicht zu überlasten
                await asyncio.sleep(0.1)
            
            enhanced_logger.success(f"Vektorisierung abgeschlossen: {len(tours)} Touren verarbeitet")
            
    except Exception as e:
        enhanced_logger.error(f"Fehler bei Vektorisierung bestehender Touren: {e}", exc_info=True)


async def run_vectorizer_loop(interval_seconds: int = 30):
    """
    Läuft als Hintergrund-Loop und verarbeitet die Vektorisierungs-Queue periodisch.
    
    Args:
        interval_seconds: Intervall in Sekunden zwischen Verarbeitungen (Standard: 30)
    """
    while True:
        try:
            await process_vectorization_queue()
        except Exception as e:
            logger.error(f"Fehler im Vectorizer-Loop: {e}", exc_info=True)
        
        # Warte bis zur nächsten Ausführung
        await asyncio.sleep(interval_seconds)

