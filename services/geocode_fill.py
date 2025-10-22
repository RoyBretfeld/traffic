from __future__ import annotations
import asyncio
import os
from urllib.parse import quote
import httpx
from typing import Iterable, List, Dict
import time
import logging
from ingest.guards import assert_no_mojibake, trace_text
from repositories.geo_repo import upsert, get_address_variants
from repositories.geo_fail_repo import skip_set, mark_temp, mark_nohit, clear
from repositories.manual_repo import add_open as manual_add
from common.normalize import normalize_address
from common.synonyms import resolve_synonym

# Konfiguration aus ENV oder Defaults
BASE = os.getenv("GEOCODER_BASE", "https://nominatim.openstreetmap.org/search")
CONTACT = os.getenv("GEOCODER_CONTACT", "")
RPS = float(os.getenv("GEOCODER_RPS", "1"))
TIMEOUT = float(os.getenv("GEOCODER_TIMEOUT_S", "20"))

# Retry-Parameter
MAX_RETRIES = 3
BASE_SLEEP = 1.0  # Sekunden (exponentiell)

# HTTP-Headers für Nominatim-Policy (höflicher UA)
HEADERS = {"User-Agent": "TrafficApp/1.0 (+contact@example.com)"}
DELAY = max(1.0 / RPS, 1.0)  # Nominatim: max 1 rps

# Manual-Queue Konfiguration
ENFORCE_MANUAL = os.getenv("GEOCODE_NO_RESULT_TO_MANUAL", "1") not in ("0","false","False")

async def _geocode_one(addr: str, client: httpx.AsyncClient, company_name: str = None) -> Dict | None:
    """
    Geokodiert eine einzelne Adresse über Nominatim mit Retry/Backoff und OT-Fallback.
    Verwendet die zentrale Adress-Normalisierung für bessere Erfolgsrate.

    Args:
        addr: Zu geokodierende Adresse
        client: HTTP-Client für die Anfrage
        company_name: Optionaler Firmenname für bessere Geocoding-Erfolge

    Returns:
        Dict mit lat/lon oder None bei Fehler
    """
    # 0) Synonym-Short-Circuit (PF/BAR etc.)
    hit = resolve_synonym(addr)
    if hit:
        # Persist-Writer verwenden für Synonyme
        from services.geocode_persist import write_synonym_result
        result = write_synonym_result(addr, hit)
        logging.info(f"[GEOCODE] Synonym-Treffer: '{addr}' -> '{hit.resolved_address}' ({hit.lat}, {hit.lon})")
        return {"lat": str(hit.lat), "lon": str(hit.lon), "_note": "synonym", "address": {"road": hit.resolved_address}}

    # 1. Zentrale Normalisierung anwenden
    normalized_addr = normalize_address(addr)
    trace_text("GEOCODE", f"Original: {addr}")
    trace_text("GEOCODE", f"Normalisiert: {normalized_addr}")
    
    # 2. OT-Varianten testen (mit und ohne OT) - VOR Mojibake-Guard
    # Jetzt auch mit Firmennamen für bessere Erfolgsrate
    variants = get_address_variants(normalized_addr, company_name)

    for i, variant in enumerate(variants):
        try:
            # Mojibake-Guard nur für die Variante, nicht für die Original-Adresse
            assert_no_mojibake(variant)
            trace_text("PRE-GEOCODE", f"Variante {i+1}: {variant}")

            result = await _geocode_variant(variant, client, is_fallback=(i > 0))
            if result:
                if i > 0:  # Fallback-Variante erfolgreich
                    logging.info(f"[GEOCODE] Fallback erfolgreich: '{addr}' -> '{variant}'")
                # Persist-Writer verwenden für erfolgreiche Geocodes
                from services.geocode_persist import write_result
                persisted = write_result(addr, [result])
                return result
        except Exception as e:
            logging.warning(f"[GEOCODE] Variante {i+1} fehlgeschlagen: {e}")
            continue

    # Kein Ergebnis gefunden → Persist-Writer für Manual-Queue
    from services.geocode_persist import write_result
    write_result(addr, [])
    return None

