"""
API-Endpunkte für automatisches Fehler-Logging.

PFLICHT: Jeder nachgewiesene Fehler muss gespeichert werden!
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.services.error_auto_logger import get_error_auto_logger

router = APIRouter(prefix="/api/errors", tags=["errors"])


class ErrorLogRequest(BaseModel):
    """Request-Modell für automatisches Fehler-Logging."""
    error_type: str
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    user_agent: Optional[str] = None
    url: Optional[str] = None
    severity: str = "🔴 KRITISCH"


@router.post("/auto-log")
async def auto_log_error(
    error_data: ErrorLogRequest,
    request: Request = None
):
    """
    Speichert einen Fehler automatisch in LESSONS_LOG.md.
    
    PFLICHT: Jeder nachgewiesene Fehler muss gespeichert werden!
    
    Args:
        error_type: Art des Fehlers (SyntaxError, ReferenceError, etc.)
        error_message: Fehlermeldung
        file_path: Datei in der der Fehler auftrat
        line_number: Zeilennummer
        stack_trace: Stack-Trace (optional)
        user_agent: Browser-Info (optional)
        url: URL wo Fehler auftrat (optional)
        severity: Schweregrad (🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW)
    """
    try:
        # Hole User-Agent aus Request falls nicht übergeben
        user_agent = error_data.user_agent
        if not user_agent and request:
            user_agent = request.headers.get("user-agent", "Unknown")
        
        # Hole URL aus Request falls nicht übergeben
        url = error_data.url
        if not url and request:
            url = str(request.url)
        
        error_logger = get_error_auto_logger()
        result = error_logger.log_error(
            error_type=error_data.error_type,
            error_message=error_data.error_message,
            file_path=error_data.file_path,
            line_number=error_data.line_number,
            stack_trace=error_data.stack_trace,
            user_agent=user_agent,
            url=url,
            severity=error_data.severity
        )
        
        if result.get("success"):
            return JSONResponse({
                **result,
                "message": f"Fehler '{result.get('title')}' automatisch in LESSONS_LOG.md eingetragen"
            })
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Fehler beim Speichern"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Auto-Logging: {str(e)}")

