from sqlalchemy import text, bindparam
import os
from typing import Optional, Iterable, Dict
from db.core import ENGINE
import unicodedata, re
from common.normalize import normalize_address

# Abkürzungen für besseres Matching (ohne Transliteration)
_ABBR = [
    (r"str\.", "straße"),   # Str. → Straße
    (r"all?e?\.", "allee"),  # Allee-Abkürzungen
    (r"pl\.", "platz"),     # Pl. → Platz
    (r"weg\.", "weg"),      # Weg-Abkürzungen
    (r"chaussee\.", "chaussee"),  # Chaussee-Varianten
]

# OT-Pattern für Ortsteil-Erkennung
_OT_PATTERNS = [
    r"\s+OT\s+.+$",  # " OT Ortsteil" (vereinfacht)
    r"\s+-\s*OT\s+.+$",  # " - OT Ortsteil" (vereinfacht)
    r"\s+-\s*[A-Za-zäöüßÄÖÜ\s\-ü]+$",  # " - Ortsteil" (ohne OT)
]

# Verwende die zentrale Normalisierung
def canon_addr(s: str) -> str:
    """Kanonische Adress-Normalisierung für Fuzzy-Search (mehr Toleranz)."""
    s = unicodedata.normalize("NFC", (s or ""))
    s = s.lower()
    # Abkürzungen vereinheitlichen
    for pat, rep in _ABBR:
        s = re.sub(pat, rep, s)
    # Mehrfach-Whitespace entfernen
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_addr(address: str | None) -> str:
    """Wrapper für die historische API (setzt auf normalize_address auf)."""

    return normalize_address(address)

def has_ot_part(address: str) -> bool:
    """Prüft ob eine Adresse OT-Teile enthält."""
    for pattern in _OT_PATTERNS:
        if re.search(pattern, address, re.IGNORECASE):
            return True
    return False

def remove_ot_part(address: str) -> str:
    """Entfernt OT-Teile aus einer Adresse."""
    result = address
    for pattern in _OT_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result.strip()

def get_address_variants(address: str, company_name: str = None) -> list:
    """
    Gibt verschiedene Varianten einer Adresse zurück (mit/ohne OT).
    Behandelt auch Mojibake-korrupte Adressen und Firmennamen.
    """
    variants = [address]

    # Firmennamen + Adresse kombinieren (falls Firmenname vorhanden)
    if company_name and company_name.strip():
        company_address = f"{company_name.strip()}, {address}"
        variants.append(company_address)

    if has_ot_part(address):
        # Variante ohne OT hinzufügen
        without_ot = remove_ot_part(address)
        if without_ot != address:
            variants.append(without_ot)
            
            # Auch Firmenname + Adresse ohne OT
            if company_name and company_name.strip():
                company_without_ot = f"{company_name.strip()}, {without_ot}"
                variants.append(company_without_ot)

    # Zusätzlich: Mojibake-korrigierte Varianten für OT-Adressen
    if "OT" in address.upper():
        # Versuche Mojibake-Korrektur für OT-Adressen
        corrected = _attempt_mojibake_correction(address)
        if corrected and corrected != address:
            variants.append(corrected)
            
            # Firmenname + korrigierte Adresse
            if company_name and company_name.strip():
                company_corrected = f"{company_name.strip()}, {corrected}"
                variants.append(company_corrected)

            # Auch ohne OT
            corrected_without_ot = remove_ot_part(corrected)
            if corrected_without_ot != corrected:
                variants.append(corrected_without_ot)
                
                # Firmenname + korrigierte Adresse ohne OT
                if company_name and company_name.strip():
                    company_corrected_without_ot = f"{company_name.strip()}, {corrected_without_ot}"
                    variants.append(company_corrected_without_ot)

    return variants

def _attempt_mojibake_correction(address: str) -> str:
    """Konservative Korrektur klassischer UTF-8-Fehldekodierungen. Optional per Flag abschaltbar."""
    if os.getenv("SAFE_MOJIBAKE_FIX", "1") in ("0","false","False"):
        return address
    fixes = {"Ã¤":"ä","Ã¶":"ö","Ã¼":"ü","ÃŸ":"ß","Ã„":"Ä","Ã–":"Ö","Ãœ":"Ü"}
    for bad, good in fixes.items():
        address = address.replace(bad, good)
    return address

def get(address: str) -> Optional[dict]:
    addr = normalize_address(address)
    with ENGINE.begin() as c:
        row = c.execute(text(
            "SELECT address_norm, lat, lon FROM geo_cache WHERE address_norm=:a"), {"a": addr}
        ).mappings().first()
        return dict(row) if row else None

