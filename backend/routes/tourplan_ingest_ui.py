# routes/tourplan_ingest_ui.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

router = APIRouter()

@router.get("/admin/tourplan-ingest", response_class=HTMLResponse, summary="Tourplan-Import-Seite")
async def tourplan_ingest_page(request: Request):
    """Tourplan-Import-Seite (geschützt)."""
    # Auth-Check
    from backend.routes.auth_api import get_session_from_request
    from fastapi.responses import RedirectResponse
    
    session_id = get_session_from_request(request)
    if not session_id:
        # Redirect zu Login
        return RedirectResponse(url="/admin/login.html?redirect=/admin/tourplan-ingest", status_code=302)
    
    try:
        html_path = Path("frontend/admin/tourplan_ingest.html")
        if not html_path.exists():
            raise FileNotFoundError(f"HTML-Datei nicht gefunden: {html_path}")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interner Serverfehler: {e}")
