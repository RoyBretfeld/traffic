from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter()

@router.get("/health/db")
async def health_db():
    try:
        with ENGINE.connect() as conn:
            # Einfacher Query zur Prüfung der Verbindung
            conn.execute(text("SELECT 1"))
            
            # Optional: Tabellennamen abrufen
            # Dies hängt stark vom DB-Typ ab. Für SQLite:
            if str(ENGINE.url).startswith("sqlite"):
                tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
                tables = ", ".join([row[0] for row in tables_result])
            else:
                tables = "unknown"

        return JSONResponse({"status": "online", "tables": tables}, status_code=200)
    except Exception as e:
        return JSONResponse({"status": "offline", "error": str(e)}, status_code=500)
