from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import asyncio
from typing import List, Dict
from repositories.geo_repo import bulk_get
from repositories.geo_alias_repo import resolve_aliases
from services.geocode_fill import fill_missing
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
import unicodedata
import re

router = APIRouter()

def _norm(s: str) -> str:
    """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
    s = unicodedata.normalize("NFC", (s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s

@router.post("/api/tourplan/bulk-process-all")
async def bulk_process_all_csv_files():
    """
    Verarbeitet alle CSV-Dateien aus dem tourplaene Ordner und geocodiert alle fehlenden Adressen.
    
    - Liest alle CSV-Dateien aus ./tourplaene
    - Extrahiert alle Adressen aus allen Dateien
    - Geocodiert alle fehlenden Adressen
    - Gibt Statistiken zurück
    """
    tourplaene_dir = Path("./tourplaene")
    
    if not tourplaene_dir.exists():
        raise HTTPException(404, detail="tourplaene Ordner nicht gefunden")
    
    # Alle CSV-Dateien finden
    csv_files = list(tourplaene_dir.glob("*.csv"))
    if not csv_files:
        raise HTTPException(404, detail="Keine CSV-Dateien im tourplaene Ordner gefunden")
    
    print(f"[BULK PROCESS] Gefunden: {len(csv_files)} CSV-Dateien")
    
    all_addresses = []
    file_stats = []
    total_customers = 0
    
    # Alle CSV-Dateien verarbeiten
    for csv_file in csv_files:
        try:
            print(f"[BULK PROCESS] Verarbeite: {csv_file.name}")
            
            # CSV mit modernem Parser lesen
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get("customers", [])
            
            # Adressen extrahieren
            file_addresses = []
            for customer in customers:
                full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
                norm_address = _norm(full_address)
                if norm_address:
                    file_addresses.append(norm_address)
                    all_addresses.append(norm_address)
            
            file_stats.append({
                "file": csv_file.name,
                "customers": len(customers),
                "addresses": len(file_addresses),
                "status": "success"
            })
            
            total_customers += len(customers)
            print(f"[BULK PROCESS] {csv_file.name}: {len(customers)} Kunden, {len(file_addresses)} Adressen")
            
        except Exception as e:
            print(f"[BULK PROCESS] Fehler bei {csv_file.name}: {e}")
            file_stats.append({
                "file": csv_file.name,
                "customers": 0,
                "addresses": 0,
                "status": "error",
                "error": str(e)
            })
    
    # Eindeutige Adressen ermitteln
    unique_addresses = list(set(all_addresses))
    print(f"[BULK PROCESS] Eindeutige Adressen: {len(unique_addresses)} von {len(all_addresses)} total")
    
    # Alias-Auflösung
    aliases = resolve_aliases(unique_addresses)
    print(f"[BULK PROCESS] Aliases gefunden: {len(aliases)}")
    
    # Cache-Lookup
    geo = bulk_get(unique_addresses + list(aliases.values()))
    cached_count = len(geo)
    print(f"[BULK PROCESS] Bereits im Cache: {cached_count}")
    
    # Fehlende Adressen identifizieren
    missing_addresses = []
    for addr in unique_addresses:
        canon = aliases.get(addr)
        if addr not in geo and (not canon or canon not in geo):
            missing_addresses.append(addr)
    
    print(f"[BULK PROCESS] Fehlende Adressen: {len(missing_addresses)}")
    
    # Geocoding der fehlenden Adressen
    geocoding_results = []
    if missing_addresses:
        print(f"[BULK PROCESS] Starte Geocoding für {len(missing_addresses)} Adressen...")
        
        # In Batches verarbeiten (je 50 Adressen)
        batch_size = 50
        for i in range(0, len(missing_addresses), batch_size):
            batch = missing_addresses[i:i + batch_size]
            print(f"[BULK PROCESS] Batch {i//batch_size + 1}: {len(batch)} Adressen")
            
            try:
                batch_results = await fill_missing(batch, limit=len(batch), dry_run=False)
                geocoding_results.extend(batch_results)
                
                # Kurze Pause zwischen Batches
                if i + batch_size < len(missing_addresses):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"[BULK PROCESS] Fehler in Batch {i//batch_size + 1}: {e}")
                geocoding_results.append({
                    "address": f"Batch {i//batch_size + 1}",
                    "result": None,
                    "status": "error",
                    "error": str(e)
                })
    
    # Finale Statistiken
    final_geo = bulk_get(unique_addresses + list(aliases.values()))
    final_cached_count = len(final_geo)
    newly_geocoded = final_cached_count - cached_count
    
    success_rate = (final_cached_count / len(unique_addresses)) * 100 if unique_addresses else 0
    
    result = {
        "files_processed": len(csv_files),
        "total_customers": total_customers,
        "total_addresses": len(all_addresses),
        "unique_addresses": len(unique_addresses),
        "initially_cached": cached_count,
        "newly_geocoded": newly_geocoded,
        "final_cached": final_cached_count,
        "success_rate": round(success_rate, 2),
        "file_stats": file_stats,
        "geocoding_results": geocoding_results[:100],  # Nur erste 100 Ergebnisse für Response
        "message": f"Verarbeitet: {len(csv_files)} Dateien, {total_customers} Kunden, {len(unique_addresses)} eindeutige Adressen. Erfolgsquote: {success_rate:.1f}%"
    }
    
    print(f"[BULK PROCESS] Abgeschlossen: {result['message']}")
    
    return JSONResponse(result, media_type="application/json; charset=utf-8")
