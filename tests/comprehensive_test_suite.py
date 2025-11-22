#!/usr/bin/env python3
"""
UMFASSENDE TEST-SUITE FÜR ADRESS-ERKENNUNG
==========================================

Diese Test-Suite prüft alle Aspekte der Adress-Erkennung:
1. Zentrale Normalisierung
2. PLZ + Name-Regel für unvollständige Adressen  
3. CSV-Integration
4. End-to-End Erkennungsrate
5. Performance und Stabilität
"""
import sys
from pathlib import Path
import time
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).parent))

from common.normalize import normalize_address, clear_address_cache
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

class AddressRecognitionTestSuite:
    """Umfassende Test-Suite für Adress-Erkennung"""
    
    def __init__(self):
        self.results = defaultdict(list)
        self.start_time = time.time()
        
    def test_central_normalization(self):
        """Test 1: Zentrale Normalisierung"""
        print('🧪 TEST 1: ZENTRALE NORMALISIERUNG')
        print('=' * 50)
        
        test_cases = [
            # Pipe-Normalisierung
            ('Fröbelstraße 1 | Dresden', 'Fröbelstraße 1, Dresden'),
            ('A | B | C', 'A, B, C'),
            
            # Halle-Entfernung
            ('Hauptstraße 1, Halle 14, 01067 Dresden', 'Hauptstr. 1, 01067 Dresden'),
            
            # OT-Entfernung
            ('Alte Str. 33, 01768 Glashütte (OT Hirschbach)', 'Alte Str. 33, 01768 Glashütte OT Hirschbach'),
            
            # Schreibfehler-Korrekturen
            ('Haupstr. 1, Dresden', 'Hauptstr. 1, Dresden'),
            ('Hauptstrasse 1, Dresden', 'Hauptstr. 1, Dresden'),
            ('Strae 1, Dresden', 'Straße 1, Dresden'),
            
            # Mojibake-Fixes
            ('FrÃ¶belstraÃŸe 1, Dresden', 'Fröbelstraße 1, Dresden'),
            
            # Spezielle Adress-Korrekturen
            ('Hauptstr. 1, 01809 Heidenau', 'Hauptstr. 1, 01809 Heidenau'),
            ('An der Triebe  25, 01468 Moritzburg', 'An der Triebe 25, 01468 Moritzburg'),
        ]
        
        passed = 0
        for input_addr, expected in test_cases:
            result = normalize_address(input_addr)
            success = result == expected
            status = '✅' if success else '❌'
            print(f'{status} "{input_addr}" -> "{result}"')
            if success:
                passed += 1
            else:
                print(f'   Erwartet: "{expected}"')
        
        self.results['normalization'] = [passed, len(test_cases)]
        print(f'\n📊 Normalisierung: {passed}/{len(test_cases)} Tests bestanden')
        return passed == len(test_cases)
    
    def test_plz_name_rule(self):
        """Test 2: PLZ + Name-Regel"""
        print('\n🧪 TEST 2: PLZ + NAME-REGEL')
        print('=' * 50)
        
        clear_address_cache()
        
        test_cases = [
            # Astral UG Fall
            ('', 'Astral UG', '01159', 'Löbtauer Straße 80, 01159 Dresden'),
            ('nan', 'Astral UG', '01159', 'Löbtauer Straße 80, 01159 Dresden'),
            
            # Sven Teichmann Fall
            ('', 'Sven Teichmann', '01468', 'An der Triebe 25, 01468 Moritzburg'),
            
            # Unbekannter Kunde (sollte leer bleiben)
            ('', 'Unbekannter Kunde', '99999', ''),
            
            # Normale Adresse (sollte normalisiert werden)
            ('Hauptstraße 1, Dresden', 'Test GmbH', '01067', 'Hauptstr. 1, Dresden'),
        ]
        
        passed = 0
        for addr, name, plz, expected in test_cases:
            result = normalize_address(addr, name, plz)
            success = result == expected
            status = '✅' if success else '❌'
            print(f'{status} "{addr}" + "{name}" + "{plz}" -> "{result}"')
            if success:
                passed += 1
            else:
                print(f'   Erwartet: "{expected}"')
        
        self.results['plz_name_rule'] = [passed, len(test_cases)]
        print(f'\n📊 PLZ+Name-Regel: {passed}/{len(test_cases)} Tests bestanden')
        return passed == len(test_cases)
    
    def test_csv_integration(self):
        """Test 3: CSV-Integration"""
        print('\n🧪 TEST 3: CSV-INTEGRATION')
        print('=' * 50)
        
        # Test mit Astral UG CSV
        csv_file = 'tourplaene/Tourenplan 09.09.2025.csv'
        
        try:
            tour_data = parse_tour_plan_to_dict(csv_file)
            customers = tour_data.get('customers', [])
            
            # Suche nach Astral UG
            astral_customers = [c for c in customers if 'Astral' in c.get('name', '')]
            
            passed = 0
            total = len(astral_customers)
            
            for customer in astral_customers:
                name = customer.get('name', '')
                street = customer.get('street', '')
                address = customer.get('address', '')
                
                # Prüfe ob PLZ+Name-Regel funktioniert
                if not street or street.lower() in ['nan', '']:
                    success = address == 'Löbtauer Straße 80, 01159 Dresden'
                else:
                    success = 'Löbtauer Straße' in address
                
                status = '✅' if success else '❌'
                print(f'{status} {name}: "{street}" -> "{address}"')
                if success:
                    passed += 1
            
            self.results['csv_integration'] = [passed, total]
            print(f'\n📊 CSV-Integration: {passed}/{total} Tests bestanden')
            return passed == total
            
        except Exception as e:
            print(f'❌ Fehler bei CSV-Integration: {e}')
            self.results['csv_integration'] = [0, 1]
            return False
    
    def test_recognition_rate(self):
        """Test 4: End-to-End Erkennungsrate"""
        print('\n🧪 TEST 4: END-TO-END ERKENNUNGSRATE')
        print('=' * 50)
        
        tour_plan_dir = Path('tourplaene')
        csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
        
        total_customers = 0
        geocoded_customers = 0
        missing_addresses = []
        
        for csv_file in csv_files[:5]:  # Test mit ersten 5 CSV-Dateien
            try:
                tour_data = parse_tour_plan_to_dict(str(csv_file))
                customers = tour_data.get('customers', [])
                
                for customer in customers:
                    total_customers += 1
                    address = customer.get('address', '')
                    
                    if address and address.strip():
                        # Prüfe ob Adresse geocodiert ist
                        if geo_get(address):
                            geocoded_customers += 1
                        else:
                            missing_addresses.append({
                                'name': customer.get('name', ''),
                                'address': address,
                                'file': csv_file.name
                            })
                            
            except Exception as e:
                print(f'⚠️ Fehler bei {csv_file.name}: {e}')
        
        recognition_rate = (geocoded_customers / total_customers * 100) if total_customers > 0 else 0
        
        print(f'📊 Erkennungsrate: {recognition_rate:.1f}%')
        print(f'   Geocodierte Kunden: {geocoded_customers}')
        print(f'   Gesamt Kunden: {total_customers}')
        print(f'   Fehlende Adressen: {len(missing_addresses)}')
        
        if missing_addresses:
            print(f'\n❌ Fehlende Adressen (Top 5):')
            for i, missing in enumerate(missing_addresses[:5]):
                print(f'   {i+1}. {missing["name"]}: {missing["address"]}')
        
        self.results['recognition_rate'] = [recognition_rate, 100.0]
        success = recognition_rate >= 99.0  # Ziel: 99%+
        print(f'\n📊 Erkennungsrate: {"✅ BESTANDEN" if success else "❌ FEHLGESCHLAGEN"}')
        return success
    
    def test_performance(self):
        """Test 5: Performance und Stabilität"""
        print('\n🧪 TEST 5: PERFORMANCE UND STABILITÄT')
        print('=' * 50)
        
        # Test Normalisierungs-Performance
        test_addresses = [
            'Fröbelstraße 1 | Dresden',
            'Hauptstraße 1, Halle 14, 01067 Dresden',
            'Alte Str. 33, 01768 Glashütte (OT Hirschbach)',
            'Haupstr. 1, Dresden',
            'Strae 1, Dresden',
        ] * 100  # 500 Adressen
        
        start_time = time.time()
        for addr in test_addresses:
            normalize_address(addr)
        normalization_time = time.time() - start_time
        
        # Test PLZ+Name-Regel Performance
        clear_address_cache()
        start_time = time.time()
        for _ in range(10):
            # Jetzt über normalize_address testen
            normalize_address('', 'Astral UG', '01159')
        plz_name_time = time.time() - start_time
        
        print(f'📊 Performance-Ergebnisse:')
        print(f'   Normalisierung (500 Adressen): {normalization_time:.3f}s')
        print(f'   PLZ+Name-Regel (10 Aufrufe): {plz_name_time:.3f}s')
        print(f'   Durchschnitt pro Adresse: {normalization_time/500*1000:.2f}ms')
        
        # Performance-Ziele
        perf_success = (
            normalization_time < 1.0 and  # Unter 1 Sekunde für 500 Adressen
            plz_name_time < 0.5  # Unter 0.5 Sekunden für 10 PLZ+Name-Aufrufe
        )
        
        self.results['performance'] = [1 if perf_success else 0, 1]
        print(f'\n📊 Performance: {"✅ BESTANDEN" if perf_success else "❌ FEHLGESCHLAGEN"}')
        return perf_success
    
    def run_all_tests(self):
        """Führe alle Tests aus"""
        print('🚀 UMFASSENDE TEST-SUITE FÜR ADRESS-ERKENNUNG')
        print('=' * 60)
        
        tests = [
            ('Zentrale Normalisierung', self.test_central_normalization),
            ('PLZ + Name-Regel', self.test_plz_name_rule),
            ('CSV-Integration', self.test_csv_integration),
            ('Erkennungsrate', self.test_recognition_rate),
            ('Performance', self.test_performance),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f'❌ {test_name} fehlgeschlagen: {e}')
        
        # Gesamtergebnis
        total_time = time.time() - self.start_time
        print(f'\n🏁 GESAMTERGEBNIS')
        print('=' * 60)
        print(f'✅ Bestandene Tests: {passed_tests}/{total_tests}')
        print(f'⏱️ Gesamtzeit: {total_time:.2f}s')
        print(f'📊 Gesamtstatus: {"✅ ALLE TESTS BESTANDEN" if passed_tests == total_tests else "❌ EINIGE TESTS FEHLGESCHLAGEN"}')
        
        # Detaillierte Ergebnisse
        print(f'\n📋 DETAILLIERTE ERGEBNISSE:')
        for test_name, (passed, total) in self.results.items():
            if isinstance(passed, float):  # Erkennungsrate
                print(f'   {test_name}: {passed:.1f}%')
            else:
                print(f'   {test_name}: {passed}/{total}')
        
        return passed_tests == total_tests

if __name__ == '__main__':
    test_suite = AddressRecognitionTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
