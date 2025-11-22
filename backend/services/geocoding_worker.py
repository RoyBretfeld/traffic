"""
Geocoding-Worker für Tour-Import & Vorladen
Verarbeitet Kunden mit geocode_status = 'pending' im Hintergrund
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from db.core import ENGINE
from sqlalchemy import text
from backend.services.geocode import geocode_address

logger = logging.getLogger(__name__)


def process_customer_geocoding(customer_id: int, limit: int = 1) -> Dict[str, Any]:
    """
    Verarbeitet einen einzelnen Kunden mit geocode_status = 'pending'.
    
    Args:
        customer_id: ID des Kunden
        limit: Maximale Anzahl zu verarbeitender Kunden (Standard: 1)
    
    Returns:
        Dict mit Ergebnis: {'processed': int, 'ok': int, 'failed': int, 'errors': list}
    """
    result = {
        'processed': 0,
        'ok': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        with ENGINE.begin() as conn:
            # Hole Kunden mit pending Status
            query = text("""
                SELECT id, name, street, zip, city, country
                FROM customers
                WHERE geocode_status = 'pending' OR geocode_status IS NULL
                LIMIT :limit
            """)
            
            rows = conn.execute(query, {'limit': limit}).fetchall()
            
            if not rows:
                logger.info(f"[GEOCODING-WORKER] Keine Kunden mit pending Status gefunden")
                return result
            
            for row in rows:
                customer_id = row[0]
                name = row[1] or ''
                street = row[2] or ''
                zip_code = row[3] or ''
                city = row[4] or ''
                country = row[5] or 'Deutschland'
                
                # Baue vollständige Adresse
                address_parts = [street]
                if zip_code and city:
                    address_parts.append(f"{zip_code} {city}")
                elif city:
                    address_parts.append(city)
                if country and country != 'Deutschland':
                    address_parts.append(country)
                
                address = ", ".join(part for part in address_parts if part.strip())
                
                if not address:
                    logger.warning(f"[GEOCODING-WORKER] Kunde {customer_id}: Keine Adresse vorhanden")
                    # Markiere als failed
                    conn.execute(
                        text("""
                            UPDATE customers 
                            SET geocode_status = 'failed',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :customer_id
                        """),
                        {'customer_id': customer_id}
                    )
                    result['failed'] += 1
                    result['processed'] += 1
                    continue
                
                # Geocode Adresse
                logger.info(f"[GEOCODING-WORKER] Geocode Kunde {customer_id}: {address}")
                geocode_result = geocode_address(address)
                
                if geocode_result and geocode_result.get('lat') and geocode_result.get('lon'):
                    # Erfolgreich geocodiert
                    lat = geocode_result['lat']
                    lon = geocode_result['lon']
                    
                    conn.execute(
                        text("""
                            UPDATE customers 
                            SET lat = :lat,
                                lon = :lon,
                                geocode_status = 'ok',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :customer_id
                        """),
                        {
                            'customer_id': customer_id,
                            'lat': lat,
                            'lon': lon
                        }
                    )
                    
                    logger.info(f"[GEOCODING-WORKER] ✅ Kunde {customer_id}: Geocoded ({lat}, {lon})")
                    result['ok'] += 1
                else:
                    # Geocoding fehlgeschlagen
                    conn.execute(
                        text("""
                            UPDATE customers 
                            SET geocode_status = 'failed',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :customer_id
                        """),
                        {'customer_id': customer_id}
                    )
                    
                    logger.warning(f"[GEOCODING-WORKER] ❌ Kunde {customer_id}: Geocoding fehlgeschlagen")
                    result['failed'] += 1
                
                result['processed'] += 1
            
            # Aktualisiere Batch-Statistiken (falls Kunde zu einem Batch gehört)
            # TODO: Verknüpfung zwischen customers und import_batches herstellen
            
    except Exception as e:
        logger.error(f"[GEOCODING-WORKER] Fehler bei Verarbeitung: {e}", exc_info=True)
        result['errors'].append(str(e))
    
    return result


def process_batch_geocoding(batch_id: Optional[int] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Verarbeitet Geocoding für einen spezifischen Batch oder alle pending Kunden.
    
    Args:
        batch_id: Optional - ID des Import-Batches
        limit: Maximale Anzahl zu verarbeitender Kunden
    
    Returns:
        Dict mit Ergebnis
    """
    if batch_id:
        # TODO: Nur Kunden aus diesem Batch verarbeiten
        # Dafür müsste eine Verknüpfung zwischen customers und import_batches existieren
        logger.info(f"[GEOCODING-WORKER] Verarbeite Batch {batch_id} (noch nicht implementiert)")
    
    return process_customer_geocoding(0, limit)


def get_pending_count() -> int:
    """Gibt die Anzahl der Kunden mit pending Geocoding-Status zurück."""
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM customers
                    WHERE geocode_status = 'pending' OR geocode_status IS NULL
                """)
            )
            count = result.scalar() or 0
            return count
    except Exception as e:
        logger.error(f"[GEOCODING-WORKER] Fehler beim Zählen: {e}")
        return 0


def update_batch_statistics(batch_id: int) -> None:
    """
    Aktualisiert die Geocoding-Statistiken für einen Import-Batch.
    """
    try:
        with ENGINE.begin() as conn:
            # Zähle Kunden nach Status (vereinfacht - müsste über tour_stops gehen)
            stats = conn.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN geocode_status = 'ok' THEN 1 ELSE 0 END) as ok,
                        SUM(CASE WHEN geocode_status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN geocode_status = 'pending' OR geocode_status IS NULL THEN 1 ELSE 0 END) as pending
                    FROM customers
                """)
            ).fetchone()
            
            if stats:
                conn.execute(
                    text("""
                        UPDATE import_batches
                        SET geocoded_ok = :ok,
                            geocoded_failed = :failed,
                            geocoded_pending = :pending
                        WHERE id = :batch_id
                    """),
                    {
                        'batch_id': batch_id,
                        'ok': stats[1] or 0,
                        'failed': stats[2] or 0,
                        'pending': stats[3] or 0
                    }
                )
                logger.info(f"[GEOCODING-WORKER] Batch {batch_id} Statistiken aktualisiert")
    except Exception as e:
        logger.error(f"[GEOCODING-WORKER] Fehler beim Aktualisieren der Batch-Statistiken: {e}")

