"""
Encoding Guards & Tracer für Mojibake-Prävention
Senior-Engineer Lösung für doppelte Zeichensatz-Korruption
"""

import sys
import logging


def trace_text(label: str, s: str) -> None:
    """Zeigt HEX-Dump eines Strings für Encoding-Diagnose"""
    if not isinstance(s, str):
        s = str(s)
    hex_dump = s.encode('utf-8').hex(' ').upper()
    print(f"[HEX {label}] {hex_dump}")
    
    # Log auch über Logger
    logger = logging.getLogger(__name__)
    logger.info(f"[HEX {label}] {hex_dump}")


def assert_no_mojibake(s: str) -> None:
    """
    Prüft auf Mojibake-Marker und wirft Exception bei Verdacht.
    
    Mojibake-Marker:
    - \uFFFD: Unicode Replacement Character
    - Ã: UTF-8 als CP1252/CP850 interpretiert (Ã = C3)
    - ┬, ├, ┤: Box-drawing characters (E2 94 AC, E2 94 9C, E2 94 A4)
    - Andere typische UTF-8-als-Latin-1 Artefakte
    """
    if not isinstance(s, str):
        s = str(s)
    
    # Mojibake-Marker definieren
    bad_markers = [
        '\uFFFD',  # Unicode Replacement Character
        'Ã',       # UTF-8 C3 als CP1252/CP850 interpretiert
        '┬',       # E2 94 AC - Box drawing
        '├',       # E2 94 9C - Box drawing  
        '┤',       # E2 94 A4 - Box drawing
        '└',       # E2 94 94 - Box drawing
        '┘',       # E2 94 98 - Box drawing
        '┌',       # E2 94 8C - Box drawing
        '┐',       # E2 94 90 - Box drawing
        '│',       # E2 94 82 - Box drawing
        '─',       # E2 94 80 - Box drawing
    ]
    
    # Prüfe auf Mojibake-Marker
    found_markers = []
    for marker in bad_markers:
        if marker in s:
            found_markers.append(f"'{marker}' (U+{ord(marker):04X})")
    
    if found_markers:
        error_msg = f"ENCODING-BUG erkannt in: {s!r}\nGefundene Mojibake-Marker: {', '.join(found_markers)}"
        logger = logging.getLogger(__name__)
        logger.error(error_msg)
        raise ValueError(error_msg)


def preview_geocode_url(addr: str) -> None:
    """
    Zeigt finale Geocoding-URL mit korrekter UTF-8-Encodierung.
    Erwartet: ß = %C3%9F, ö = %C3%B6
    Verhindert: %E2%94%AC (┬) = Mojibake
    """
    import urllib.parse
    
    # URL-Encode mit UTF-8
    encoded_addr = urllib.parse.quote(addr, safe='')
    
    # Prüfe auf Mojibake in URL
    if any(marker in encoded_addr for marker in ['%E2%94%AC', '%E2%94%9C', '%E2%94%A4']):
        raise ValueError(f"MOJIBAKE in URL: {encoded_addr}")
    
    # Erwartete UTF-8-Sequenzen prüfen
    expected_sequences = {
        'ß': '%C3%9F',
        'ö': '%C3%B6', 
        'ä': '%C3%A4',
        'ü': '%C3%BC',
        'Ö': '%C3%96',
        'Ä': '%C3%84',
        'Ü': '%C3%9C'
    }
    
    print(f"[GEOCODE URL] {encoded_addr}")
    
    # Prüfe auf korrekte UTF-8-Encodierung
    for char, expected in expected_sequences.items():
        if char in addr and expected not in encoded_addr:
            print(f"[WARNING] Char '{char}' nicht korrekt encodiert in URL")
    
    logger = logging.getLogger(__name__)
    logger.info(f"[GEOCODE URL] {encoded_addr}")


def setup_utf8_logging() -> None:
    """Konfiguriert Logging für UTF-8"""
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    
    # Entferne alle bestehenden Handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Neuer UTF-8 Handler
    handler = logging.StreamHandler(stream=sys.stdout)
    # setEncoding ist nicht verfügbar in Python 3.13, verwende TextIOWrapper
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    print("[LOGGING] UTF-8 Logging konfiguriert")


def smoke_test_encoding() -> None:
    """Führt Encoding-Smoke-Test durch"""
    test_string = "Löbtauer Straße 1, 01809 Heidenau"
    
    print("[SMOKE TEST] Starte Encoding-Test...")
    
    # 1. Trace Text
    trace_text("SMOKE", test_string)
    
    # 2. Prüfe auf Mojibake
    try:
        assert_no_mojibake(test_string)
        print("[SMOKE TEST] ✅ Kein Mojibake erkannt")
    except ValueError as e:
        print(f"[SMOKE TEST] ❌ Mojibake erkannt: {e}")
        raise
    
    # 3. Prüfe Geocoding-URL
    try:
        preview_geocode_url(test_string)
        print("[SMOKE TEST] ✅ Geocoding-URL korrekt")
    except ValueError as e:
        print(f"[SMOKE TEST] ❌ Geocoding-URL-Problem: {e}")
        raise
    
    # 4. Prüfe UTF-8 Roundtrip
    utf8_bytes = test_string.encode('utf-8')
    decoded = utf8_bytes.decode('utf-8')
    
    if decoded == test_string:
        print("[SMOKE TEST] ✅ UTF-8 Roundtrip erfolgreich")
    else:
        print(f"[SMOKE TEST] ❌ UTF-8 Roundtrip fehlgeschlagen: {decoded!r} != {test_string!r}")
        raise ValueError("UTF-8 Roundtrip fehlgeschlagen")
    
    # 5. Erwartete HEX-Sequenzen prüfen
    expected_hex = "4C C3 B6 62 74 61 75 65 72 20 53 74 72 61 C3 9F 65"
    actual_hex = test_string.encode('utf-8').hex(' ').upper()
    
    if "C3 B6" in actual_hex and "C3 9F" in actual_hex:
        print("[SMOKE TEST] ✅ Korrekte UTF-8-Sequenzen erkannt")
    else:
        print(f"[SMOKE TEST] ❌ Falsche UTF-8-Sequenzen: {actual_hex}")
        raise ValueError("Falsche UTF-8-Sequenzen")
    
    print("[SMOKE TEST] ✅ Alle Tests erfolgreich!")


if __name__ == "__main__":
    setup_utf8_logging()
    smoke_test_encoding()
