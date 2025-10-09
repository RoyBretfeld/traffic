from __future__ import annotations
import asyncio
import os
from urllib.parse import quote
import httpx
from typing import Iterable, List, Dict
import time
from ingest.guards import assert_no_mojibake, trace_text
from repositories.geo_repo import upsert, normalize_addr
from repositories.geo_fail_repo import skip_set, mark_temp, mark_nohit, clear

# Konfiguration aus ENV oder Defaults
BASE = os.getenv("GEOCODER_BASE", "https://nominatim.openstreetmap.org/search")
CONTACT = os.getenv("GEOCODER_CONTACT", "")
RPS = float(os.getenv("GEOCODER_RPS", "1"))
TIMEOUT = float(os.getenv("GEOCODER_TIMEOUT_S", "20"))

# Retry-Parameter
MAX_RETRIES = 3
BASE_SLEEP = 1.0  # Sekunden (exponentiell)

# HTTP-Headers für Nominatim-Policy
HEADERS = {"User-Agent": f"tourplan-geocoder/1.0 ({CONTACT})".strip()}
DELAY = max(1.0 / RPS, 1.0)  # Nominatim: max 1 rps

async def _geocode_one(addr: str, client: httpx.AsyncClient) -> Dict | None:
    """
    Geokodiert eine einzelne Adresse über Nominatim mit Retry/Backoff.
    
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
    
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = await client.get(url)
            
            # 429 Rate-Limiting behandeln
            if r.status_code == 429:
                ra = r.headers.get('Retry-After')
                delay = float(ra) if ra and ra.isdigit() else BASE_SLEEP * (2 ** (attempt - 1))
                print(f"[GEOCODE] 429 Rate-Limited, warte {delay}s (Versuch {attempt}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                last_err = RuntimeError(f"429 rate-limited; retry in {delay}s")
                continue
            
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
            else:
                return None  # no result
                
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
            last_err = e
            delay = BASE_SLEEP * (2 ** (attempt - 1))
            print(f"[GEOCODE] Timeout/Connection Error, warte {delay}s (Versuch {attempt}/{MAX_RETRIES}): {e}")
            await asyncio.sleep(delay)
            continue
        except Exception as e:
            last_err = e
            print(f"[GEOCODE] Unerwarteter Fehler (Versuch {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                delay = BASE_SLEEP * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
            continue
    
    # Nach allen Retries gescheitert
    print(f"[GEOCODE] Alle {MAX_RETRIES} Versuche fehlgeschlagen für '{addr}': {last_err}")
    raise last_err or RuntimeError("geocode failed")

async def fill_missing(addrs: Iterable[str], *, limit: int = 20, dry_run: bool = False) -> List[Dict]:
    """
    Geokodiert bis zu `limit` fehlende Adressen mit Fail-Cache-Unterstützung.
    
    Args:
        addrs: Iterable von Adressen zu geokodieren
        limit: Maximale Anzahl zu verarbeitender Adressen
        dry_run: Wenn True, keine DB-Updates
        
    Returns:
        Liste mit Ergebnissen + Meta-Informationen
    """
    # Adressen normalisieren und deduplizieren
    unique = []
    seen = set()
    for a in addrs:
        a = normalize_addr(a)
        if a and a not in seen:
            unique.append(a)
            seen.add(a)
    
    # Fail-Cache ausschließen
    skip = skip_set(unique)
    todo = [a for a in unique if a not in skip][:max(0, int(limit))]
    
    print(f"[GEOCODE] {len(unique)} Adressen, {len(skip)} im Fail-Cache, {len(todo)} zu verarbeiten")
    
    out = []
    t0 = time.time()
    
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        for i, addr in enumerate(todo, 1):
            print(f"[GEOCODE] Verarbeite {i}/{len(todo)}: {addr[:50]}...")
            
            try:
                res = await _geocode_one(addr, client)
                
                if res:
                    if not dry_run:
                        upsert(addr, res["lat"], res["lon"])  # Erfolg → Cache füllen
                        clear(addr)  # ggf. Fail-Eintrag löschen
                    print(f"[GEOCODE] ✅ Gespeichert: {addr[:30]}... -> {res['lat']:.4f}, {res['lon']:.4f}")
                    out.append({"address": addr, "result": res, "status": "ok"})
                else:
                    if not dry_run:
                        mark_nohit(addr)  # No-Hit markieren
                    print(f"[GEOCODE] ❌ Nicht gefunden: {addr[:30]}...")
                    out.append({"address": addr, "result": None, "status": "nohit"})
                    
            except Exception as e:
                if not dry_run:
                    mark_temp(addr, minutes=60, reason=type(e).__name__)  # Temporärer Fehler
                print(f"[GEOCODE] 💥 Fehler: {addr[:30]}... -> {e}")
                out.append({"address": addr, "error": str(e), "status": "error"})
            
            # Polite delay zwischen Requests
            if i < len(todo):  # Nicht nach dem letzten Request
                await asyncio.sleep(DELAY)
    
    # Meta-Informationen hinzufügen
    out.append({
        "_meta": {
            "t_sec": round(time.time() - t0, 2),
            "count": len(todo),
            "skipped": len(skip),
            "dry_run": dry_run,
            "delay_sec": DELAY
        }
    })
    
    return out
