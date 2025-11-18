"""
Multi-Tour Generator API Router
KI-basierte Aufteilung großer Touren in optimale Untertouren
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Dict, Any, List
import sqlite3
import json
from datetime import datetime

from backend.db.dao import insert_tour, _connect, get_database_path
from backend.services.geocode import geocode_address
from backend.services.ai_optimizer import AIOptimizer, Stop
from backend.services.optimization_rules import default_rules

router = APIRouter()


def _db_path() -> Path:
    """Gibt den Pfad zur Datenbank zurück."""
    return Path(get_database_path())


def _dedupe_preserve_order(items: List[int]) -> List[int]:
    """Entfernt Duplikate in einer ID-Liste und behält die Reihenfolge bei."""
    seen: set[int] = set()
    result: List[int] = []
    for value in items:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _normalize_address(adresse: str) -> str:
    """Normalisiert eine Adresse für den Vergleich."""
    if not adresse:
        return ""
    return adresse.strip().lower().replace(" ", "")


def _dedupe_customers_by_address(rows: List[tuple]) -> List[tuple]:
    """Dedupeliste für (id, name, adresse) anhand der Adresse, Reihenfolge bleibt erhalten."""
    seen_addr: set[str] = set()
    result: List[tuple] = []
    for cid, name, adresse in rows:
        key = _normalize_address(adresse)
        if key and key not in seen_addr:
            seen_addr.add(key)
            result.append((cid, name, adresse))
    return result


def _normalize_base_name(original_name: str) -> str:
    """Normalisiert einen Tour-Namen für die Suffix-Generierung."""
    name = (original_name or "Tour").strip()
    # Häufige Muster vereinfachen
    name = name.replace(" Uhr Tour", "").replace(" Uhr", "").replace("Tour", "").strip()
    name = name.replace(".", ":")
    # Mehrfach-Leerzeichen entfernen
    name = " ".join(name.split())
    return name


def _next_suffix(base: str, con: sqlite3.Connection) -> str:
    """Gibt den nächsten verfügbaren Suffix (A, B, C, ...) zurück."""
    # Alle existierenden Namen mit diesem Prefix holen
    rows = con.execute("select tour_id from touren where tour_id like ?", (f"{base}-%",)).fetchall()
    used = set()
    for (tour_name,) in rows:
        try:
            suffix = tour_name.split("-")[-1]
            if len(suffix) == 1 and suffix.isalpha():
                used.add(suffix.upper())
        except Exception:
            pass
    
    # Nächsten freien Buchstaben finden
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if letter not in used:
            return letter
    
    # Fallback: Wenn alle Buchstaben verwendet wurden, verwende AA, AB, etc.
    for i in range(26):
        for j in range(26):
            suffix = chr(65 + i) + chr(65 + j)
            if suffix not in used:
                return suffix
    
    return "ZZ"  # Fallback


def _purge_generated_tours(con: sqlite3.Connection, base: str, current_date: str) -> None:
    """Löscht alle zuvor generierten Touren für einen bestimmten Basisnamen und das aktuelle Datum."""
    con.execute("DELETE FROM touren WHERE tour_id LIKE ? AND datum = ?", (f"{base}%", current_date))
    con.commit()


@router.post("/tour/{tour_id}/generate_multi_ai", tags=["ai"], summary="KI: Stopps in mehrere Touren aufteilen und speichern")
async def generate_multi_ai(tour_id: int) -> Dict[str, Any]:
    """
    Multi-Tour Generator: Teilt eine große Tour mit vielen Kunden in mehrere optimierte Untertouren auf.
    
    Verwendet KI-basiertes Clustering für geografische Optimierung.
    """
    print(f"[INFO] Multi-Tour-Generator API aufgerufen für Tour ID: {tour_id}")
    try:
        db = _db_path()
        if not db.exists():
            raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
        
        con = sqlite3.connect(str(db))
        row = con.execute("select tour_id, datum, kunden_ids from touren where id=?", (tour_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tour nicht gefunden")
        
        base_name, datum, kid_json = row
        
        try:
            ids = json.loads(kid_json) if kid_json else []
            ids = _dedupe_preserve_order(ids)
        except Exception:
            ids = []
        
        if not ids:
            raise HTTPException(status_code=400, detail="Keine Kunden in Tour")
        
        # Kunden laden und per Adresse deduplizieren
        placeholders = ",".join(["?"] * len(ids))
        rows = con.execute(
            f"select id, name, adresse from kunden where id in ({placeholders})",
            tuple(ids),
        ).fetchall()
        customers = _dedupe_customers_by_address(rows)
        
        # Stopps aufbereiten
        stops = []
        for idx, (cid, name, adr) in enumerate(customers):
            geo_result = geocode_address(adr)
            if geo_result is None:
                continue
            # geocode_address gibt ein Dict zurück, nicht ein Tuple
            if isinstance(geo_result, dict):
                lat = geo_result.get('lat')
                lon = geo_result.get('lon')
            else:
                lat, lon = geo_result
            
            if lat is None or lon is None:
                continue
            
            stops.append(Stop(id=str(cid), name=name, address=adr, lat=lat, lon=lon, sequence=idx + 1))
        
        if len(stops) < 2:
            raise HTTPException(status_code=400, detail="Zu wenige geocodierte Stopps")
        
        print(f"[KI] Starte KI-Clustering für {len(stops)} Stopps...")
        optimizer = AIOptimizer(use_local=True)
        result = await optimizer.cluster_stops_into_tours(stops, default_rules)
        print(f"[OK] KI-Clustering Ergebnis: {result}")
        
        tours = result.get("tours", [])
        if not tours:
            print("[WARNUNG] Keine Touren von KI generiert")
            return JSONResponse({
                "created": [],
                "tours": [],
                "reason": result.get("reasoning", "Keine Vorschläge")
            })
        
        print(f"[KI] KI hat {len(tours)} Touren vorgeschlagen")
        
        # Vorherige generierte Touren entfernen und bei A beginnen
        base = _normalize_base_name(base_name or "Tour")
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        with _connect() as con:
            _purge_generated_tours(con, base, current_date_str)
        
        created_ids: List[int] = []
        for t in tours:
            with _connect() as con:
                suffix = _next_suffix(base, con)
            new_name = f"{base}-{suffix}"
            cust_ids = [int(x) for x in t.get("customer_ids", []) if isinstance(x, (int, str)) and str(x).isdigit()]
            print(f"[TOUR] Erstelle Tour: {new_name} mit {len(cust_ids)} Kunden")
            created_id = insert_tour(tour_id=new_name, datum=str(datum or ""), kunden_ids=cust_ids)
            created_ids.append(created_id)
        
        print(f"[OK] Multi-Tour-Generator abgeschlossen: {len(created_ids)} Touren erstellt")
        return JSONResponse({
            "created": created_ids,
            "tours": tours,
            "reason": result.get("reasoning")
        })
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Multi-Tour-Generator Fehler: {e}")
        print(f"[ERROR TRACE] {error_trace}")
        raise HTTPException(status_code=500, detail=f"KI-Aufteilung fehlgeschlagen: {e}")

