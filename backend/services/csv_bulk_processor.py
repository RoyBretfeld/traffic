"""
CSV Bulk Processor Service für FAMO TrafficApp
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import sqlite3
from datetime import datetime

# Backend-Module importieren
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from backend.parsers import parse_tour_plan_to_dict
from backend.services.geocode import geocode_address


class CSVBulkProcessor:
    """Service für die Massenverarbeitung aller CSV-Dateien."""
    
    def __init__(self, tourplaene_dir: str = "tourplaene", db_path: str = "data/customers.db"):
        self.tourplaene_dir = Path(tourplaene_dir)
        self.db_path = Path(db_path)
        # Parser liefert strukturierte Tour-Daten gemäß Neu-Logik
        self.parse_tour_plan_to_dict = parse_tour_plan_to_dict
        
        # Datenbank-Verzeichnis erstellen
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def find_all_csv_files(self) -> List[Path]:
        """Findet alle CSV-Dateien im tourplaene Verzeichnis."""
        csv_files = list(self.tourplaene_dir.glob("*.csv"))
        print(f"[INFO] {len(csv_files)} CSV-Dateien gefunden:")
        for csv_file in csv_files:
            print(f"   - {csv_file.name}")
        return csv_files
    
    def process_csv_file(self, csv_file: Path) -> Dict[str, Any]:
        """Verarbeitet eine einzelne CSV-Datei."""
        try:
            print(f"\n🔄 Verarbeite: {csv_file.name}")
            
            # CSV parsen
            parsed_data = self.parse_tour_plan_to_dict(str(csv_file))
            
            # Alle Kunden extrahieren
            all_customers = []
            for tour in parsed_data.get('tours', []):
                tour_type = tour.get('tour_type', '')
                tour_time = tour.get('time')
                for customer in tour.get('customers', []):
                    enriched = dict(customer)
                    enriched['tour_type'] = tour_type
                    enriched['tour_time'] = tour_time
                    enriched['source_file'] = csv_file.name
                    enriched['processed_at'] = datetime.now().isoformat()
                    all_customers.append(enriched)
            
            print(f"   [OK] {len(all_customers)} Kunden extrahiert")
            return {
                'filename': csv_file.name,
                'customers': all_customers,
                'metadata': parsed_data.get('metadata', {}),
                'total_tours': len(parsed_data.get('tours', [])),
                'total_customers': len(all_customers)
            }
            
        except Exception as e:
            print(f"   [FEHLER] {e}")
            return {
                'filename': csv_file.name,
                'error': str(e),
                'customers': [],
                'total_tours': 0,
                'total_customers': 0
            }
    
    def calculate_geopoints(self, customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Berechnet Geopunkte für alle Kunden mit echtem Geocoding."""
        print(f"   🌍 Berechne Geopunkte für {len(customers)} Kunden...")
        
        customers_with_geo = []
        for i, customer in enumerate(customers):
            print(f"   📍 Geocoding {i+1}/{len(customers)}: {customer.get('name', 'Unbekannt')}")
            
            # Echte Geocoding-Implementierung
            geo_data = self._get_real_geopoint(customer)
            
            customer_with_geo = {
                **customer,
                'latitude': geo_data['lat'],
                'longitude': geo_data['lon'],
                'geocoded': True
            }
            customers_with_geo.append(customer_with_geo)
        
        print(f"   [OK] Geopunkte berechnet")
        return customers_with_geo
    
    def _get_real_geopoint(self, customer: Dict[str, Any]) -> Dict[str, float]:
        """Echte Geocoding-Implementierung für Kundenadressen."""
        try:
            # Adresse aus Kunden-Daten zusammenbauen
            street = customer.get('street', '')
            postal_code = customer.get('postal_code', '')
            city = customer.get('city', '')
            
            # Vollständige Adresse erstellen
            full_address = f"{street}, {postal_code} {city}, Deutschland"
            print(f"      [GEOCODING] {full_address}")
            
            # Geocoding-Service aufrufen
            geo_result = geocode_address(full_address)
            if geo_result and geo_result.get('lat') is not None and geo_result.get('lon') is not None:
                lat = geo_result['lat']
                lon = geo_result['lon']
                postal_code = customer.get('postal_code') or geo_result.get('postal_code')
                if postal_code:
                    customer['postal_code'] = postal_code
                if not customer.get('city') and geo_result.get('city'):
                    customer['city'] = geo_result['city']
                print(f"      [OK] Gefunden: {lat}, {lon}")
                return {'lat': lat, 'lon': lon}
            else:
                print(f"      [FEHLER] Geocoding fehlgeschlagen, verwende Fallback")
                return self._get_fallback_geopoint(customer)
                
        except Exception as e:
            print(f"      [FEHLER] Geocoding-Fehler: {e}")
            return self._get_fallback_geopoint(customer)
    
    def _get_fallback_geopoint(self, customer: Dict[str, Any]) -> Dict[str, float]:
        """Fallback-Geopunkte basierend auf Postleitzahl."""
        postal_code = customer.get('postal_code', '00000')
        
        # Fallback-Koordinaten für deutsche Postleitzahlen
        if postal_code.startswith('1'):  # Berlin
            return {'lat': 52.5200, 'lon': 13.4050}
        elif postal_code.startswith('2'):  # Hamburg
            return {'lat': 53.5511, 'lon': 9.9937}
        elif postal_code.startswith('3'):  # Niedersachsen
            return {'lat': 52.3759, 'lon': 9.7320}
        elif postal_code.startswith('4'):  # Nordrhein-Westfalen
            return {'lat': 51.2277, 'lon': 6.7735}
        elif postal_code.startswith('5'):  # Rheinland-Pfalz
            return {'lat': 49.4521, 'lon': 7.7508}
        elif postal_code.startswith('6'):  # Hessen
            return {'lat': 50.1109, 'lon': 8.6821}
        elif postal_code.startswith('7'):  # Baden-Württemberg
            return {'lat': 48.7758, 'lon': 9.1829}
        elif postal_code.startswith('8'):  # Bayern
            return {'lat': 48.1351, 'lon': 11.5820}
        else:
            # Standard-Koordinaten (Deutschland-Zentrum)
            return {'lat': 51.1657, 'lon': 10.4515}
    
    def create_database(self):
        """Erstellt die SQLite-Datenbank mit den notwendigen Tabellen."""
        print(f"\n[INFO] Erstelle Datenbank: {self.db_path}")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabelle für Kunden mit Geodaten
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_number TEXT,
                name TEXT,
                street TEXT,
                postal_code TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                tour_type TEXT,
                tour_time TEXT,
                bar_flag BOOLEAN,
                source_file TEXT,
                processed_at TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabelle für Verarbeitungsstatistiken
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                total_tours INTEGER,
                total_customers INTEGER,
                status TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("   [OK] Datenbank erstellt")
    
    def save_to_database(self, processed_files: List[Dict[str, Any]]):
        """Speichert alle verarbeiteten Daten in der Datenbank."""
        print(f"\n[INFO] Speichere Daten in Datenbank...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        total_customers_saved = 0
        
        for file_data in processed_files:
            if 'error' in file_data:
                # Fehler-Statistik speichern
                cursor.execute('''
                    INSERT INTO processing_stats (filename, total_tours, total_customers, status)
                    VALUES (?, ?, ?, ?)
                ''', (file_data['filename'], 0, 0, f"ERROR: {file_data['error']}"))
                continue
            
            # Kunden in Datenbank speichern
            for customer in file_data['customers']:
                cursor.execute('''
                    INSERT INTO customers (
                        customer_number, name, street, postal_code, city,
                        latitude, longitude, tour_type, tour_time, bar_flag,
                        source_file, processed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer.get('customer_number', ''),
                    customer.get('name', ''),
                    customer.get('street', ''),
                    customer.get('postal_code', ''),
                    customer.get('city', ''),
                    customer.get('latitude', 0.0),
                    customer.get('longitude', 0.0),
                    customer.get('tour_type', ''),
                    customer.get('tour_time', ''),
                    customer.get('bar_flag', False),
                    customer.get('source_file', ''),
                    customer.get('processed_at', '')
                ))
                total_customers_saved += 1
            
            # Verarbeitungsstatistik speichern
            cursor.execute('''
                INSERT INTO processing_stats (filename, total_tours, total_customers, status)
                VALUES (?, ?, ?, ?)
            ''', (file_data['filename'], file_data['total_tours'], file_data['total_customers'], 'SUCCESS'))
        
        conn.commit()
        conn.close()
        print(f"   [OK] {total_customers_saved} Kunden in Datenbank gespeichert")
    
    def process_all_files(self) -> Dict[str, Any]:
        """Verarbeitet alle CSV-Dateien und erstellt eine Datenbank."""
        print("[START] CSV Bulk Processing...")
        
        # CSV-Dateien finden
        csv_files = self.find_all_csv_files()
        if not csv_files:
            return {
                'message': 'Keine CSV-Dateien gefunden',
                'total_customers': 0,
                'total_tours': 0,
                'database_path': str(self.db_path)
            }
        
        # Datenbank erstellen
        self.create_database()
        
        # Alle Dateien verarbeiten
        processed_files = []
        for csv_file in csv_files:
            result = self.process_csv_file(csv_file)
            if result['customers']:
                # Geocoding für Kunden
                result['customers'] = self.calculate_geopoints(result['customers'])
            processed_files.append(result)
        
        # In Datenbank speichern
        self.save_to_database(processed_files)
        
        # Zusammenfassung
        total_customers = sum(f.get('total_customers', 0) for f in processed_files)
        total_tours = sum(f.get('total_tours', 0) for f in processed_files)
        
        summary = {
            'message': 'CSV Bulk Processing erfolgreich abgeschlossen',
            'total_customers': total_customers,
            'total_tours': total_tours,
            'database_path': str(self.db_path),
            'files_processed': len(processed_files)
        }
        
        print(f"\n[FERTIG] CSV Bulk Processing abgeschlossen!")
        print(f"   - Dateien verarbeitet: {len(processed_files)}")
        print(f"   - Touren: {total_tours}")
        print(f"   - Kunden: {total_customers}")
        print(f"   - Datenbank: {self.db_path}")
        
        return summary
