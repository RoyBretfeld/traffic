"""Deterministisches CSV-Parsing mit Synonym-Resolver"""

from __future__ import annotations
import csv
import io
import sys
from pathlib import Path
from typing import Dict, Any, List

from backend.services.text_normalize import normalize_token, normalize_key
from backend.services.synonyms import SynonymStore

REQUIRED = ["customer", "street", "postal_code", "city"]


class IngestError(Exception):
    """Fehler beim CSV-Ingest"""
    pass


def _open_bytes(path: Path) -> bytes:
    """Liest Datei als Bytes (BOM-tolerant)"""
    b = path.read_bytes()
    return b


def _decode_bytes(b: bytes) -> str:
    """
    Dekodiert Bytes zu String (utf-8-sig, Fallback cp1252).
    
    Args:
        b: Input-Bytes
        
    Returns:
        Dekodierter String
        
    Raises:
        IngestError: Wenn Decodierung komplett fehlschlägt
    """
    try:
        return b.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Fallback deterministisch: cp1252 → Audit
        txt = b.decode("cp1252", errors="replace")
        sys.stderr.write(f"[WARN] cp1252 fallback used – replaced characters present\n")
        return txt


def parse_csv(path: Path, synonyms: SynonymStore) -> List[Dict[str, Any]]:
    """
    Parst CSV deterministisch mit Synonym-Auflösung.
    
    Args:
        path: Pfad zur CSV-Datei
        synonyms: SynonymStore für Alias-Auflösung
        
    Returns:
        Liste von normalisierten Zeilen mit Synonym-Auflösung
        
    Raises:
        IngestError: Wenn CSV ungültig ist
    """
    txt = _decode_bytes(_open_bytes(path))
    # Normalisiere Zeilenenden
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    
    # Deterministisches CSV-Parsing (kein Sniffing!)
    reader = csv.DictReader(
        io.StringIO(txt),
        delimiter=';',
        quotechar='"',
        escapechar='\\'
    )
    
    if reader.fieldnames is None:
        raise IngestError("Header fehlt")
    
    # Pflichtspalten prüfen
    missing = [c for c in REQUIRED if c not in reader.fieldnames]
    if missing:
        raise IngestError(f"Pflichtspalten fehlen: {missing}")
    
    rows: List[Dict[str, Any]] = []
    quarantine: List[Dict[str, Any]] = []
    
    for row_no, raw in enumerate(reader, start=2):  # 1 = Header
        try:
            cust = normalize_token(raw.get("customer", ""))
            street = normalize_token(raw.get("street", ""))
            plz = normalize_token(raw.get("postal_code", ""))
            city = normalize_token(raw.get("city", ""))
            
            # Synonyme zuerst (höchste Priorität!)
            syn = synonyms.resolve(cust) or synonyms.resolve(street)
            
            if syn:
                # Synonym-Override: Verwende Daten aus Synonym
                street = syn.street or street
                plz = syn.postal_code or plz
                city = syn.city or city
                # Optionale feste Koordinaten aus Synonym
                lat = syn.lat
                lon = syn.lon
            else:
                lat = None
                lon = None
            
            key = normalize_key(street, plz, city, 'DE')
            
            rows.append({
                "row_no": row_no,
                "customer": cust,
                "street": street,
                "postal_code": plz,
                "city": city,
                "country": "DE",
                "key": key,
                "lat": lat,
                "lon": lon,
                "synonym_applied": syn is not None,
            })
            
        except Exception as ex:
            # Fehlerhafte Zeile → Quarantäne
            quarantine.append({
                "row_no": row_no,
                "error": str(ex),
                **(raw or {})
            })
    
    # Deterministische Reihenfolge (Input-Order)
    rows.sort(key=lambda r: r["row_no"])
    
    # Quarantäne ausschreiben
    if quarantine:
        q_path = Path("state/quarantine.csv")
        q_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Header bestimmen
        fieldnames = set()
        for q_row in quarantine:
            fieldnames.update(q_row.keys())
        
        with q_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted(fieldnames))
            w.writeheader()
            w.writerows(quarantine)
        
        sys.stderr.write(f"[QUARANTINE] {len(quarantine)} Zeilen in state/quarantine.csv\n")
    
    return rows

