from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import asyncio
import os
from typing import List, Dict, Any
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import bulk_get
from services.geocode_fill import fill_missing
from ingest.reader import read_tourplan
from common.normalize import normalize_address

# Best-effort Upsert in Stammdaten-Tabelle 'kunden'
def _upsert_kunde(name: str, address: str, lat: float, lon: float) -> None:
    if not name or not address or lat is None or lon is None:
        return
    try:
        from settings import SETTINGS
        import sqlite3
        db_path = SETTINGS.database_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kunden WHERE LOWER(name)=LOWER(?)", (name.strip(),))
        exists = (cursor.fetchone() or [0])[0] > 0
        if exists:
            cursor.execute(
                "UPDATE kunden SET adresse=?, lat=?, lon=? WHERE LOWER(name)=LOWER(?)",
                (address, float(lat), float(lon), name.strip()),
            )
        else:
            cursor.execute(
                "INSERT INTO kunden (name, adresse, lat, lon) VALUES (?,?,?,?)",
                (name.strip(), address, float(lat), float(lon)),
            )
        conn.commit()
        conn.close()
    except Exception:
        # darf UI nie blockieren
        pass

router = APIRouter()

@router.post("/api/tourplan-analysis")
async def api_tourplan_analysis():
    """
    Analysiert alle CSV-Dateien im tourplaene Ordner und geocodiert fehlende Adressen.
    
    - Findet alle CSV-Dateien im ./tourplaene Ordner
    - Parst jede Datei und extrahiert Kunden
    - Geocodiert fehlende Adressen automatisch
    - Gibt Zusammenfassung mit Erkennungsquoten zurück
    """
    try:
        # Tourplaene Ordner finden
        tourplaene_dir = Path("./tourplaene")
        if not tourplaene_dir.exists():
            raise HTTPException(404, detail="Tourplaene Ordner nicht gefunden")
        
        # DEBUG: Nur eine spezifische Datei verarbeiten
        test_file = tourplaene_dir / "Tourenplan 04.09.2025.csv"
        if not test_file.exists():
            raise HTTPException(404, detail=f"Test-Datei nicht gefunden: {test_file}")
        
        print(f"[BULK ANALYSIS] DEBUG: Verarbeite nur {test_file.name}")
        
        all_tours = []
        all_customers = []
        total_geocoded = 0
        total_from_db = 0
        total_failed = 0
        
        try:
            # CSV parsen
            print(f"[BULK ANALYSIS] Parse {test_file.name}")
            tour_data = parse_tour_plan_to_dict(test_file)
            print(f"[BULK ANALYSIS] {test_file.name}: tour_data keys = {list(tour_data.keys()) if tour_data else 'None'}")
            
            if not tour_data:
                print(f"[BULK ANALYSIS] tour_data ist None für {test_file.name}")
                raise HTTPException(500, detail=f"Parsing fehlgeschlagen für {test_file.name}")
            
            if not tour_data.get('tours'):
                print(f"[BULK ANALYSIS] Keine Touren in {test_file.name}: tours = {tour_data.get('tours')}")
                raise HTTPException(500, detail=f"Keine Touren gefunden in {test_file.name}")
            
            print(f"[BULK ANALYSIS] {test_file.name}: {len(tour_data['tours'])} Touren gefunden")
            
            # Alle Adressen sammeln
            all_addresses = []
            for tour in tour_data['tours']:
                if tour.get('customers'):
                    for customer in tour['customers']:
                        # Adresse aus street, postal_code, city zusammenbauen
                        street = customer.get('street', '').strip()
                        postal_code = customer.get('postal_code', '').strip()
                        city = customer.get('city', '').strip()
                        
                        # NaN-Werte abfangen und zu leeren Strings machen + Excel-Apostrophe entfernen
                        def clean_excel_value(val):
                            if not val or str(val).lower() == 'nan':
                                return ''
                            s = str(val).strip()
                            # Excel-Apostrophe entfernen (führende/abschließende Quotes)
                            s = s.strip("'").strip('"')
                            # Mehrfach-Spaces normalisieren
                            s = ' '.join(s.split())
                            return s
                        
                        street = clean_excel_value(street)
                        postal_code = clean_excel_value(postal_code)
                        city = clean_excel_value(city)
                        
                        print(f"[BULK ANALYSIS] Customer: {customer.get('name', 'Unknown')} - Street: '{street}', Postal: '{postal_code}', City: '{city}'")
                        
                        # Adresse nur zusammenbauen wenn mindestens ein Teil vorhanden ist
                        address_parts = [part for part in [street, postal_code, city] if part.strip()]
                        if address_parts:
                            address = ', '.join(address_parts)
                            # Normalisieren (entfernt z. B. "(OT ...)" u. Pipes)
                            from common.normalize import normalize_address
                            addr_norm = normalize_address(address)
                            all_addresses.append(addr_norm)
                            print(f"[BULK ANALYSIS] Adresse hinzugefügt: '{addr_norm}' (raw: '{address}')")
                        else:
                            print(f"[BULK ANALYSIS] Adresse übersprungen: unvollständig")
            
            if not all_addresses:
                print(f"[BULK ANALYSIS] Keine Adressen in {test_file.name}")
                raise HTTPException(500, detail=f"Keine Adressen gefunden in {test_file.name}")
            
            print(f"[BULK ANALYSIS] {test_file.name}: {len(all_addresses)} Adressen gefunden")
            
            # Bereits vorhandene Geocodes abrufen
            existing_geo = bulk_get(all_addresses)
            print(f"[BULK ANALYSIS] {test_file.name}: {len(existing_geo)} bereits geocodiert")
            
            # Fehlende Adressen identifizieren
            missing_addresses = [addr for addr in all_addresses if addr and addr not in existing_geo]
            print(f"[BULK ANALYSIS] {test_file.name}: {len(missing_addresses)} fehlend")
            
            # Fehlende Adressen geocodieren (Batch-Limit beachten)
            batch_limit = int(os.getenv("GEOCODE_BATCH_LIMIT", "50"))
            if missing_addresses:
                print(f"[BULK ANALYSIS] Geocodiere {min(len(missing_addresses), batch_limit)} Adressen")
                geocoded_results = await fill_missing(
                    missing_addresses[:batch_limit], 
                    limit=batch_limit, 
                    dry_run=False
                )
                
                # Geocoding-Ergebnisse zählen
                for result in geocoded_results:
                    if result.get('status') == 'ok':
                        total_geocoded += 1
                    else:
                        total_failed += 1
            
            # Geocodes erneut abrufen (inkl. neu geocodierte)
            updated_geo = bulk_get(all_addresses)
            total_from_db += len(updated_geo)
            print(f"[BULK ANALYSIS] {test_file.name}: {len(updated_geo)} total geocodiert")
            
            # Touren mit Geocodes anreichern
            enriched_tours = []
            for tour in tour_data['tours']:
                if tour.get('customers'):
                    enriched_customers = []
                    for customer in tour['customers']:
                        enriched_customer = customer.copy()
                        
                        # 0) Synonym-Short-Circuit für PF/BAR-Kunden (z. B. Sven/Jochen)
                        try:
                            from common.synonyms import resolve_synonym
                            hit = resolve_synonym(enriched_customer.get('name', ''))
                        except Exception:
                            hit = None
                        if hit:
                            # Stammdaten pflegen
                            _upsert_kunde(enriched_customer.get('name',''), hit.resolved_address, hit.lat, hit.lon)
                            enriched_customer.update({
                                'resolved_address': hit.resolved_address,
                                'lat': hit.lat,
                                'lon': hit.lon,
                                'latitude': hit.lat,   # UI erwartet auch diese Keys
                                'longitude': hit.lon,
                                'is_recognized': True,
                                'from_db': True,
                                'from_geocoding': False,
                                'geo_source': 'synonym',
                            })
                            enriched_customers.append(enriched_customer)
                            all_customers.append(enriched_customer)
                            continue
                        
                        # Geocoding-Status setzen
                        street = customer.get('street', '').strip()
                        postal_code = customer.get('postal_code', '').strip()
                        city = customer.get('city', '').strip()
                        
                        if street and postal_code and city:
                            address = f"{street}, {postal_code} {city}"
                        else:
                            address = None
                            
                        if address and address in updated_geo:
                            geo_data = updated_geo[address]
                            _upsert_kunde(
                                enriched_customer.get('name',''),
                                normalize_address(address),
                                geo_data['lat'],
                                geo_data['lon'],
                            )
                            enriched_customer.update({
                                'lat': geo_data['lat'],
                                'lon': geo_data['lon'],
                                'latitude': geo_data['lat'],
                                'longitude': geo_data['lon'],
                                'is_recognized': True,
                                'from_db': True,
                                'from_geocoding': address in missing_addresses[:batch_limit] if missing_addresses else False
                            })
                        else:
                            enriched_customer.update({
                                'is_recognized': False,
                                'from_db': False,
                                'from_geocoding': False
                            })
                        
                        enriched_customers.append(enriched_customer)
                        all_customers.append(enriched_customer)
                    
                    tour['customers'] = enriched_customers
                    enriched_tours.append(tour)
            
            all_tours.extend(enriched_tours)
            print(f"[BULK ANALYSIS] {test_file.name}: {len(enriched_tours)} Touren verarbeitet")
            
        except Exception as e:
            print(f"[BULK ANALYSIS] Fehler bei {test_file.name}: {e}")
            raise HTTPException(500, detail=f"Fehler bei {test_file.name}: {str(e)}")
        
        # Statistiken berechnen
        total_customers = len(all_customers)
        recognized_customers = len([c for c in all_customers if c.get('is_recognized', False)])
        unrecognized_customers = total_customers - recognized_customers
        success_rate = (recognized_customers / total_customers * 100) if total_customers > 0 else 0
        
        result = {
            "success": True,
            "summary": {
                "total_files": 1,
                "total_tours": len(all_tours),
                "total_customers": total_customers,
                "recognized_customers": recognized_customers,
                "unrecognized_customers": unrecognized_customers,
                "success_rate": round(success_rate, 2),
                "geocoding_stats": {
                    "from_db": total_from_db,
                    "newly_geocoded": total_geocoded,
                    "failed": total_failed
                }
            },
            "tours": all_tours,
            "files_processed": [test_file.name]
        }
        
        print(f"[BULK ANALYSIS] Abgeschlossen: {len(all_tours)} Touren, {total_customers} Kunden, {success_rate:.1f}% erkannt")
        
        return JSONResponse(result, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        print(f"[BULK ANALYSIS] Fehler: {e}")
        raise HTTPException(500, detail=f"Fehler bei Bulk-Analyse: {str(e)}")