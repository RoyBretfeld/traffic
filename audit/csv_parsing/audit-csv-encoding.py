#!/usr/bin/env python3
"""
CSV-Encoding-Audit CLI
Extrahiert 10 Adressen aus CSV-Dateien und prüft auf Mojibake
"""

import sys
import random
from pathlib import Path
import pandas as pd

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importiere direkt aus der kopierten Datei
sys.path.insert(0, str(Path(__file__).parent))

# Kopiere die Funktionen direkt hierher für Standalone-Betrieb
def trace_text(label: str, s: str) -> None:
    """Zeigt HEX-Dump eines Strings für Encoding-Diagnose"""
    if not isinstance(s, str):
        print(f"[TRACE {label}] Erwarteter String, aber erhielt {type(s)}")
        return
    try:
        print(f"[HEX {label}]", s.encode('utf-8').hex(' ').upper())
    except Exception as e:
        print(f"[TRACE {label}] Fehler beim HEX-Tracing: {e}")

def assert_no_mojibake(s: str) -> None:
    """Prüft einen String auf verbotene Mojibake-Marker."""
    if not isinstance(s, str):
        print(f"[ASSERT] Erwarteter String, aber erhielt {type(s)}")
        return

    bad_markers = ['\uFFFD', 'Ã', '┬', '├', '┤']
    found_bad_markers = [m for m in bad_markers if m in s]
    if found_bad_markers:
        error_message = f"ENCODING-BUG erkannt in: {s!r}\nGefundene Mojibake-Marker: {', '.join(f"'{m}' (U+{ord(m):04X})" for m in found_bad_markers)}"
        print(f"[ERROR] {error_message}")
        raise ValueError(error_message)

def preview_geocode_url(addr: str) -> None:
    """Zeigt die finale URL für eine Nominatim-Geocoding-Anfrage."""
    try:
        import urllib.parse
        encoded_addr = urllib.parse.quote(addr, safe='')
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_addr}&format=jsonv2"
        print(f"[URL] {url}")
        assert_no_mojibake(url)
        
        # Prüfe auf korrekte UTF-8-Kodierung deutscher Sonderzeichen
        if 'ö' in addr and '%C3%B6' not in url:
            print(f"[URL-ENCODING] 'ö' in Adresse, aber nicht als '%C3%B6' in URL kodiert")
        if 'ß' in addr and '%C3%9F' not in url:
            print(f"[URL-ENCODING] 'ß' in Adresse, aber nicht als '%C3%9F' in URL kodiert")
        if 'ä' in addr and '%C3%A4' not in url:
            print(f"[URL-ENCODING] 'ä' in Adresse, aber nicht als '%C3%A4' in URL kodiert")
            
    except Exception as e:
        print(f"[PREVIEW_GEOCODE_URL] Fehler beim Generieren der URL-Vorschau für '{addr}': {e}")

def audit_csv_encoding():
    """Auditiert CSV-Encoding mit 10 zufälligen Adressen"""
    
    print("CSV-Encoding-Audit gestartet...")
    print("=" * 60)
    
    # Finde CSV-Dateien
    tourplaene_dir = Path("tourplaene")
    if not tourplaene_dir.exists():
        print("ERROR: tourplaene Verzeichnis nicht gefunden")
        return 1
    
    csv_files = list(tourplaene_dir.glob("*.csv"))
    if not csv_files:
        print("ERROR: Keine CSV-Dateien gefunden")
        return 1
    
    print(f"Gefundene CSV-Dateien: {len(csv_files)}")
    
    # Sammle Adressen aus allen Dateien
    all_addresses = []
    
    for csv_file in csv_files[:3]:  # Nur erste 3 Dateien
        try:
            print(f"\nVerarbeite: {csv_file.name}")
            
            # CSV lesen mit verschiedenen Encodings
            for encoding in ["cp850", "utf-8"]:
                try:
                    df = pd.read_csv(csv_file, sep=';', header=None, dtype=str, encoding=encoding)
                    print(f"   OK {encoding}: {len(df)} Zeilen")
                    
                    # Extrahiere Adressen (Spalten 2-4: Straße, PLZ, Ort)
                    for idx, row in df.iterrows():
                        if len(row) >= 5 and pd.notna(row.iloc[2]) and pd.notna(row.iloc[4]):
                            street = str(row.iloc[2]).strip()
                            postal_code = str(row.iloc[3]).strip()
                            city = str(row.iloc[4]).strip()
                            
                            if street and city and street != 'nan' and city != 'nan':
                                address = f"{street}, {postal_code} {city}"
                                all_addresses.append({
                                    'address': address,
                                    'encoding': encoding,
                                    'file': csv_file.name,
                                    'row': idx
                                })
                    
                    break  # Erste erfolgreiche Encoding verwenden
                    
                except UnicodeDecodeError:
                    print(f"   ERROR {encoding}: Decode-Fehler")
                    continue
                    
        except Exception as e:
            print(f"   ERROR bei {csv_file.name}: {e}")
            continue
    
    if not all_addresses:
        print("ERROR: Keine Adressen gefunden")
        return 1
    
    print(f"\nGesammelte Adressen: {len(all_addresses)}")
    
    # Wähle 10 zufällige Adressen
    sample_addresses = random.sample(all_addresses, min(10, len(all_addresses)))
    
    print(f"\nTeste {len(sample_addresses)} zufällige Adressen:")
    print("=" * 60)
    
    mojibake_found = False
    
    for i, addr_data in enumerate(sample_addresses, 1):
        address = addr_data['address']
        encoding = addr_data['encoding']
        file_name = addr_data['file']
        
        print(f"\n{i}. Adresse ({encoding}): {address}")
        print(f"   Datei: {file_name}")
        
        try:
            # 1. Trace Text
            trace_text(f"ADDR_{i}", address)
            
            # 2. Mojibake-Prüfung
            assert_no_mojibake(address)
            print("   OK: Kein Mojibake erkannt")
            
            # 3. Geocoding-URL
            preview_geocode_url(address)
            
        except ValueError as e:
            print(f"   ERROR: MOJIBAKE ERKANNT: {e}")
            mojibake_found = True
    
    print("\n" + "=" * 60)
    
    if mojibake_found:
        print("AUDIT FEHLGESCHLAGEN: Mojibake gefunden!")
        return 1
    else:
        print("AUDIT ERFOLGREICH: Kein Mojibake gefunden!")
        return 0

if __name__ == "__main__":
    try:
        exit_code = audit_csv_encoding()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Audit fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
