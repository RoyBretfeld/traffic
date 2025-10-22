#!/usr/bin/env python3
"""
Sentinel-Tests für Encoding-Regress
Verhindert Mojibake in der /api/tourplan/match JSON-Response
"""

import pytest
import tempfile
import os
from pathlib import Path
import requests
import json


class TestEncodingSentinels:
    """Sentinel-Tests für Encoding-Regress"""
    
    def test_no_mojibake_in_api_response(self):
        """Teste dass keine Mojibake-Marker in der API-Response sind"""
        # Mojibake-Marker die nicht in der Response sein dürfen
        BAD_MARKERS = ["Ã", "┬", "├", ""]
        
        # Teste mit bestehender CSV-Datei
        test_file = Path("tourplaene/Tourenplan 04.09.2025.csv")
        if not test_file.exists():
            pytest.skip(f"Test-Datei {test_file} nicht gefunden")
        
        # Server-URL
        base_url = "http://127.0.0.1:8111"
        
        try:
            # Teste parse-csv-tourplan Endpoint
            with open(test_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{base_url}/api/parse-csv-tourplan", files=files, timeout=30)
            
            assert response.status_code == 200, f"API gibt Status {response.status_code}: {response.text}"
            
            # Überprüfe Response-Text auf Mojibake
            response_text = response.text
            
            found_markers = []
            for marker in BAD_MARKERS:
                if marker in response_text:
                    found_markers.append(marker)
            
            assert not found_markers, f"Mojibake-Marker gefunden: {found_markers}"
            
            # Überprüfe auch JSON-Parsing
            data = response.json()
            assert "tours" in data
            assert "customers" in data
            
            # Überprüfe spezifische Felder auf Mojibake
            for customer in data.get("customers", []):
                for field in ["name", "street", "city"]:
                    if field in customer:
                        value = customer[field]
                        for marker in BAD_MARKERS:
                            assert marker not in value, f"Mojibake in {field}: {value}"
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Server nicht erreichbar: {e}")
    
    def test_no_mojibake_in_process_csv_response(self):
        """Teste dass keine Mojibake-Marker in der process-csv-modular Response sind"""
        # Mojibake-Marker die nicht in der Response sein dürfen
        BAD_MARKERS = ["Ã", "┬", "├", ""]
        
        # Teste mit bestehender CSV-Datei
        test_file = Path("tourplaene/Tourenplan 04.09.2025.csv")
        if not test_file.exists():
            pytest.skip(f"Test-Datei {test_file} nicht gefunden")
        
        # Server-URL
        base_url = "http://127.0.0.1:8111"
        
        try:
            # Teste process-csv-modular Endpoint
            with open(test_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{base_url}/api/process-csv-modular", files=files, timeout=30)
            
            assert response.status_code == 200, f"API gibt Status {response.status_code}: {response.text}"
            
            # Überprüfe Response-Text auf Mojibake
            response_text = response.text
            
            found_markers = []
            for marker in BAD_MARKERS:
                if marker in response_text:
                    found_markers.append(marker)
            
            assert not found_markers, f"Mojibake-Marker gefunden: {found_markers}"
            
            # Überprüfe auch JSON-Parsing
            data = response.json()
            assert "workflow_results" in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Server nicht erreichbar: {e}")
    
    def test_encoding_consistency(self):
        """Teste dass Encoding konsistent ist"""
        # Teste mit verschiedenen Encodings
        test_cases = [
            ("cp850", "Fröbelstraße 1, Dresden"),
            ("utf-8", "Müllerstraße 2, Berlin"),
            ("latin1", "Straße 3, München")
        ]
        
        for encoding, test_address in test_cases:
            # Erstelle temporäre CSV mit spezifischem Encoding
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding=encoding) as tmp_file:
                tmp_file.write("Kunde;Adresse\n")
                tmp_file.write(f"Test;{test_address}\n")
                tmp_file_path = tmp_file.name
            
            try:
                # Server-URL
                base_url = "http://127.0.0.1:8111"
                
                try:
                    # Teste parse-csv-tourplan Endpoint
                    with open(tmp_file_path, 'rb') as f:
                        files = {'file': f}
                        response = requests.post(f"{base_url}/api/parse-csv-tourplan", files=files, timeout=30)
                    
                    assert response.status_code == 200, f"API gibt Status {response.status_code} für {encoding}"
                    
                    # Überprüfe dass keine Mojibake-Marker vorhanden sind
                    response_text = response.text
                    BAD_MARKERS = ["Ã", "┬", "├", ""]
                    
                    found_markers = []
                    for marker in BAD_MARKERS:
                        if marker in response_text:
                            found_markers.append(marker)
                    
                    assert not found_markers, f"Mojibake-Marker gefunden für {encoding}: {found_markers}"
                    
                except requests.exceptions.RequestException as e:
                    pytest.skip(f"Server nicht erreichbar: {e}")
                    
            finally:
                # Cleanup
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
    
    def test_unicode_handling(self):
        """Teste dass Unicode-Zeichen korrekt behandelt werden"""
        # Unicode-Test-Zeichen
        unicode_tests = [
            "äöüß",  # Deutsche Umlaute
            "ÄÖÜ",    # Deutsche Umlaute groß
            "éèêë",   # Französische Akzente
            "ñ",      # Spanisches ñ
            "€",      # Euro-Symbol
            "°",      # Grad-Symbol
        ]
        
        for unicode_text in unicode_tests:
            # Erstelle temporäre CSV mit Unicode
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write("Kunde;Adresse\n")
                tmp_file.write(f"Test;{unicode_text} 1, Teststadt\n")
                tmp_file_path = tmp_file.name
            
            try:
                # Server-URL
                base_url = "http://127.0.0.1:8111"
                
                try:
                    # Teste parse-csv-tourplan Endpoint
                    with open(tmp_file_path, 'rb') as f:
                        files = {'file': f}
                        response = requests.post(f"{base_url}/api/parse-csv-tourplan", files=files, timeout=30)
                    
                    assert response.status_code == 200, f"API gibt Status {response.status_code} für Unicode: {unicode_text}"
                    
                    # Überprüfe dass Unicode korrekt erhalten bleibt
                    response_text = response.text
                    assert unicode_text in response_text, f"Unicode-Text {unicode_text} nicht in Response gefunden"
                    
                    # Überprüfe dass keine Mojibake-Marker vorhanden sind
                    BAD_MARKERS = ["Ã", "┬", "├", ""]
                    found_markers = []
                    for marker in BAD_MARKERS:
                        if marker in response_text:
                            found_markers.append(marker)
                    
                    assert not found_markers, f"Mojibake-Marker gefunden für Unicode {unicode_text}: {found_markers}"
                    
                except requests.exceptions.RequestException as e:
                    pytest.skip(f"Server nicht erreichbar: {e}")
                    
            finally:
                # Cleanup
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
