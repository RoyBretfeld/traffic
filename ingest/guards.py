#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Encoding-Guards für CSV-Ingest
=======================================

Dieses Modul stellt zentrale Funktionen für die Erkennung und Behandlung
von Encoding-Problemen (Mojibake) bereit.

Verwendung:
    from ingest.guards import assert_no_mojibake, trace_text, BAD_MARKERS
    
    # Nach CSV-Ingest
    assert_no_mojibake(text)
    trace_text("CSV_INGEST", text[:200])
"""

import sys
import logging
from typing import List, Optional

# Mojibake-Marker die auf Encoding-Probleme hinweisen
BAD_MARKERS: List[str] = [
    '\uFFFD',  # Unicode Replacement Character
    'Ã',       # UTF-8-als-Latin-1 Marker
    'Â',       # UTF-8-als-Latin-1 Marker
    '┬',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '├',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┤',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┴',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┼',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┐',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '└',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┘',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┌',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '─',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '│',       # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '▒',       # Block-Zeichen (CP850-Fehlinterpretation)
    '▓',       # Block-Zeichen (CP850-Fehlinterpretation)
    '¶',       # Paragraph-Zeichen (oft bei Encoding-Problemen)
]

def assert_no_mojibake(s: str, context: str = "") -> None:
    """
    Prüft einen String auf Mojibake-Marker und wirft einen Fehler bei Problemen.
    
    Args:
        s: Der zu prüfende String
        context: Zusätzlicher Kontext für die Fehlermeldung
        
    Raises:
        ValueError: Wenn Mojibake-Marker gefunden werden
    """
    if not isinstance(s, str):
        raise TypeError(f"Erwarteter String, aber erhielt {type(s)}")
    
    found_markers = [m for m in BAD_MARKERS if m in s]
    if found_markers:
        error_msg = f"ENCODING-BUG erkannt{': ' + context if context else ''}\n"
        error_msg += f"String: {s!r}\n"
        error_msg += f"Gefundene Mojibake-Marker: {', '.join(f'{m!r} (U+{ord(m):04X})' for m in found_markers)}"
        
        # Logging mit Unicode-sicherer Ausgabe
        try:
            logger = logging.getLogger(__name__)
            logger.error(error_msg)
        except UnicodeEncodeError:
            # Fallback für Konsolen ohne UTF-8-Unterstützung
            safe_msg = error_msg.encode('ascii', errors='replace').decode('ascii')
            print(f"[ENCODING-ERROR] {safe_msg}")
        
        raise ValueError(error_msg)

def trace_text(label: str, s: str, max_length: int = 200) -> None:
    """
    Zeigt einen HEX-Dump eines Strings für Encoding-Diagnose.
    
    Args:
        label: Label für die Ausgabe
        s: Der zu analysierende String
        max_length: Maximale Länge des Strings für die Ausgabe
    """
    if not isinstance(s, str):
        print(f"[TRACE {label}] Erwarteter String, aber erhielt {type(s)}")
        return
    
    # String kürzen für bessere Lesbarkeit
    display_text = s[:max_length] if len(s) > max_length else s
    if len(s) > max_length:
        display_text += "..."
    
    try:
        hex_dump = display_text.encode('utf-8').hex(' ').upper()
        print(f"[HEX {label}] {hex_dump}")
        
        # Logging mit Unicode-sicherer Ausgabe
        logger = logging.getLogger(__name__)
        logger.info(f"[HEX {label}] {hex_dump}")
        
    except Exception as e:
        print(f"[TRACE {label}] Fehler beim HEX-Tracing: {e}")

def preview_geocode_url(addr: str) -> None:
    """
    Zeigt die finale URL für eine Nominatim-Geocoding-Anfrage.
    
    Args:
        addr: Die Adresse für die Geocoding-URL
    """
    try:
        import urllib.parse
        
        encoded_addr = urllib.parse.quote(addr, safe='')
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_addr}&format=jsonv2"
        
        print(f"[URL] {url}")
        
        # Mojibake-Prüfung der URL
        assert_no_mojibake(url, "in Geocoding-URL")
        
        # Prüfe auf korrekte UTF-8-Kodierung deutscher Sonderzeichen
        if 'ö' in addr and '%C3%B6' not in url:
            print(f"[URL-ENCODING] 'ö' in Adresse, aber nicht als '%C3%B6' in URL kodiert")
        if 'ß' in addr and '%C3%9F' not in url:
            print(f"[URL-ENCODING] 'ß' in Adresse, aber nicht als '%C3%9F' in URL kodiert")
        if 'ä' in addr and '%C3%A4' not in url:
            print(f"[URL-ENCODING] 'ä' in Adresse, aber nicht als '%C3%A4' in URL kodiert")
            
    except Exception as e:
        print(f"[PREVIEW_GEOCODE_URL] Fehler beim Generieren der URL-Vorschau für '{addr}': {e}")

def setup_utf8_logging() -> None:
    """
    Konfiguriert den Root-Logger für UTF-8-Ausgabe.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Entferne alle bestehenden Handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Neuer UTF-8 Handler
    handler = logging.StreamHandler(stream=sys.stdout)
    # setEncoding ist nicht verfügbar in Python 3.13, verwende TextIOWrapper
    # Die Konsole muss selbst UTF-8 unterstützen (z.B. chcp 65001 in cmd/powershell)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    print("[LOGGING] UTF-8 Logging konfiguriert.")

def smoke_test_encoding() -> None:
    """
    Führt einen Smoke-Test für die Encoding-Konfiguration durch.
    """
    test_string = "Löbtauer Straße 1, 01809 Heidenau"
    print(f"[SMOKE TEST] Test-String: {test_string!r}")
    trace_text("SMOKE", test_string)
    assert_no_mojibake(test_string)
    preview_geocode_url(test_string)
    print("[SMOKE TEST] Encoding-Test erfolgreich abgeschlossen.")

if __name__ == "__main__":
    # Test der Funktionen
    setup_utf8_logging()
    smoke_test_encoding()
    
    # Test mit Mojibake
    try:
        mojibake_string = "Stra├ße 1"
        assert_no_mojibake(mojibake_string, "Test-Mojibake")
    except ValueError as e:
        print(f"[TEST] Mojibake korrekt erkannt: {e}")
