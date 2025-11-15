# services/geocode_persist.py
from __future__ import annotations
from typing import Optional, Dict, Any, Iterable
from sqlalchemy import text
from db.core import ENGINE
from common.normalize import normalize_address
import repositories.geo_repo as repo

# Map von Notizen/Quellen auf Felder
SOURCE_MAP = {
    "synonym": ("synonym", None),
    "zip_centroid": ("geocoder", "zip_centroid"),
    "geocoder": ("geocoder", "full"),
    "cache": ("cache", None),
}

def write_result(address_raw: str, result_items: Iterable[Dict[str,Any]]) -> Optional[Dict[str,Any]]:
    """
    Nimmt das Ergebnis des Geocoders (oder Synonym-Treffers),
    persistiert exakt *eine* Zeile in geo_cache (Upsert) und liefert
    das verwendete Objekt zurück. Bei leerem Ergebnis → Manual-Queue.
    
    Args:
        address_raw: Ursprüngliche Adresse (vor Normalisierung)
        result_items: Iterable von Geocoding-Ergebnissen
        
    Returns:
        Dict mit persistierten Daten oder None bei Fehlschlag
    """
    key = normalize_address(address_raw)
    item = None
    
    # Erstes gültiges Ergebnis verwenden
    for x in (result_items or []):
        if x and x.get("lat") and x.get("lon"):
            item = x
            break
    
    if not item:
        # fehlgeschlagen → Manual-Queue
        from repositories.manual_repo import add_open
        add_open(address_raw, reason="geocode_miss")
        return None

    try:
        lat = float(item.get("lat"))
        lon = float(item.get("lon"))
    except (ValueError, TypeError):
        # Ungültige Koordinaten → Manual-Queue
        from repositories.manual_repo import add_open
        add_open(address_raw, reason="invalid_coordinates")
        return None

    note = item.get("_note") or "geocoder"
    source, precision = SOURCE_MAP.get(note, ("geocoder", "full"))

    # region_ok aus Antwort ableiten, wenn vorhanden
    region_ok = None
    addr = item.get("address") or {}
    state = addr.get("state") or addr.get("state_district")
    if state is not None:
        # Prüfe ob in Sachsen, Thüringen oder Sachsen-Anhalt
        region_ok = 1 if state in ("Sachsen", "Thüringen", "Sachsen-Anhalt") else 0

    # Upsert mit Zusatzfeldern
    repo.upsert_ex(
        address=key, lat=lat, lon=lon,
        source=source, precision=precision, region_ok=region_ok
    )
    
    return {
        "address_norm": key, 
        "lat": lat, 
        "lon": lon, 
        "source": source, 
        "precision": precision, 
        "region_ok": region_ok
    }

def write_synonym_result(address_raw: str, synonym_hit) -> Dict[str,Any]:
    """
    Spezielle Funktion für Synonym-Ergebnisse.
    
    Args:
        address_raw: Ursprüngliche Adresse
        synonym_hit: SynonymHit Objekt
        
    Returns:
        Dict mit persistierten Daten
    """
    key = normalize_address(address_raw)
    
    # Synonym-Ergebnisse haben immer region_ok=1 (da sie in Dresden sind)
    repo.upsert_ex(
        address=key, 
        lat=synonym_hit.lat, 
        lon=synonym_hit.lon,
        source="synonym", 
        precision=None, 
        region_ok=1
    )
    
    return {
        "address_norm": key, 
        "lat": synonym_hit.lat, 
        "lon": synonym_hit.lon, 
        "source": "synonym", 
        "precision": None, 
        "region_ok": 1
    }