async def _geocode_variant(addr: str, client: httpx.AsyncClient, is_fallback: bool = False) -> Dict | None:
    """
    Geokodiert eine Adress-Variante über Nominatim.
    
    Args:
        addr: Zu geokodierende Adresse
        client: HTTP-Client für die Anfrage
        is_fallback: True wenn dies eine Fallback-Variante ist
        
    Returns:
        Dict mit lat/lon oder None bei Fehler
    """
    # Verbesserte Nominatim-Suche mit PLZ-Priorität
    q = quote(addr, safe='')
    
    # Zuerst mit vollständiger Adresse suchen (inkl. PLZ)
    url = f"{BASE}?q={q}&format=jsonv2&addressdetails=1&limit=1"
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
                delay = max(delay, 1.0)  # Mindestens 1 Sekunde
                logging.warning(f"[GEOCODE] 429 Rate-Limited, warte {delay}s (Versuch {attempt}/{MAX_RETRIES})")
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
                    
                    # Zusätzliche Validierung: Prüfe ob PLZ in der Antwort enthalten ist
                    display_name = best.get("display_name", "").lower()
                    addr_lower = addr.lower()
                    
                    # Wenn PLZ in der Adresse ist, sollte sie auch in der Antwort sein
                    import re
                    plz_pattern = re.compile(r'\b\d{5}\b')
                    addr_plz = plz_pattern.findall(addr)
                    
                    if addr_plz:
                        # PLZ sollte in der Antwort enthalten sein
                        if not any(plz in display_name for plz in addr_plz):
                            logging.warning(f"[GEOCODE] WARN: PLZ {addr_plz} nicht in Antwort gefunden: {display_name[:100]}")
                            # Trotzdem verwenden, aber warnen
                    
                    # KRITISCH: Rückgabe des gesamten Ergebnis-Dicts für geocode_persist
                    return {
                        "lat": lat, 
                        "lon": lon, 
                        "address": best.get("address", {}),
                        "_note": "geocoder",
                        "display_name": display_name
                    }
                except (ValueError, KeyError):
                    return None
            else:
                return None  # no result
                
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
            last_err = e
            delay = BASE_SLEEP * (2 ** (attempt - 1))
            logging.warning(f"[GEOCODE] Timeout/Connection Error, warte {delay}s (Versuch {attempt}/{MAX_RETRIES}): {e}")
            await asyncio.sleep(delay)
            continue
        except Exception as e:
            last_err = e
            logging.error(f"[GEOCODE] Unerwarteter Fehler (Versuch {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                delay = BASE_SLEEP * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
            continue
    
    # Nach allen Retries gescheitert
    logging.error(f"[GEOCODE] Alle {MAX_RETRIES} Versuche fehlgeschlagen für '{addr}': {last_err}")
    raise last_err or RuntimeError("geocode failed")

async def fill_missing(addrs: Iterable[str], *, limit: int = 20, dry_run: bool = False, company_names: Dict[str, str] = None) -> List[Dict]:
    """
    Geokodiert bis zu `limit` fehlende Adressen mit Fail-Cache-Unterstützung.
    
    Args:
        addrs: Iterable von Adressen zu geokodieren
        limit: Maximale Anzahl zu verarbeitender Adressen
        dry_run: Wenn True, keine DB-Updates
        company_names: Dict mit Adresse -> Firmenname Mapping für bessere Geocoding-Erfolge
        
    Returns:
        Liste mit Ergebnissen + Meta-Informationen
    """
    # Adressen normalisieren und deduplizieren
    unique = []
    seen = set()
    for a in addrs:
        a = normalize_address(a) # Changed from normalize_addr
        if a and a not in seen:
            unique.append(a)
            seen.add(a)
    
    # Fail-Cache ausschließen
    skip = skip_set(unique)
    todo = [a for a in unique if a not in skip][:max(0, int(limit))]
    
    logging.info(f"[GEOCODE] {len(unique)} Adressen, {len(skip)} im Fail-Cache, {len(todo)} zu verarbeiten")
    
    out = []
    t0 = time.time()
    
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        for i, addr in enumerate(todo, 1):
            logging.info(f"[GEOCODE] Verarbeite {i}/{len(todo)}: {addr[:50]}...")
            
            try:
                # Firmenname für diese Adresse holen (falls vorhanden)
                company_name = company_names.get(addr) if company_names else None
                res = await _geocode_one(addr, client, company_name)
                
                if res:
                    if not dry_run:
                        upsert(addr, res["lat"], res["lon"])  # Erfolg → Cache füllen
                        clear(addr)  # ggf. Fail-Eintrag löschen
                    logging.info(f"[GEOCODE] OK Gespeichert: {addr[:30]}... -> {res['lat']:.4f}, {res['lon']:.4f}")
                    out.append({"address": addr, "result": res, "status": "ok"})
                else:
                    if not dry_run:
                        mark_nohit(addr)  # No-Hit markieren
                        if ENFORCE_MANUAL:
                            manual_add(addr, reason='no_result')
                    logging.warning(f"[GEOCODE] MISS Nicht gefunden: {addr[:30]}...")
                    out.append({"address": addr, "result": None, "status": "nohit"})
                    
            except Exception as e:
                if not dry_run:
                    mark_temp(addr, minutes=60, reason=type(e).__name__)  # Temporärer Fehler
                logging.error(f"[GEOCODE] ERROR Fehler: {addr[:30]}... -> {e}")
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
