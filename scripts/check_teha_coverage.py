#!/usr/bin/env python3
"""
Prüft ob alle TEHA-Adressen bereits in der DB sind (einmal geocodiert = für immer).

Usage:
    python scripts/check_teha_coverage.py <teha_export.csv>
"""

import sys
from pathlib import Path

# Projekt-Root finden
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from backend.pipeline.csv_ingest_strict import parse_csv
from backend.services.synonyms import SynonymStore
from repositories.geo_repo import bulk_get


def build_address(row: dict) -> str:
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


def check_teha_coverage(csv_path: Path):
    """
    Prüft Coverage: Wie viele TEHA-Adressen sind bereits in der DB?
    
    Ziel: 100% Coverage = Einmal geocodiert, für immer gesichert
    """
    print("=" * 70)
    print("TEHA COVERAGE CHECK")
    print("=" * 70)
    print(f"CSV: {csv_path}")
    print("=" * 70)
    
    # 1. Synonym-Store initialisieren
    synonym_store = SynonymStore(Path('data/address_corrections.sqlite3'))
    
    # 2. CSV parsen
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
    synonym_coords = 0
    
    for row in rows:
        # Wenn Synonym bereits Koordinaten hat
        if row.get('lat') and row.get('lon'):
            synonym_coords += 1
            continue
        
        addr_str = build_address(row)
        if addr_str:
            addresses.append({
                'address': addr_str,
                'customer': row.get('customer', ''),
                'row_no': row.get('row_no', 0)
            })
    
    print(f"  ✓ {len(addresses)} Adressen zu prüfen")
    if synonym_coords > 0:
        print(f"  → {synonym_coords} Adressen haben Koordinaten aus Synonymen")
    
    # 4. DB-Check
    print("\n[3] Prüfe geo_cache...")
    address_strings = [a['address'] for a in addresses]
    
    if not address_strings:
        print("  ✓ Keine Adressen zu prüfen (alle haben Synonym-Koordinaten)")
        print("\n" + "=" * 70)
        print("FAZIT: ✅ 100% Coverage (alle über Synonyme)")
        print("=" * 70)
        return
    
    cached = bulk_get(address_strings)
    
    in_db = 0
    missing = []
    
    for addr_str, data in cached.items():
        if data and data.get('lat') and data.get('lon'):
            in_db += 1
        else:
            missing.append(addr_str)
    
    # 5. Statistik
    total_with_coords = synonym_coords + in_db
    total_needed = synonym_coords + len(addresses)
    coverage = (total_with_coords / total_needed * 100) if total_needed > 0 else 100
    
    print(f"  ✓ {in_db} Adressen bereits in DB")
    print(f"  → {len(missing)} Adressen fehlen noch")
    
    # 6. Fehlende Adressen auflisten
    if missing:
        print(f"\n[4] Fehlende Adressen ({len(missing)}):")
        for i, addr in enumerate(missing[:20], 1):  # Erste 20 zeigen
            print(f"  {i}. {addr}")
        if len(missing) > 20:
            print(f"  ... und {len(missing) - 20} weitere")
    
    # 7. Fazit
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG:")
    print(f"  Gesamt Zeilen: {len(rows)}")
    print(f"  Mit Synonym-Koordinaten: {synonym_coords}")
    print(f"  In DB: {in_db}")
    print(f"  Fehlend: {len(missing)}")
    print(f"  Coverage: {coverage:.1f}%")
    print()
    
    if coverage == 100:
        print("  ✅ 100% COVERAGE - ALLE ADRESSEN GECODIERT")
        print("  ✅ Einmal geocodiert = Für immer gesichert")
    elif coverage >= 90:
        print(f"  ⚠️  {coverage:.1f}% Coverage - Fast vollständig")
        print(f"  → {len(missing)} Adressen müssen noch geocodiert werden")
        print(f"  → Nutze: python scripts/teha_bulk_geocode.py {csv_path}")
    else:
        print(f"  ⚠️  {coverage:.1f}% Coverage - Geocoding nötig")
        print(f"  → {len(missing)} Adressen müssen geocodiert werden")
        print(f"  → Nutze: python scripts/teha_bulk_geocode.py {csv_path}")
    
    print("=" * 70)
    
    return {
        'total': len(rows),
        'synonym_coords': synonym_coords,
        'in_db': in_db,
        'missing': len(missing),
        'coverage': coverage
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_teha_coverage.py <teha_export.csv>")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Fehler: Datei nicht gefunden: {csv_path}")
        sys.exit(1)
    
    check_teha_coverage(csv_path)

