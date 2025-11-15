"""
API-Endpoints für Code-Improvement Background-Job.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from backend.services.code_improvement_job import get_background_job
import asyncio

router = APIRouter()

@router.get("/api/code-improvement-job/status")
async def get_job_status():
    """Gibt Status des Background-Jobs zurück."""
    job = get_background_job()
    status = job.get_status()
    return JSONResponse(status)

@router.post("/api/code-improvement-job/start")
async def start_job():
    """Startet den Background-Job."""
    job = get_background_job()
    
    if job.is_running:
        return JSONResponse({
            "success": False,
            "message": "Background-Job läuft bereits"
        })
    
    if not job.enabled:
        return JSONResponse({
            "success": False,
            "message": "Background-Job ist deaktiviert"
        })
    
    if not job.ai_checker:
        return JSONResponse({
            "success": False,
            "message": "KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)"
        })
    
    # Starte Job im Hintergrund
    asyncio.create_task(job.run_continuously())
    
    return JSONResponse({
        "success": True,
        "message": "Background-Job gestartet"
    })

@router.post("/api/code-improvement-job/stop")
async def stop_job():
    """Stoppt den Background-Job."""
    job = get_background_job()
    
    if not job.is_running:
        return JSONResponse({
            "success": False,
            "message": "Background-Job läuft nicht"
        })
    
    job.stop()
    
    return JSONResponse({
        "success": True,
        "message": "Background-Job gestoppt"
    })

@router.post("/api/code-improvement-job/run-once")
async def run_job_once():
    """Führt eine einmalige Verbesserungs-Runde aus."""
    job = get_background_job()
    
    if not job.enabled:
        raise HTTPException(status_code=400, detail="Background-Job ist deaktiviert")
    
    if not job.ai_checker:
        raise HTTPException(status_code=503, detail="KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
    
    result = await job.run_once()
    
    return JSONResponse(result)

