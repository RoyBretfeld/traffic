from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import re
import time
from ingest.guards import assert_no_mojibake, trace_text
from common.text_cleaner import repair_cp_mojibake

router = APIRouter()

# Tourplaene-Verzeichnis (read-only) - NIEMALS hier schreiben!
TOURPLAENE_DIR = Path(os.getenv("ORIG_DIR", "./tourplaene")).resolve()

# Staging-Verzeichnis für temporäre Verarbeitung (NUR hier schreiben!)
STAGING = Path(os.getenv("STAGING_DIR", "./data/staging")).resolve()
STAGING.mkdir(parents=True, exist_ok=True)

# Cleanup-Konfiguration
STAGING_RETENTION_HOURS = int(os.getenv("STAGING_RETENTION_HOURS", "24"))  # Standard: 24 Stunden
STAGING_MAX_FILES = int(os.getenv("STAGING_MAX_FILES", "100"))  # Max. Anzahl Dateien

def cleanup_old_staging_files():
    """
    Löscht alte Dateien aus dem Staging-Verzeichnis.
    - Dateien älter als STAGING_RETENTION_HOURS werden gelöscht
    - Wenn mehr als STAGING_MAX_FILES vorhanden sind, werden die ältesten gelöscht
    """
    if not STAGING.exists():
        return
    
    current_time = time.time()
    cutoff_time = current_time - (STAGING_RETENTION_HOURS * 3600)
    
    staging_files = list(STAGING.glob("*.csv"))
    deleted_count = 0
    total_size_freed = 0
    
    # 1. Lösche Dateien älter als Retention-Zeit
    for file_path in staging_files:
        try:
            file_age = file_path.stat().st_mtime
            if file_age < cutoff_time:
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1
                total_size_freed += file_size
        except Exception as e:
            print(f"[CLEANUP] Fehler beim Löschen von {file_path.name}: {e}")
    
    # 2. Wenn immer noch zu viele Dateien: Lösche die ältesten
    remaining_files = list(STAGING.glob("*.csv"))
    if len(remaining_files) > STAGING_MAX_FILES:
        # Sortiere nach Alter (älteste zuerst)
        remaining_files.sort(key=lambda f: f.stat().st_mtime)
        
        # Lösche die ältesten Dateien
        files_to_delete = remaining_files[:len(remaining_files) - STAGING_MAX_FILES]
        for file_path in files_to_delete:
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1
                total_size_freed += file_size
            except Exception as e:
                print(f"[CLEANUP] Fehler beim Löschen von {file_path.name}: {e}")
    
    if deleted_count > 0:
        size_mb = total_size_freed / (1024 * 1024)
        print(f"[CLEANUP] {deleted_count} alte Staging-Dateien gelöscht ({size_mb:.2f} MB freigegeben)")
    
    return deleted_count, total_size_freed

# Schutz-Prüfung für Uploads
try:
    from fs.protected_fs import is_protected_path
    _HAS_PROTECTION = True
except ImportError:
    _HAS_PROTECTION = False

# Sichere Dateinamen (nur alphanumerisch, Punkte, Bindestriche, Unterstriche)
SAFE = re.compile(r"[^A-Za-z0-9_.\-]+")
MAX_BYTES = 5 * 1024 * 1024  # 5MB Limit

def _heuristic_decode(raw: bytes, skip_mojibake_check: bool = False) -> tuple[str, str]:
    """
    Heuristische Dekodierung von CSV-Daten mit Encoding-Erkennung.
    Versucht verschiedene Encodings in der Reihenfolge: cp850, utf-8-sig, latin-1
    
    Args:
        skip_mojibake_check: Wenn True, wird der Mojibake-Check übersprungen
                            (für bereits reparierte Staging-Dateien)
    """
    for enc in ("cp850", "utf-8-sig", "latin-1"):
        try:
            decoded = raw.decode(enc)
            # Mojibake-Schutz aktivieren (nur wenn nicht übersprungen)
            if not skip_mojibake_check:
                assert_no_mojibake(decoded)
            trace_text("UPLOAD-DECODE", f"Encoding: {enc}, Length: {len(decoded)}")
            return decoded, enc
        except UnicodeDecodeError:
            continue
        except Exception as e:
            if skip_mojibake_check:
                # Bei übersprungenem Check: trotzdem verwenden
                trace_text("UPLOAD-DECODE", f"Encoding: {enc}, Length: {len(decoded)} (Mojibake-Check übersprungen)")
                return decoded, enc
            print(f"[UPLOAD] Mojibake-Schutz aktiviert für {enc}: {e}")
            continue
    
    # Letzte Rettung: UTF-8 mit Ersetzung
    print("[UPLOAD] Fallback auf UTF-8 mit Ersetzung")
    return raw.decode("utf-8", errors="replace"), "utf-8*replace"

