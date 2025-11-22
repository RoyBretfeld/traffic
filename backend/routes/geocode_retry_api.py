"""
AR-05: Geocoding-Failure Retry API.
Ermöglicht erneutes Versuchen von fehlgeschlagenen Geocodes.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from backend.routes.auth_api import require_admin
from backend.utils.error_response import create_error_response, ErrorCode
from repositories.geo_fail_repo import GeoFailRepo
from backend.services.geocode import geocode_address
from db.core import ENGINE
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/geocode", tags=["geocoding"])


class RetryRequest(BaseModel):
    """Request für Geocoding-Retry (AR-05)."""
    address: str
    force: bool = False  # Ignoriere next_attempt TTL


class RetryBatchRequest(BaseModel):
    """Request für Batch-Retry (AR-05)."""
    addresses: List[str] = []
    limit: int = 10
    force: bool = False


@router.post("/retry", dependencies=[Depends(require_admin)])
async def retry_geocode(request: RetryRequest):
    """
    AR-05: Versucht erneut, eine Adresse zu geocodieren.
    
    Args:
        request: RetryRequest mit address und optional force
    
    Returns:
        JSONResponse mit Geocoding-Ergebnis
    """
    try:
        # Prüfe ob Adresse im geo_fail ist
        geo_fail_repo = GeoFailRepo()
        fail_entry = geo_fail_repo.get_by_address(request.address)
        
        if not fail_entry and not request.force:
            return create_error_response(
                code=ErrorCode.NOT_FOUND,
                message=f"Adresse '{request.address}' nicht in Fehler-Liste gefunden",
                status_code=404
            )
        
        # Versuche Geocoding
        result = geocode_address(request.address)
        
        if result and result.get('lat') and result.get('lon'):
            # Erfolg: Speichere in geo_cache und entferne aus geo_fail
            with ENGINE.begin() as conn:
                # Upsert in geo_cache
                conn.execute(text("""
                    INSERT INTO geo_cache (address_norm, lat, lon, source, updated_at)
                    VALUES (:address, :lat, :lon, 'geocoded', CURRENT_TIMESTAMP)
                    ON CONFLICT(address_norm) DO UPDATE SET
                        lat = excluded.lat,
                        lon = excluded.lon,
                        source = excluded.source,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    "address": request.address,
                    "lat": result['lat'],
                    "lon": result['lon']
                })
                
                # Entferne aus geo_fail
                conn.execute(text("""
                    DELETE FROM geo_fail WHERE address_norm = :address
                """), {"address": request.address})
            
            logger.info(f"Geocoding-Retry erfolgreich: {request.address} -> {result['lat']}, {result['lon']}")
            
            return JSONResponse({
                "success": True,
                "address": request.address,
                "result": result,
                "message": "Geocoding erfolgreich"
            })
        else:
            # Fehlgeschlagen: Aktualisiere geo_fail
            geo_fail_repo.mark_failed(request.address, reason="retry_failed")
            
            return create_error_response(
                code=ErrorCode.GEOCODING_FAILED,
                message=f"Geocoding fehlgeschlagen für '{request.address}'",
                status_code=500
            )
            
    except Exception as e:
        logger.error(f"Fehler beim Geocoding-Retry: {e}", exc_info=True)
        return create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Fehler beim Retry: {str(e)}",
            status_code=500
        )


@router.post("/retry-batch", dependencies=[Depends(require_admin)])
async def retry_geocode_batch(request: RetryBatchRequest):
    """
    AR-05: Versucht erneut, mehrere Adressen zu geocodieren (Batch).
    
    Args:
        request: RetryBatchRequest mit addresses, limit, force
    
    Returns:
        JSONResponse mit Batch-Ergebnis
    """
    try:
        addresses = request.addresses[:request.limit] if request.addresses else []
        
        if not addresses:
            # Lade Adressen aus geo_fail
            with ENGINE.begin() as conn:
                rows = conn.execute(text("""
                    SELECT address_norm FROM geo_fail
                    WHERE next_attempt IS NULL OR next_attempt <= strftime('%s', 'now')
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """), {"limit": request.limit}).fetchall()
                addresses = [row[0] for row in rows]
        
        if not addresses:
            return JSONResponse({
                "success": True,
                "message": "Keine Adressen zum Retry gefunden",
                "results": []
            })
        
        results = []
        success_count = 0
        failed_count = 0
        
        for address in addresses:
            try:
                retry_request = RetryRequest(address=address, force=request.force)
                result = await retry_geocode(retry_request)
                
                result_data = result.body.decode('utf-8') if hasattr(result, 'body') else {}
                if isinstance(result_data, str):
                    import json
                    result_data = json.loads(result_data)
                
                if result_data.get('success'):
                    success_count += 1
                else:
                    failed_count += 1
                
                results.append({
                    "address": address,
                    "success": result_data.get('success', False),
                    "result": result_data.get('result')
                })
            except Exception as e:
                failed_count += 1
                results.append({
                    "address": address,
                    "success": False,
                    "error": str(e)
                })
        
        return JSONResponse({
            "success": True,
            "total": len(addresses),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Batch-Retry: {e}", exc_info=True)
        return create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Fehler beim Batch-Retry: {str(e)}",
            status_code=500
        )

