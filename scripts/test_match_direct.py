#!/usr/bin/env python3
"""Direkter Test des Match-Endpoints ohne HTTP"""
import sys
from pathlib import Path
import urllib.parse

sys.path.insert(0, '.')

file_path = Path("data/staging/1762276347_Tourenplan_04.09.2025.csv").resolve()
print(f"Teste Match-Logik direkt...")
print(f"Datei: {file_path}")
print(f"Existiert: {file_path.exists()}")
print()

try:
    # Simuliere die URL-Dekodierung
    encoded = urllib.parse.quote(str(file_path))
    decoded = urllib.parse.unquote(encoded)
    print(f"Encoded: {encoded[:100]}...")
    print(f"Decoded: {decoded}")
    print()
    
    # Teste Pfad-Verarbeitung
    p = Path(decoded)
    print(f"Path object: {p}")
    print(f"Path exists: {p.exists()}")
    print()
    
    # Teste Parser
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    print("Parser importiert...")
    tour_data = parse_tour_plan_to_dict(str(p))
    print(f"Kunden gefunden: {len(tour_data.get('customers', []))}")
    
    # Teste Normalisierung
    from common.normalize import normalize_address
    print("Normalize importiert...")
    
    # Teste Geo-Repo
    from repositories.geo_repo import bulk_get
    print("Geo-Repo importiert...")
    
    print("✅ Alle Imports erfolgreich!")
    
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()