@router.get("/api/tourplaene/list")
async def list_tourplaene():
    """
    Listet alle verfügbaren Tourplan-CSV-Dateien aus dem Tourplaene-Verzeichnis auf.
    
    Returns:
        JSON mit Liste der CSV-Dateien und deren Metadaten
    """
    try:
        if not TOURPLAENE_DIR.exists():
            raise HTTPException(404, detail=f"Tourplaene-Verzeichnis nicht gefunden: {TOURPLAENE_DIR}")
        
        # CSV-Dateien auflisten
        csv_files = []
        for csv_file in TOURPLAENE_DIR.glob("*.csv"):
            try:
                stat = csv_file.stat()
                csv_files.append({
                    "name": csv_file.name,
                    "path": str(csv_file),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "read_only": True  # Dateien sind read-only
                })
            except Exception as e:
                print(f"[WARNING] Fehler beim Lesen von {csv_file}: {e}")
                continue
        
        # Nach Name sortieren
        csv_files.sort(key=lambda x: x["name"])
        
        return JSONResponse({
            "success": True,
            "files": csv_files,
            "count": len(csv_files),
            "directory": str(TOURPLAENE_DIR),
            "note": "Dateien werden direkt aus dem Tourplaene-Verzeichnis gelesen (read-only)"
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Auflisten der Dateien: {str(e)}")

@router.post("/api/process-csv-direct")
async def process_csv_direct(filename: str):
    """
    Verarbeitet eine CSV-Datei direkt aus dem Tourplaene-Verzeichnis.
    
    Args:
        filename: Name der CSV-Datei im Tourplaene-Verzeichnis
        
    Returns:
        JSON mit Verarbeitungsergebnissen
    """
    try:
        # Dateipfad validieren
        csv_path = TOURPLAENE_DIR / filename
        
        if not csv_path.exists():
            raise HTTPException(404, detail=f"Datei nicht gefunden: {filename}")
        
        if not csv_path.suffix.lower() == '.csv':
            raise HTTPException(400, detail="Nur CSV-Dateien werden unterstützt")
        
        # Datei direkt verarbeiten (ohne Upload)
        print(f"[DIRECT PROCESS] Verarbeite {csv_path}")
        
        # Verwende den modernen Tourplan-Parser
        from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
        
        tour_data = parse_tour_plan_to_dict(str(csv_path))
        
        return JSONResponse({
            "success": True,
            "filename": filename,
            "path": str(csv_path),
            "tour_data": tour_data,
            "note": "Datei direkt aus Tourplaene-Verzeichnis verarbeitet"
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        print(f"[DIRECT PROCESS] Fehler: {e}")
        raise HTTPException(500, detail=f"Fehler bei der Verarbeitung: {str(e)}")

@router.post("/api/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload einer CSV-Datei (FALLBACK für externe Dateien).
    
    WARNUNG: Diese Funktion sollte nur für externe Dateien verwendet werden!
    Für Tourpläne verwenden Sie /api/process-csv-direct mit Dateien aus dem Tourplaene-Verzeichnis.
    
    - Speichert nur in STAGING_DIR (UTF-8)
    - Originale bleiben read-only
    - Heuristische Encoding-Erkennung (cp850, utf-8-sig, latin-1)
    - Mojibake-Schutz aktiviert
    """
    try:
        # Warnung für externe Uploads
        print(f"[UPLOAD WARNING] Externer Upload: {file.filename}")
        print("[UPLOAD WARNING] Verwenden Sie /api/process-csv-direct für Tourpläne aus dem Tourplaene-Verzeichnis!")

        # Validierung
        if not file.filename:
            raise HTTPException(400, detail="Kein Dateiname angegeben")

        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(400, detail="only .csv allowed")
        
        # Sicheren Dateinamen generieren
        safe_name = SAFE.sub('_', file.filename)
        timestamp = int(time.time())
        staged_name = f"{timestamp}_{safe_name}"
        staged_path = STAGING / staged_name
        
        # WICHTIG: Stelle sicher, dass staged_path absolut ist
        staged_path = staged_path.resolve()
        
        # Datei lesen und validieren
        content = await file.read()
        if len(content) > MAX_BYTES:
            raise HTTPException(413, detail=f"Datei zu groß (max {MAX_BYTES} Bytes)")
        
        if len(content) == 0:
            raise HTTPException(400, detail="Leere Datei")
        
        # Encoding-Erkennung und Dekodierung
        try:
            decoded_content, encoding = _heuristic_decode(content)
            decoded_content = repair_cp_mojibake(decoded_content)
        except Exception as e:
            print(f"[UPLOAD ERROR] Encoding-Erkennung fehlgeschlagen: {e}, verwende UTF-8 Fallback")
            # Fallback: UTF-8 mit Fehlerbehandlung
            decoded_content = content.decode('utf-8', errors='replace')
            encoding = 'utf-8-fallback'
            decoded_content = repair_cp_mojibake(decoded_content)
        
        # In Staging-Verzeichnis speichern (UTF-8)
        staged_path.write_text(decoded_content, encoding='utf-8')
        
        # Cleanup alter Dateien NACH dem Speichern (nur wenn nötig)
        staging_files = list(STAGING.glob("*.csv"))
        if len(staging_files) > STAGING_MAX_FILES:
            print(f"[UPLOAD] Zu viele Staging-Dateien ({len(staging_files)} > {STAGING_MAX_FILES}), starte Cleanup...")
            cleanup_old_staging_files()
        
        trace_text("UPLOAD-SUCCESS", f"Datei gespeichert: {staged_path}")
        
        # WICHTIG: Gebe absolut normalisierten Pfad zurück (Windows-Backslashes)
        staged_path_str = str(staged_path)
        print(f"[UPLOAD DEBUG] Absoluter Pfad zurückgegeben: {staged_path_str}")
        
        # Zeilen zählen (für Response)
        rows = len(decoded_content.splitlines())
        
        return JSONResponse({
            "success": True,
            "ok": True,
            "filename": file.filename,
            "stored_path": staged_path_str,  # Vereinheitlichtes Feld (Hauptfeld)
            "staged_path": staged_path_str,    # Kompatibilität (Legacy)
            "staging_file": staged_path_str,  # Kompatibilität (Legacy)
            "rows": rows,
            "encoding": encoding,
            "encoding_used": encoding,
            "size": len(content),
            "warning": "Externer Upload! Verwenden Sie /api/process-csv-direct für Tourpläne."
        }, media_type="application/json; charset=utf-8")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        raise HTTPException(500, detail=f"Upload-Fehler: {str(e)}")

@router.get("/api/upload/status")
async def upload_status():
    """
    Status des Upload-Systems.
    """
    staging_files = list(STAGING.glob("*.csv"))
    total_size = sum(f.stat().st_size for f in staging_files)
    
    return JSONResponse({
        "tourplaene_directory": str(TOURPLAENE_DIR),
        "tourplaene_exists": TOURPLAENE_DIR.exists(),
        "staging_directory": str(STAGING),
        "staging_dir": str(STAGING),
        "staging_exists": STAGING.exists(),
        "staging_files_count": len(staging_files),
        "staging_total_size_mb": round(total_size / (1024 * 1024), 2),
        "staging_retention_hours": STAGING_RETENTION_HOURS,
        "staging_max_files": STAGING_MAX_FILES,
        "staging_files": [
            {
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "modified": f.stat().st_mtime,
                "age_hours": round((time.time() - f.stat().st_mtime) / 3600, 1)
            }
            for f in sorted(staging_files, key=lambda x: x.stat().st_mtime, reverse=True)
        ],
        "recommended_method": "Verwenden Sie /api/process-csv-direct für Tourpläne aus dem Tourplaene-Verzeichnis",
        "upload_warning": "Upload nur für externe Dateien verwenden!"
    }, media_type="application/json; charset=utf-8")

@router.post("/api/upload/cleanup")
async def cleanup_staging():
    """
    Manuelles Cleanup des Staging-Verzeichnisses.
    Löscht alte Dateien (älter als STAGING_RETENTION_HOURS) und überschreitet STAGING_MAX_FILES.
    """
    try:
        deleted_count, size_freed = cleanup_old_staging_files()
        size_mb = size_freed / (1024 * 1024)
        
        remaining_files = list(STAGING.glob("*.csv"))
        remaining_size = sum(f.stat().st_size for f in remaining_files)
        remaining_size_mb = remaining_size / (1024 * 1024)
        
        return JSONResponse({
            "success": True,
            "deleted_count": deleted_count,
            "size_freed_mb": round(size_mb, 2),
            "remaining_files": len(remaining_files),
            "remaining_size_mb": round(remaining_size_mb, 2),
            "message": f"{deleted_count} Dateien gelöscht, {size_mb:.2f} MB freigegeben"
        }, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(500, detail=f"Cleanup-Fehler: {str(e)}")