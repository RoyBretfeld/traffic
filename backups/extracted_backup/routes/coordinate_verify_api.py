"""
API für Koordinaten-Verifizierung.
Prüft ob gespeicherte Koordinaten wirklich zu den Unternehmen passen.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import asyncio
from repositories.geo_repo import get as geo_get

from backend.services.coordinate_verifier import verify_coordinate

router = APIRouter()


@router.post("/api/coordinate/verify-single")
async def verify_single_coordinate(
    lat: float = Query(..., description="Breitengrad"),
    lon: float = Query(..., description="Längengrad"),
    company_name: str = Query(..., description="Firmenname"),
    address: str = Query(..., description="Adresse")
):
    """
    Verifiziert eine einzelne Koordinate mit allen 3 Services.
    
    Returns:
        {
            "google_maps": {...},
            "geoapify": {...},
            "nominatim": {...},
            "overall_status": "all_good" | "needs_review" | "critical",
            "success_count": int
        }
    """
    try:
        result = await verify_coordinate(lat, lon, company_name, address)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verifizierung fehlgeschlagen: {str(e)}")


@router.post("/api/coordinate/verify-batch")
async def verify_batch_coordinates(
    customers: List[Dict[str, Any]]
):
    """
    Verifiziert mehrere Koordinaten parallel.
    
    Request Body:
        [
            {
                "customer_number": "1234",
                "company_name": "Firma XYZ",
                "address": "Straße 1, 01234 Dresden",
                "lat": 51.0,
                "lon": 13.7
            },
            ...
        ]
    
    Returns:
        {
            "results": [
                {
                    "customer_number": "1234",
                    "google_maps": {...},
                    "geoapify": {...},
                    "nominatim": {...},
                    "overall_status": "...",
                    "success_count": int
                },
                ...
            ],
            "summary": {
                "total": int,
                "all_good": int,
                "needs_review": int,
                "critical": int
            }
        }
    """
    try:
        # Verarbeite alle parallel (mit Rate-Limiting)
        results = []
        for i, customer in enumerate(customers):
            # Rate-Limiting: 0.5 Sekunden zwischen Requests (Nominatim erfordert das)
            if i > 0:
                await asyncio.sleep(0.5)
            
            result = await verify_coordinate(
                lat=customer["lat"],
                lon=customer["lon"],
                company_name=customer.get("company_name", ""),
                address=customer.get("address", "")
            )
            
            results.append({
                "customer_number": customer.get("customer_number", ""),
                "company_name": customer.get("company_name", ""),
                "address": customer.get("address", ""),
                **result
            })
        
        # Zusammenfassung
        summary = {
            "total": len(results),
            "all_good": sum(1 for r in results if r["overall_status"] == "all_good"),
            "needs_review": sum(1 for r in results if r["overall_status"] == "needs_review"),
            "critical": sum(1 for r in results if r["overall_status"] == "critical")
        }
        
        return JSONResponse({
            "results": results,
            "summary": summary
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch-Verifizierung fehlgeschlagen: {str(e)}")


@router.get("/api/coordinate/verify-from-workflow")
async def verify_from_workflow(
    session_id: Optional[str] = Query(None, description="Session ID (optional)")
):
    """
    Lädt Kunden aus aktueller Workflow-Session und verifiziert deren Koordinaten.
    
    Returns:
        Wie verify-batch, aber mit Daten aus Workflow-Session.
    """
    try:
        # TODO: Workflow-Session-Daten laden
        # Für jetzt: Rückgabe leere Liste
        return JSONResponse({
            "results": [],
            "summary": {
                "total": 0,
                "all_good": 0,
                "needs_review": 0,
                "critical": 0
            },
            "message": "Workflow-Session-Daten werden noch nicht unterstützt. Bitte verwende /verify-batch"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

