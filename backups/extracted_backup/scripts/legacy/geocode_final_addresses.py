#!/usr/bin/env python3
"""
Geocoding für die finalen problematischen Adressen
"""
import sys
import asyncio
import httpx
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from services.geocode_fill import _geocode_one
from repositories.geo_repo import upsert

async def geocode_final_addresses():
    """Geocode die finalen problematischen Adressen"""
    print(f"🧪 Geocode finale problematische Adressen...")
    
    addresses = [
        ("Gersdorf 43, 01819 Bahretal OT Gersdorf", "Schütze Gersdorf"),
        ("Alte Str. 33, 01768 Glashütte OT Hirschbach", "Auto Service Meusel"),
        ("Reinberger Dorfstraße 6a, 01744 Dippoldiswalde/OT Reinberg", "Karsten Noack"),
        ("Johnsbacher Hauptstraße 55, 01768 Glashütte", "Metallbau Kummer"),
        ("Schulstraße 25, 01468 Moritzburg", "Autoservice Mehlig"),
        ("Zur Quelle 5, 01731 Kreischa OT Saida", "Schmiede Vogel"),
        ("Goppelner Hauptstr. 2, 01728 Bannewitz OT Goppeln", "Sachsenstapler GmbH"),
        ("Strand 20, 01796 Struppen", "Muschialik,Jürg Jens"),
        ("Am Graben 37, 01705 Freital Sömmsdorf", "Enrico Lust"),
        ("Kesselsdorfer Str. 10, 01723 Wilsdruff", "A. Eckoldt"),
        ("Hauptstr. 89, 01744 Dippoldiswalde", "AS Frank Zimmermann"),
        ("Hauptstr. 11, 01728 Bannewitz", "Tilo Hofmann"),
    ]
    
    success_count = 0
    
    try:
        async with httpx.AsyncClient() as client:
            for i, (address, company) in enumerate(addresses, 1):
                print(f"\n{i:2d}. {address}")
                print(f"    Firma: {company}")
                
                try:
                    result = await _geocode_one(address, client, company)
                    
                    if result and result.get('lat') and result.get('lon'):
                        print(f"    ✅ Geocoding erfolgreich!")
                        print(f"    Koordinaten: {result['lat']}, {result['lon']}")
                        
                        # Im Geo-Cache speichern
                        upsert(address, float(result['lat']), float(result['lon']))
                        print(f"    💾 Im Geo-Cache gespeichert")
                        success_count += 1
                    else:
                        print(f"    ❌ Geocoding fehlgeschlagen")
                        
                except Exception as e:
                    print(f"    ❌ Fehler: {e}")
    
    except Exception as e:
        print(f"❌ Allgemeiner Fehler: {e}")
    
    print(f"\n📊 ERGEBNIS:")
    print(f"  Erfolgreich geocodiert: {success_count}/{len(addresses)}")
    print(f"  Erfolgsrate: {(success_count/len(addresses)*100):.1f}%")

if __name__ == "__main__":
    asyncio.run(geocode_final_addresses())
