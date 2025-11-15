#!/usr/bin/env python3
"""
TEHA Bulk Geocoding: Importiert TEHA-Adressen und geocodiert sie einmalig.
Nach dem Import: Alle Adressen kommen aus der DB.

Usage:
    python scripts/teha_bulk_geocode.py <teha_export.csv>
    
    Oder mit Limit:
    python scripts/teha_bulk_geocode.py <teha_export.csv> --limit 50
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict

# Projekt-Root finden
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from backend.pipeline.csv_ingest_strict import parse_csv
from backend.services.synonyms import SynonymStore
from services.geocode_fill import fill_missing
from repositories.geo_repo import bulk_get, upsert
from common.normalize import normalize_address


def build_address(row: Dict) -> str:
    """Baut vollständige Adresse aus CSV-Zeile"""
    street = row.get('street', '').strip()
    postal_code = row.get('postal_code', '').strip()
    city = row.get('city', '').strip()
    
    parts = []
    if street:
        parts.append(street)
    if postal_code and city:
        parts.append(f"{postal_code} {city}")
    elif postal_code:
        parts.append(postal_code)
    elif city:
        parts.append(city)
    
    return ", ".join(parts) if parts else ""


async def process_teha_csv(csv_path: Path, limit: int = None, dry_run: bool = False):
    """
    Verarbeitet TEHA-CSV: Einmalige Geocodierung, dann für immer aus DB.
    
    Args:
        csv_path: Pfad zur TEHA-CSV
        limit: Maximale Anzahl zu geocodierender Adressen (None = alle)
        dry_run: Wenn True, keine DB-Updates
    """
    print("=" * 70)
    print("TEHA BULK GEOCODING")
    print("=" * 70)
    print(f"CSV: {csv_path}")
    print(f"Limit: {limit or 'unbegrenzt'}")
    print(f"Dry-Run: {dry_run}")
    print("=" * 70)
    
    # 1. Synonym-Store initialisieren
    synonym_store = SynonymStore(Path('data/address_corrections.sqlite3'))
    
    # 2. CSV parsen (mit Synonym-Auflösung)
    print("\n[1] CSV parsen...")
    try:
        rows = parse_csv(csv_path, synonym_store)
        print(f"  ✓ {len(rows)} Zeilen gelesen")
    except Exception as e:
        print(f"  ✗ Fehler beim Parsen: {e}")
        return
    
    # 3. Adressen extrahieren
    print("\n[2] Adressen extrahieren...")
    addresses = []
    for row in rows:
        # Wenn Synonym bereits Koordinaten hat → überspringen
        if row.get('lat') and row.get('lon'):
            print(f"  → {row.get('customer', 'N/A')}: Koordinaten bereits aus Synonym")
            if not dry_run:
                # Trotzdem in geo_cache speichern
                addr_str = build_address(row)
                if addr_str:
                    upsert(addr_str, row['lat'], row['lon'], source='synonym')
            continue
        
        # Adresse bauen
        addr_str = build_address(row)
        if not addr_str:
            continue
        
        addresses.append({
            'address': addr_str,
            'customer': row.get('customer', ''),
            'row_no': row.get('row_no', 0)
        })
    
    print(f"  ✓ {len(addresses)} Adressen zu verarbeiten")
    
    # 4. Prüfen was bereits in DB ist
    print("\n[3] Prüfe geo_cache...")
    address_strings = [a['address'] for a in addresses]
    cached = bulk_get(address_strings)
    
    in_db = sum(1 for a in address_strings if a in cached and cached[a])
    missing = len(address_strings) - in_db
    
    print(f"  ✓ {in_db} Adressen bereits in DB")
    print(f"  → {missing} Adressen müssen geocodiert werden")
    
    # 5. Fehlende Adressen geocodieren
    if missing > 0:
        missing_addresses = [a['address'] for a in addresses if a['address'] not in cached or not cached[a['address']]]
        
        if limit:
            missing_addresses = missing_addresses[:limit]
            print(f"\n[4] Geocode bis zu {limit} fehlende Adressen...")
        else:
            print(f"\n[4] Geocode {len(missing_addresses)} fehlende Adressen...")
        
        if not dry_run:
            results = await fill_missing(missing_addresses, limit=limit or len(missing_addresses))
            
            geocoded = sum(1 for r in results if r.get('status') == 'ok')
            nohit = sum(1 for r in results if r.get('status') == 'nohit')
            errors = sum(1 for r in results if r.get('status') == 'error')
            
            print(f"  ✓ {geocoded} erfolgreich geocodiert")
            if nohit > 0:
                print(f"  → {nohit} nicht gefunden (→ Manual Queue)")
            if errors > 0:
                print(f"  ✗ {errors} Fehler")
        else:
            print("  [DRY-RUN] Keine Geocodierung durchgeführt")
    else:
        print("\n[4] Alle Adressen bereits in DB - keine Geocodierung nötig")
    
    # 6. Finale Statistik
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG:")
    print(f"  Gesamt Zeilen: {len(rows)}")
    print(f"  Adressen: {len(addresses)}")
    print(f"  Bereits in DB: {in_db}")
    print(f"  Neu geocodiert: {missing - (limit if limit and missing > limit else missing)}")
    
    if not dry_run:
        # Finale Prüfung
        final_check = bulk_get(address_strings)
        final_in_db = sum(1 for a in address_strings if a in final_check and final_check[a])
        print(f"  Final in DB: {final_in_db}/{len(address_strings)}")
        if final_in_db == len(address_strings):
            print("\n  ✅ ALLE ADRESSEN IN DB - EINMAL GECODIERT, FÜR IMMER GESICHERT")
    
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/teha_bulk_geocode.py <teha_export.csv> [--limit N] [--dry-run]")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Fehler: Datei nicht gefunden: {csv_path}")
        sys.exit(1)
    
    limit = None
    dry_run = False
    
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    
    if "--dry-run" in sys.argv:
        dry_run = True
    
    asyncio.run(process_teha_csv(csv_path, limit=limit, dry_run=dry_run))

