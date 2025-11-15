#!/usr/bin/env python3
"""CLI-Tool zum Hinzufügen von Synonymen"""

import sys
from pathlib import Path

# Projekt-Root finden
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from backend.services.synonyms import SynonymStore, Synonym

DB = Path('data/address_corrections.sqlite3')

if len(sys.argv) < 5:
    print("Usage: python synonym_upsert.py <alias> <street> <postal_code> <city> [lat] [lon]")
    print("Example: python synonym_upsert.py 'Roswitha' 'Hauptstr 1' '01067' 'Dresden' 51.0500 13.7373")
    sys.exit(1)

alias = sys.argv[1]
street = sys.argv[2]
plz = sys.argv[3]
city = sys.argv[4]
lat = float(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] else None
lon = float(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] else None

S = SynonymStore(DB)
S.upsert(Synonym(
    alias=alias,
    customer_id=None,
    customer_name=None,
    street=street,
    postal_code=plz,
    city=city,
    lat=lat,
    lon=lon
))
print(f"OK: Synonym '{alias}' → {street}, {plz} {city}" + (f" ({lat}, {lon})" if lat and lon else ""))

