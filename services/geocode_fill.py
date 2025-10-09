from __future__ import annotations
import asyncio
import os
from urllib.parse import quote
import httpx
from typing import Iterable, List, Dict
import time
from ingest.guards import assert_no_mojibake, trace_text
from repositories.geo_repo import upsert, normalize_addr

# Konfiguration aus ENV oder Defaults
BASE = os.getenv("GEOCODER_BASE", "https://nominatim.openstreetmap.org/search")
CONTACT = os.getenv("GEOCODER_CONTACT", "")
RPS = float(os.getenv("GEOCODER_RPS", "1"))
TIMEOUT = float(os.getenv("GEOCODER_TIMEOUT_S", "20"))

# HTTP-Headers für Nominatim-Policy
HEADERS = {"User-Agent": f"tourplan-geocoder/1.0 ({CONTACT})".strip()}
DELAY = max(1.0 / RPS, 1.0)  # Nominatim: max 1 rps

async def _geocode_one(addr: str, client: httpx.AsyncClient) -> Dict | None:
    """
    Geokodiert eine einzelne Adresse über Nominatim.
    
    Args:
        addr: Zu geokodierende Adresse
        client: HTTP-Client für die Anfrage
        
    Returns:
        Dict mit lat/lon oder None bei Fehler
    """
    # Guard & Trace
    assert_no_mojibake(addr)
    trace_text("PRE-GEOCODE", addr)
    
    # Encode UTF-8 safely
    q = quote(addr, safe='')
    url = f"{BASE}?q={q}&format=jsonv2"
    if CONTACT:
        url += f"&email={quote(CONTACT)}"
    
    try:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        
        if isinstance(data, list) and data:
            best = data[0]
            try:
                lat = float(best["lat"])
                lon = float(best["lon"])
                return {"lat": lat, "lon": lon}
            except (ValueError, KeyError):
                return None
        return None
        
    except Exception as e:
        print(f"[GEOCODE ERROR] Fehler bei Adresse '{addr}': {e}")
        return None

async def fill_missing(addrs: Iterable[str], *, limit: int = 20, dry_run: bool = False) -> List[Dict]:
    """
    Geokodiert bis zu `limit` fehlende Adressen; schreibe in geo_cache (außer dry_run).
    
    Args:
        addrs: Iterable von Adressen zu geokodieren
        limit: Maximale Anzahl zu verarbeitender Adressen
        dry_run: Wenn True, keine DB-Updates
        
    Returns:
        Liste mit Ergebnissen + Meta-Informationen
    """
    # Adressen normalisieren und deduplizieren
    todo = []
    seen = set()
    for a in addrs:
        a = normalize_addr(a)
        if a and a not in seen:
            todo.append(a)
            seen.add(a)
    
    # Limit anwenden
    todo = todo[:max(0, int(limit))]
    
    out = []
    t0 = time.time()
    
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        for i, addr in enumerate(todo, 1):
            print(f"[GEOCODE] Verarbeite {i}/{len(todo)}: {addr[:50]}...")
            
            res = await _geocode_one(addr, client)
            
            if res and not dry_run:
                upsert(addr, res["lat"], res["lon"])  # Cache aktualisieren
                print(f"[GEOCODE] ✅ Gespeichert: {addr[:30]}... -> {res['lat']:.4f}, {res['lon']:.4f}")
            elif res:
                print(f"[GEOCODE] 🔍 Gefunden (dry_run): {addr[:30]}... -> {res['lat']:.4f}, {res['lon']:.4f}")
            else:
                print(f"[GEOCODE] ❌ Nicht gefunden: {addr[:30]}...")
            
            out.append({"address": addr, "result": res})
            
            # Polite delay zwischen Requests
            if i < len(todo):  # Nicht nach dem letzten Request
                await asyncio.sleep(DELAY)
    
    # Meta-Informationen hinzufügen
    out.append({
        "_meta": {
            "t_sec": round(time.time() - t0, 2),
            "count": len(todo),
            "dry_run": dry_run,
            "delay_sec": DELAY
        }
    })
    
    return out