def upsert(address: str, lat: float, lon: float, source: str = "geocoded", by_user: str = None, company_name: str = None) -> dict:
    addr = normalize_address(address)
    
    # Wenn Firmenname vorhanden, auch Firmenname + Adresse speichern
    company_addresses = []
    if company_name and company_name.strip():
        company_addr = f"{company_name.strip()}, {address}"
        company_addresses.append(normalize_address(company_addr))
    
    with ENGINE.begin() as c:
        # Hauptadresse speichern (ON CONFLICT für sauberes Merge)
        c.execute(text(
            """
            INSERT INTO geo_cache (address_norm, lat, lon, source, by_user)
            VALUES (:a, :lat, :lon, :source, :by_user)
            ON CONFLICT(address_norm) DO UPDATE SET
              lat = excluded.lat,
              lon = excluded.lon,
              source = excluded.source,
              by_user = excluded.by_user,
              updated_at = CURRENT_TIMESTAMP
            """
        ), {"a": addr, "lat": lat, "lon": lon, "source": source, "by_user": by_user})
        
        # Firmenname + Adresse auch speichern (für bessere Suche)
        for company_addr in company_addresses:
            c.execute(text(
                """
                INSERT INTO geo_cache (address_norm, lat, lon, source, by_user)
                VALUES (:a, :lat, :lon, :source, :by_user)
                ON CONFLICT(address_norm) DO UPDATE SET
                  lat = excluded.lat,
                  lon = excluded.lon,
                  source = excluded.source,
                  by_user = excluded.by_user,
                  updated_at = CURRENT_TIMESTAMP
                """
            ), {"a": company_addr, "lat": lat, "lon": lon, "source": source, "by_user": by_user})
    
    return {"address_norm": addr, "lat": lat, "lon": lon, "source": source, "by_user": by_user, "company_addresses": company_addresses}

def upsert_ex(*, address: str, lat: float, lon: float, source: str, precision: str|None, region_ok: int|None) -> dict:
    """
    Erweiterte Upsert-Funktion mit allen neuen Feldern für Persistenz-Policy.
    
    Args:
        address: Normalisierte Adresse
        lat: Breitengrad
        lon: Längengrad
        source: Quelle (synonym, geocoder, cache)
        precision: Präzision (full, zip_centroid, None)
        region_ok: Region-Validierung (1=ok, 0=außerhalb, None=unbekannt)
        
    Returns:
        Dict mit persistierten Daten
    """
    key = normalize_address(address)
    
    with ENGINE.begin() as c:
        c.execute(text(
            """
            INSERT INTO geo_cache(address_norm, lat, lon, source, precision, region_ok, first_seen, last_seen)
            VALUES(:k, :lat, :lon, :src, :prec, :rok, 
                   COALESCE((SELECT first_seen FROM geo_cache WHERE address_norm=:k), CURRENT_TIMESTAMP), 
                   CURRENT_TIMESTAMP)
            ON CONFLICT(address_norm) DO UPDATE SET
              lat = excluded.lat,
              lon = excluded.lon,
              source = excluded.source,
              precision = excluded.precision,
              region_ok = COALESCE(excluded.region_ok, geo_cache.region_ok),
              last_seen = CURRENT_TIMESTAMP
            """
        ), {"k": key, "lat": lat, "lon": lon, "src": source, "prec": precision, "rok": region_ok})
    
    return {
        "address_norm": key, 
        "lat": lat, 
        "lon": lon, 
        "source": source, 
        "precision": precision, 
        "region_ok": region_ok
    }

def bulk_get(addresses: Iterable[str]) -> Dict[str, dict]:
    """Bulk-Lookup mit korrekter IN-Klausel-Bindung und Chunking."""
    addrs = [normalize_address(a) for a in addresses if a]
    if not addrs:
        return {}
    
    # SQLAlchemy expanding bindparam für portable IN-Klausel
    stmt = text(
        "SELECT address_norm, lat, lon, source, precision, region_ok, first_seen, last_seen "
        "FROM geo_cache WHERE address_norm IN :alist"
    ).bindparams(bindparam("alist", expanding=True))
    
    out: Dict[str, dict] = {}
    CHUNK = 800
    with ENGINE.begin() as c:
        for i in range(0, len(addrs), CHUNK):
            chunk = addrs[i:i+CHUNK]
            rows = c.execute(stmt, {"alist": chunk}).mappings().all()
            for r in rows:
                row = dict(r)
                key = canon_addr(row["address_norm"])
                source = row.get("source") or "cache"
                out[key] = {
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "source": source,
                    "src": "cache",
                    "precision": row.get("precision"),
                    "region_ok": row.get("region_ok"),
                    "first_seen": row.get("first_seen"),
                    "last_seen": row.get("last_seen"),
                }
    
    return out
