from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import re
import time
from ingest.guards import assert_no_mojibake, trace_text

router = APIRouter()

# Staging-Verzeichnis aus ENV oder Default
STAGING = Path(os.getenv("STAGING_DIR", "./data/staging")).resolve()
STAGING.mkdir(parents=True, exist_ok=True)

# Sichere Dateinamen (nur alphanumerisch, Punkte, Bindestriche, Unterstriche)
SAFE = re.compile(r"[^A-Za-z0-9_.\-]+")
MAX_BYTES = 5 * 1024 * 1024  # 5MB Limit

def _heuristic_decode(raw: bytes) -> tuple[str, str]:
    """
    Heuristische Dekodierung von CSV-Daten mit Encoding-Erkennung.
    Versucht verschiedene Encodings in der Reihenfolge: cp850, utf-8-sig, latin-1
    """
    for enc in ("cp850", "utf-8-sig", "latin-1"):
        try:
            decoded = raw.decode(enc)
            # Mojibake-Schutz aktivieren
            assert_no_mojibake(decoded)
            trace_text("UPLOAD-DECODE", f"Encoding: {enc}, Length: {len(decoded)}")
            return decoded, enc
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[UPLOAD] Mojibake-Schutz aktiviert für {enc}: {e}")
            continue
    
    # Letzte Rettung: UTF-8 mit Ersetzung
    print("[UPLOAD] Fallback auf UTF-8 mit Ersetzung")
    return raw.decode("utf-8", errors="replace"), "utf-8*replace"

@router.post("/api/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload einer CSV-Datei mit automatischer Encoding-Erkennung.
    
    - Speichert nur in STAGING_DIR (UTF-8)
    - Originale bleiben read-only
    - Heuristische Encoding-Erkennung (cp850, utf-8-sig, latin-1)
    - Mojibake-Schutz aktiviert
    """
    if not file.filename:
        raise HTTPException(400, detail="Kein Dateiname angegeben")
    
    # Nur .csv erlauben (locker)
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, detail="Nur .csv Dateien erlaubt")
    
    try:
        # Datei lesen
        raw = await file.read()
        if len(raw) == 0:
            raise HTTPException(400, detail="Leere Datei")
        
        # Size-Limit prüfen
        if len(raw) > MAX_BYTES:
            raise HTTPException(413, detail="Datei zu groß")
        
        # Heuristische Dekodierung
        text, used = _heuristic_decode(raw)
        
        # Sicheren Staging-Pfad generieren
        base = SAFE.sub("_", Path(file.filename).stem)  # ohne .csv
        timestamp = int(time.time())
        staging_file = (STAGING / f"{timestamp}_{base}.csv").resolve()
        
        # Pfad-Guard: Sicherstellen, dass nur in STAGING geschrieben wird
        if STAGING not in staging_file.parents and staging_file != STAGING:
            raise HTTPException(400, detail="Ungültiger Pfad")
        
        # UTF-8 Staging-Datei schreiben
        staging_file.write_text(text, encoding="utf-8")
        
        print(f"[UPLOAD] Erfolgreich: {file.filename} -> {staging_file}")
        
        return JSONResponse({
            "ok": True,
            "staging_file": str(staging_file),
            "original_filename": file.filename,
            "size": len(raw),
            "decoded_size": len(text),
            "encoding_used": used
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        print(f"[UPLOAD] Fehler bei {file.filename}: {e}")
        raise HTTPException(500, detail=f"Upload-Fehler: {str(e)}")

@router.get("/api/upload/status")
async def upload_status():
    """
    Status des Upload-Systems.
    """
    staging_files = list(STAGING.glob("*.csv"))
    
    return JSONResponse({
        "staging_dir": str(STAGING),
        "staging_files_count": len(staging_files),
        "staging_files": [
            {
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            }
            for f in staging_files
        ]
    })
