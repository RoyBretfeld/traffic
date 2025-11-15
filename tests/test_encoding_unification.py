#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests für zentrale Encoding-Module
=================================

Diese Tests validieren die korrekte Funktionalität der zentralen
Encoding-Module und Guards.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from io import StringIO

from ingest.guards import assert_no_mojibake, trace_text, preview_geocode_url, BAD_MARKERS
from ingest.csv_reader import read_csv_unified, write_csv_unified
from ingest.http_responses import create_utf8_json_response, create_utf8_html_response

class TestEncodingGuards:
    """Tests für Encoding-Guards"""
    
    def test_assert_no_mojibake_clean_text(self):
        """Test mit sauberem Text ohne Mojibake"""
        clean_text = "Löbtauer Straße 1, 01809 Heidenau"
        # Sollte keine Exception werfen
        assert_no_mojibake(clean_text)
    
    def test_assert_no_mojibake_detects_problems(self):
        """Test mit Mojibake-Text"""
        mojibake_text = "Stra├ße 1"  # Enthält ├ (Box-Drawing-Zeichen)
        
        with pytest.raises(ValueError, match="ENCODING-BUG"):
            assert_no_mojibake(mojibake_text)
    
    def test_assert_no_mojibake_all_bad_markers(self):
        """Test mit allen bekannten Mojibake-Markern"""
        for marker in BAD_MARKERS:
            test_text = f"Test{marker}Text"
            with pytest.raises(ValueError, match="ENCODING-BUG"):
                assert_no_mojibake(test_text)
    
    def test_trace_text_output(self, capsys):
        """Test der trace_text Ausgabe"""
        test_text = "Löbtauer Straße"
        trace_text("TEST", test_text)
        
        captured = capsys.readouterr()
        assert "[HEX TEST]" in captured.out
        assert "C3 B6" in captured.out  # ö in UTF-8
        assert "C3 9F" in captured.out  # ß in UTF-8
    
    def test_preview_geocode_url(self, capsys):
        """Test der Geocoding-URL-Generierung"""
        test_address = "Löbtauer Straße 1, 01809 Heidenau"
        preview_geocode_url(test_address)
        
        captured = capsys.readouterr()
        assert "[URL]" in captured.out
        assert "%C3%B6" in captured.out  # ö in URL
        assert "%C3%9F" in captured.out    # ß in URL
        assert "nominatim.openstreetmap.org" in captured.out

class TestCSVReader:
    """Tests für CSV-Reader"""
    
    def test_read_csv_unified_utf8(self):
        """Test mit UTF-8 CSV"""
        test_data = "Name;Straße;PLZ;Ort\nMax Mustermann;Löbtauer Straße;01809;Heidenau"
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            df = read_csv_unified(temp_path)
            assert len(df) == 1
            assert df.iloc[0, 1] == "Löbtauer Straße"  # Straße-Spalte
        finally:
            Path(temp_path).unlink()
    
    def test_read_csv_unified_cp850(self):
        """Test mit CP850 CSV (simuliert)"""
        # Erstelle CP850-kodierte Testdaten
        test_data = "Name;Straße;PLZ;Ort\nMax Mustermann;Löbtauer Straße;01809;Heidenau"
        cp850_bytes = test_data.encode('cp850')
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(cp850_bytes)
            temp_path = f.name
        
        try:
            df = read_csv_unified(temp_path)
            assert len(df) == 1
            assert "Löbtauer Straße" in str(df.iloc[0, 1])  # Straße-Spalte
        finally:
            Path(temp_path).unlink()
    
    def test_write_csv_unified(self):
        """Test des CSV-Schreibens"""
        test_df = pd.DataFrame({
            'Name': ['Max Mustermann'],
            'Straße': ['Löbtauer Straße'],
            'PLZ': ['01809'],
            'Ort': ['Heidenau']
        })
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            write_csv_unified(test_df, temp_path)
            
            # Prüfe, dass Datei erstellt wurde
            assert Path(temp_path).exists()
            
            # Prüfe Inhalt
            content = Path(temp_path).read_text(encoding='utf-8')
            assert "Löbtauer Straße" in content
            assert "Max Mustermann" in content
            
        finally:
            Path(temp_path).unlink()

class TestHTTPResponses:
    """Tests für HTTP-Responses"""
    
    def test_create_utf8_json_response(self):
        """Test der UTF-8 JSON Response"""
        test_content = {"test": "Löbtauer Straße", "umlaut": "äöüß"}
        
        response = create_utf8_json_response(test_content)
        
        assert response.status_code == 200
        assert "charset=utf-8" in response.headers["content-type"]
        assert response.headers["content-type"] == "application/json; charset=utf-8"
    
    def test_create_utf8_html_response(self):
        """Test der UTF-8 HTML Response"""
        test_content = "<html><body>Löbtauer Straße</body></html>"
        
        response = create_utf8_html_response(test_content)
        
        assert response.status_code == 200
        assert "charset=utf-8" in response.headers["content-type"]
        assert response.headers["content-type"] == "text/html; charset=utf-8"

class TestEncodingRoundtrip:
    """Tests für Encoding-Roundtrip"""
    
    def test_encoding_roundtrip(self):
        """Test des Encoding-Roundtrips"""
        test_string = "Löbtauer Straße 1, 01809 Heidenau"
        
        # UTF-8 Roundtrip
        encoded = test_string.encode("utf-8")
        decoded = encoded.decode("utf-8")
        
        assert decoded == test_string
        
        # Prüfe spezifische Bytes
        assert b'\xc3\xb6' in encoded  # ö in UTF-8
        assert b'\xc3\x9f' in encoded  # ß in UTF-8
    
    def test_no_mojibake_anywhere(self):
        """Test des gesamten Flows ohne Mojibake"""
        test_address = "Löbtauer Straße 1, 01809 Heidenau"
        
        # Simuliere CSV-Ingest
        test_data = f"Name;Straße;PLZ;Ort\nMax Mustermann;{test_address.split(',')[0]};01809;Heidenau"
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            # CSV lesen
            df = read_csv_unified(temp_path)
            
            # Adresse extrahieren
            address = df.iloc[0, 1] + ", " + df.iloc[0, 2] + " " + df.iloc[0, 3]
            
            # Mojibake-Prüfung
            assert_no_mojibake(address)
            
            # Geocoding-URL generieren
            preview_geocode_url(address)
            
        finally:
            Path(temp_path).unlink()

if __name__ == "__main__":
    # Führe Tests aus
    pytest.main([__file__, "-v"])
