from sqlalchemy import text
from typing import Optional, Iterable, Dict
from db.core import ENGINE
import unicodedata, re

# Abkürzungen für besseres Matching (ohne Transliteration)
_ABBR = [
    (r"str\.", "straße"),   # Str. → Straße
    (r"all?e?\.", "allee"),  # Allee-Abkürzungen
    (r"pl\.", "platz"),     # Pl. → Platz
    (r"weg\.", "weg"),      # Weg-Abkürzungen
    (r"chaussee\.", "chaussee"),  # Chaussee-Varianten
]

# dieselbe Normalisierung wie im Ingest (ohne Transliteration)
def normalize_addr(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s

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

def get(address: str) -> Optional[dict]:
    addr = normalize_addr(address)
    with ENGINE.begin() as c:
        row = c.execute(text(
            "SELECT address_norm, lat, lon FROM geo_cache WHERE address_norm=:a"), {"a": addr}
        ).mappings().first()
        return dict(row) if row else None

def upsert(address: str, lat: float, lon: float) -> dict:
    addr = normalize_addr(address)
    with ENGINE.begin() as c:
        # Portable UPSERT: erst versuchen UPDATE, sonst INSERT
        n = c.execute(text(
            "UPDATE geo_cache SET lat=:lat, lon=:lon, updated_at=CURRENT_TIMESTAMP WHERE address_norm=:a"),
            {"a": addr, "lat": lat, "lon": lon}
        ).rowcount
        if n == 0:
            c.execute(text(
                "INSERT INTO geo_cache (address_norm, lat, lon) VALUES (:a, :lat, :lon)"),
                {"a": addr, "lat": lat, "lon": lon}
            )
    return {"address_norm": addr, "lat": lat, "lon": lon}

def bulk_get(addresses: Iterable[str]) -> Dict[str, dict]:
    addrs = [normalize_addr(a) for a in addresses]
    if not addrs:
        return {}
    with ENGINE.begin() as c:
        # SQLite-kompatible IN-Liste mit Platzhaltern
        placeholders = ",".join([":addr" + str(i) for i in range(len(addrs))])
        params = {f"addr{i}": addr for i, addr in enumerate(addrs)}
        rows = c.execute(text(
            f"SELECT address_norm, lat, lon FROM geo_cache WHERE address_norm IN ({placeholders})"
        ), params).mappings().all()
    return {r["address_norm"]: {"lat": r["lat"], "lon": r["lon"]} for r in rows}
