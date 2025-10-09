"""
Encoding-Fix Tests für Mojibake-Prävention
Senior-Engineer Tests für doppelte Zeichensatz-Korruption
"""

import pytest
import sys
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.encoding_guards import (
    trace_text, 
    assert_no_mojibake, 
    preview_geocode_url,
    smoke_test_encoding
)


class TestEncodingGuards:
    """Tests für Encoding-Guards und Mojibake-Prävention"""
    
    def test_trace_text_basic(self):
        """Testet trace_text Funktion"""
        test_string = "Löbtauer Straße"
        # Sollte keine Exception werfen
        trace_text("TEST", test_string)
    
    def test_assert_no_mojibake_clean_text(self):
        """Testet assert_no_mojibake mit sauberem Text"""
        clean_texts = [
            "Löbtauer Straße 1, 01809 Heidenau",
            "Müller & Söhne GmbH",
            "Café am Markt",
            "Bäckerei Schröder"
        ]
        
        for text in clean_texts:
            # Sollte keine Exception werfen
            assert_no_mojibake(text)
    
    def test_assert_no_mojibake_detects_mojibake(self):
        """Testet assert_no_mojibake erkennt Mojibake"""
        mojibake_texts = [
            "Löbtauer Stra┬ße",  # Box-drawing character
            "Müller & S├öhne",   # Box-drawing character
            "Café am Markt",     # Replacement character
            "Bäckerei Schröder"  # UTF-8 als CP1252 interpretiert
        ]
        
        for text in mojibake_texts:
            with pytest.raises(ValueError, match="ENCODING-BUG"):
                assert_no_mojibake(text)
    
    def test_preview_geocode_url_clean(self):
        """Testet preview_geocode_url mit sauberem Text"""
        clean_address = "Löbtauer Straße 1, 01809 Heidenau"
        # Sollte keine Exception werfen
        preview_geocode_url(clean_address)
    
    def test_preview_geocode_url_detects_mojibake(self):
        """Testet preview_geocode_url erkennt Mojibake in URL"""
        mojibake_address = "Löbtauer Stra┬ße 1, 01809 Heidenau"
        
        with pytest.raises(ValueError, match="MOJIBAKE in URL"):
            preview_geocode_url(mojibake_address)
    
    def test_utf8_roundtrip(self):
        """Testet UTF-8 Roundtrip"""
        test_string = "Löbtauer Straße 1, 01809 Heidenau"
        
        # Encode zu UTF-8 Bytes
        utf8_bytes = test_string.encode('utf-8')
        
        # Decode zurück zu String
        decoded = utf8_bytes.decode('utf-8')
        
        # Sollte identisch sein
        assert decoded == test_string
    
    def test_expected_hex_sequences(self):
        """Testet erwartete UTF-8 HEX-Sequenzen"""
        test_string = "Löbtauer Straße"
        hex_dump = test_string.encode('utf-8').hex(' ').upper()
        
        # Erwartete UTF-8-Sequenzen
        assert "C3 B6" in hex_dump  # ö
        assert "C3 9F" in hex_dump  # ß
        
        # Sollte KEINE Mojibake-Sequenzen enthalten
        assert "E2 94 AC" not in hex_dump  # ┬
        assert "E2 94 9C" not in hex_dump  # ├
        assert "E2 94 A4" not in hex_dump  # ┤


class TestEncodingRoundtrip:
    """Tests für Encoding-Roundtrip-Szenarien"""
    
    def test_encoding_roundtrip_complete(self):
        """Testet kompletten Encoding-Roundtrip"""
        # Test-String mit deutschen Umlauten
        original = "Löbtauer Straße 1, 01809 Heidenau"
        
        # 1. UTF-8 Encode
        utf8_bytes = original.encode('utf-8')
        
        # 2. UTF-8 Decode
        decoded = utf8_bytes.decode('utf-8')
        
        # 3. Sollte identisch sein
        assert decoded == original
        
        # 4. Kein Mojibake
        assert_no_mojibake(decoded)
    
    def test_geocoding_url_encoding(self):
        """Testet Geocoding-URL-Encoding"""
        address = "Löbtauer Straße 1, 01809 Heidenau"
        
        # Sollte korrekte UTF-8-URL-Encodierung erzeugen
        preview_geocode_url(address)
        
        # Manuell prüfen
        import urllib.parse
        encoded = urllib.parse.quote(address, safe='')
        
        # Sollte korrekte UTF-8-Sequenzen enthalten
        assert "%C3%B6" in encoded  # ö
        assert "%C3%9F" in encoded  # ß
        
        # Sollte KEINE Mojibake-Sequenzen enthalten
        assert "%E2%94%AC" not in encoded  # ┬
        assert "%E2%94%9C" not in encoded  # ├


class TestSmokeTest:
    """Tests für Smoke-Test-Funktionen"""
    
    def test_smoke_test_encoding(self):
        """Testet smoke_test_encoding Funktion"""
        # Sollte erfolgreich durchlaufen
        smoke_test_encoding()


class TestCSVEncoding:
    """Tests für CSV-Encoding-Szenarien"""
    
    def test_csv_encoding_scenarios(self):
        """Testet verschiedene CSV-Encoding-Szenarien"""
        # Simuliere verschiedene Encoding-Probleme
        
        # 1. Korrekte UTF-8-Datei
        utf8_content = "Name;Adresse\nMüller;Löbtauer Straße 1"
        utf8_bytes = utf8_content.encode('utf-8')
        
        # Sollte korrekt decodiert werden
        decoded = utf8_bytes.decode('utf-8')
        assert_no_mojibake(decoded)
        
        # 2. CP850-Datei (Windows-Standard)
        cp850_content = "Name;Adresse\nMüller;Löbtauer Straße 1"
        cp850_bytes = cp850_content.encode('cp850')
        
        # Sollte korrekt decodiert werden
        decoded = cp850_bytes.decode('cp850')
        assert_no_mojibake(decoded)
    
    def test_mojibake_detection_in_csv(self):
        """Testet Mojibake-Erkennung in CSV-Daten"""
        # Simuliere Mojibake in CSV
        mojibake_content = "Name;Adresse\nM├╝ller;Löbtauer Stra┬ße 1"
        
        # Sollte Mojibake erkennen
        with pytest.raises(ValueError, match="ENCODING-BUG"):
            assert_no_mojibake(mojibake_content)


if __name__ == "__main__":
    # Führe Tests aus
    pytest.main([__file__, "-v"])
