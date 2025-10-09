#!/usr/bin/env python3
"""
Intelligentes Geocoding für Problemfälle mit Sonderzeichen und Ortsteilen
"""
import sys
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import time

sys.path.insert(0, '.')
from backend.db.config import get_database_path

def normalize_address(address: str) -> str:
    """Normalisiert Adresse (Umlaute, Leerzeichen, etc.)"""
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
    }
    result = address
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result

def geocode_direct_nominatim(address: str) -> Optional[Dict[str, Any]]:
    """Direktes Geocoding über Nominatim ohne AddressCorrector"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'de'
    }
    headers = {
        'User-Agent': 'TrafficApp/1.0'
    }
    
    try:
        time.sleep(1)  # Rate limiting
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lon': float(result['lon']),
                    'provider': 'nominatim'
                }
    except Exception as e:
        pass
    
    return None

def smart_geocode(address: str, customer_id: int, name: str) -> Optional[Dict[str, Any]]:
    """
    Intelligentes Geocoding mit mehreren Strategien
    """
    strategies = []
    
    # Strategie 1: Original
    strategies.append(("Original", address))
    
    # Strategie 2: Normalisierte Umlaute
    normalized = normalize_address(address)
    if normalized != address:
        strategies.append(("Ohne Umlaute", normalized))
    
    # Strategie 3: OT/Ortsteil entfernen
    if " OT " in address or "-OT " in address or "/OT " in address:
        parts = address.split(",")
        if len(parts) >= 3:
            city_part = parts[-1].strip()
            cleaned = city_part.split(" OT ")[0].split("-OT ")[0].split("/OT ")[0]
            variant = ", ".join(parts[:-1]) + ", " + cleaned
            strategies.append(("ohne OT", variant))
    
    # Strategie 4: / entfernen
    if "/" in address and "OT" not in address:
        parts = address.split(",")
        if len(parts) >= 3:
            city_part = parts[-1].strip()
            if "/" in city_part:
                cleaned = city_part.split("/")[0].strip()
                variant = ", ".join(parts[:-1]) + ", " + cleaned
                strategies.append(("ohne Ortsteil-Suffix", variant))
                
                # Auch normalisierte Version davon
                norm_variant = normalize_address(variant)
                if norm_variant != variant:
                    strategies.append(("ohne Ortsteil + Umlaute", norm_variant))
    
    # Strategie 5: | und alles danach entfernen
    if "|" in address:
        cleaned = address.split("|")[0].strip()
        strategies.append(("ohne Zusatzinfo", cleaned))
    
    # Alle Strategien testen
    for desc, test_address in strategies:
        result = geocode_direct_nominatim(test_address)
        if result:
            print(f"    [OK] {name} - Erfolg mit: {desc}")
            if desc != "Original":
                print(f"         Verwendet: {test_address}")
            return result
    
    return None

print("\n" + "="*80)
print("INTELLIGENTE KORREKTUR DER PROBLEMFÄLLE")
print("="*80 + "\n")

# DB-Verbindung
db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Kunden ohne Koordinaten holen
cursor.execute("""
    SELECT id, name, adresse 
    FROM kunden 
    WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0)
      AND adresse IS NOT NULL 
      AND adresse != ''
    ORDER BY name
""")

problem_customers = cursor.fetchall()

print(f"[1/3] Zu bearbeiten: {len(problem_customers)} Kunden\n")
print(f"[2/3] Starte intelligentes Geocoding...\n")

stats = {
    'total': len(problem_customers),
    'success': 0,
    'failed': 0
}

failed_list = []
successful_updates = []

for i, (cid, name, address) in enumerate(problem_customers, 1):
    # Safe print für Console
    try:
        print(f"[{i}/{stats['total']}] {name[:50]}")
    except:
        print(f"[{i}/{stats['total']}] [Kunde mit Sonderzeichen]")
    
    result = smart_geocode(address, cid, name)
    
    if result:
        # Update in DB
        cursor.execute("""
            UPDATE kunden 
            SET lat = ?, lon = ? 
            WHERE id = ?
        """, (result['lat'], result['lon'], cid))
        
        stats['success'] += 1
        successful_updates.append((cid, name, address))
    else:
        stats['failed'] += 1
        failed_list.append((cid, name, address))
        print(f"    [X] Keine Loesung gefunden")

# Änderungen speichern
conn.commit()
conn.close()

print(f"\n[3/3] Fertig!")
print(f"\n{'='*80}")
print(f"ENDERGEBNIS")
print(f"{'='*80}")
print(f"Verarbeitet:         {stats['total']}")
print(f"  [OK] Erfolgreich:  {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
print(f"  [X] Weiterhin offen: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
print(f"\n{'='*80}\n")

# Übrige exportieren
if failed_list:
    output_file = Path("still_need_manual_fix.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("VERBLEIBENDE PROBLEMFÄLLE\n")
        f.write("="*80 + "\n\n")
        f.write(f"Anzahl: {len(failed_list)}\n\n")
        
        for i, (cid, name, address) in enumerate(failed_list, 1):
            f.write(f"{i}. {name} (ID: {cid})\n")
            f.write(f"   Adresse: {address}\n")
            f.write(f"   Korrigierte Adresse: ___________________________\n\n")
    
    print(f"[EXPORT] {len(failed_list)} verbleibende Fälle in: {output_file}")
else:
    print(f"[SUCCESS] ALLE Adressen erfolgreich geocodiert!")

print(f"\n{'='*80}\n")

