"""
UID-Service: Generierung von tour_uid und stop_uid gemäß Betriebsordnung.

Betriebsordnung §2:
- tour_uid = sha256(tour_id) (Hex, lower)
- stop_uid = sha256(source_id | norm(address) | plz | ort)
"""
import hashlib
from typing import Optional
from common.normalize import normalize_address  # Repair-Layer für Adressen


def generate_tour_uid(tour_id: str) -> str:
    """
    Generiert tour_uid aus tour_id.
    
    Betriebsordnung §2: tour_uid = sha256(tour_id) (Hex, lower)
    
    Args:
        tour_id: Tour-ID (z.B. "W-07.00", "ext-2025-11-01-A")
    
    Returns:
        tour_uid als hexadezimaler SHA256-Hash (lowercase)
    """
    if not tour_id:
        raise ValueError("tour_id darf nicht leer sein")
    
    # SHA256-Hash (Hex, lowercase)
    tour_uid = hashlib.sha256(tour_id.encode('utf-8')).hexdigest().lower()
    return tour_uid


def generate_stop_uid(
    source_id: str,
    address: str,
    postal_code: Optional[str] = None,
    city: Optional[str] = None
) -> str:
    """
    Generiert stop_uid aus normalisierten Daten.
    
    Betriebsordnung §2: stop_uid = sha256(source_id | norm(address) | plz | ort)
    
    Args:
        source_id: Quell-ID (z.B. "ROW-12345")
        address: Adresse (wird normalisiert via Repair-Layer)
        postal_code: Postleitzahl (optional)
        city: Stadt (optional)
    
    Returns:
        stop_uid als hexadezimaler SHA256-Hash (lowercase)
    """
    if not source_id:
        raise ValueError("source_id darf nicht leer sein")
    
    # Repair-Layer: Normalisiere Adresse
    norm_address = normalize_address(address) if address else ""
    
    # Normalisiere PLZ und Ort (trim, lower)
    norm_plz = (postal_code or "").strip()
    norm_city = (city or "").strip()
    
    # Key: source_id | norm(address) | plz | ort
    key = f"{source_id}|{norm_address}|{norm_plz}|{norm_city}"
    
    # SHA256-Hash (Hex, lowercase)
    stop_uid = hashlib.sha256(key.encode('utf-8')).hexdigest().lower()
    return stop_uid


def validate_tour_uid(tour_uid: str) -> bool:
    """
    Validiert ob tour_uid gültiges Format hat (64 hex chars, lowercase).
    """
    if not tour_uid:
        return False
    return len(tour_uid) == 64 and all(c in '0123456789abcdef' for c in tour_uid.lower())


def validate_stop_uid(stop_uid: str) -> bool:
    """
    Validiert ob stop_uid gültiges Format hat (64 hex chars, lowercase).
    """
    if not stop_uid:
        return False
    return len(stop_uid) == 64 and all(c in '0123456789abcdef' for c in stop_uid.lower())

