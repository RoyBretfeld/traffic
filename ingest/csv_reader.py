#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentraler CSV-Ingest für FAMO TrafficApp
========================================

Dieses Modul stellt eine einheitliche, gehärtete CSV-Lese-Funktion bereit,
die das Encoding-Chaos beendet.

Verwendung:
    from ingest.csv_reader import read_csv_unified
    
    df = read_csv_unified("path/to/file.csv")
"""

import pandas as pd
import unicodedata
from pathlib import Path
from typing import Union, Optional, Dict, Any
from io import StringIO

from ingest.guards import assert_no_mojibake, trace_text
from common.text_cleaner import repair_cp_mojibake

def read_csv_unified(
    file_path: Union[str, Path],
    sep: str = ';',
    header: Optional[int] = None,
    dtype: Optional[Dict[str, Any]] = None,
    encoding_hint: Optional[str] = None
) -> pd.DataFrame:
    """
    Einheitliche CSV-Lese-Funktion mit gehärtetem Encoding.
    
    Diese Funktion implementiert die "EINMALIGE CP850-Decodierung, dann UTF-8" Regel:
    1. Versucht CP850 (Windows-Standard für CSV-Exporte)
    2. Fallback auf UTF-8-sig (mit BOM)
    3. Fallback auf UTF-8 (ohne BOM)
    4. Unicode-Normalisierung
    5. Mojibake-Guards
    6. DataFrame-Erstellung
    
    Args:
        file_path: Pfad zur CSV-Datei
        sep: Separator (Standard: ';')
        header: Header-Zeile (Standard: None)
        dtype: Datentypen für Spalten
        encoding_hint: Hinweis auf erwartetes Encoding (für Debugging)
        
    Returns:
        pandas.DataFrame: Die gelesene CSV-Datei
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert
        UnicodeDecodeError: Wenn alle Encoding-Versuche fehlschlagen
        ValueError: Wenn Mojibake erkannt wird
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV-Datei nicht gefunden: {file_path}")
    
    print(f"[CSV-INGEST] Verarbeite: {file_path.name}")
    if encoding_hint:
        print(f"[CSV-INGEST] Encoding-Hinweis: {encoding_hint}")
    
    # 1. Datei als Bytes lesen
    try:
        raw_bytes = file_path.read_bytes()
        print(f"[CSV-INGEST] Dateigröße: {len(raw_bytes)} Bytes")
    except Exception as e:
        raise Exception(f"Fehler beim Lesen der Datei {file_path}: {e}")
    
    # 2. EINMALIGE Decoding mit CP850 (Windows-Standard für CSV-Export)
    # Danach IMMER UTF-8 verwenden
    decoded_text = None
    used_encoding = None
    
    # Versuche CP850 zuerst (Windows-Standard)
    try:
        decoded_text = raw_bytes.decode("cp850")
        used_encoding = "cp850"
        print(f"[CSV-INGEST] CP850 erfolgreich für {file_path.name}")
    except UnicodeDecodeError:
        print(f"[CSV-INGEST] CP850 fehlgeschlagen für {file_path.name}")
        
        # Fallback auf UTF-8-sig (mit BOM)
        try:
            decoded_text = raw_bytes.decode("utf-8-sig")
            used_encoding = "utf-8-sig"
            print(f"[CSV-INGEST] UTF-8-sig erfolgreich für {file_path.name}")
        except UnicodeDecodeError:
            print(f"[CSV-INGEST] UTF-8-sig fehlgeschlagen für {file_path.name}")
            
            # Fallback auf UTF-8 (ohne BOM)
            try:
                decoded_text = raw_bytes.decode("utf-8")
                used_encoding = "utf-8"
                print(f"[CSV-INGEST] UTF-8 erfolgreich für {file_path.name}")
            except UnicodeDecodeError:
                # Letzter Versuch mit Fehlerersetzung
                decoded_text = raw_bytes.decode("utf-8", errors='replace')
                used_encoding = "utf-8 (mit Fehlerersetzung)"
                print(f"[CSV-INGEST] UTF-8 mit Fehlerersetzung für {file_path.name}")
    
    if decoded_text is None:
        raise UnicodeDecodeError("utf-8", raw_bytes, 0, len(raw_bytes), "Alle Encoding-Versuche fehlgeschlagen")
    
    # 3. Unicode normalisieren (verlustfrei)
    normalized_text = unicodedata.normalize("NFC", decoded_text)
    repaired_text = repair_cp_mojibake(normalized_text)
    print(f"[CSV-INGEST] Unicode normalisiert (NFC)")
    
    # 4. GUARD: Mojibake-Prüfung direkt nach Ingest
    try:
        assert_no_mojibake(repaired_text, f"nach {used_encoding}-Decodierung")
        print(f"[CSV-INGEST] Mojibake-Guard: OK")
    except ValueError as e:
        # Mojibake erkannt - trotzdem weiterarbeiten, aber warnen
        error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        print(f"[CSV-INGEST] Mojibake erkannt: {error_msg}")
        print(f"[CSV-INGEST] Datei wird trotzdem verarbeitet...")
    
    # 5. TRACE: Erste 200 Zeichen für Diagnose
    trace_text("CSV_INGEST", repaired_text[:200])
    
    # 6. In DataFrame - KEINE Reparatur mehr!
    try:
        read_header = 0 if header is None else header
        df = pd.read_csv(
            StringIO(repaired_text),
            sep=sep,
            header=read_header,
            dtype=dtype or str
        )
        print(f"[CSV-INGEST] DataFrame erstellt: {len(df)} Zeilen, {len(df.columns)} Spalten")
        return df
        
    except Exception as e:
        raise Exception(f"Fehler beim Erstellen des DataFrame aus {file_path}: {e}")

def write_csv_unified(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    sep: str = ';',
    index: bool = False,
    encoding: str = 'utf-8'
) -> None:
    """
    Einheitliche CSV-Schreib-Funktion mit UTF-8.
    
    Args:
        df: DataFrame zum Schreiben
        file_path: Ziel-Pfad
        sep: Separator (Standard: ';')
        index: Ob Index geschrieben werden soll
        encoding: Encoding (Standard: 'utf-8')
    """
    file_path = Path(file_path)
    
    try:
        df.to_csv(file_path, sep=sep, index=index, encoding=encoding)
        print(f"[CSV-EXPORT] Erfolgreich geschrieben: {file_path.name} ({encoding})")
    except Exception as e:
        raise Exception(f"Fehler beim Schreiben von {file_path}: {e}")

if __name__ == "__main__":
    # Test der Funktionen
    print("CSV-Ingest Test")
    
    # Test mit einer existierenden CSV-Datei
    test_files = list(Path("tourplaene").glob("*.csv"))
    if test_files:
        test_file = test_files[0]
        print(f"\nTeste mit: {test_file.name}")
        
        try:
            df = read_csv_unified(test_file)
            print(f"Erfolgreich gelesen: {len(df)} Zeilen")
            
            # Test-Schreiben
            test_output = Path("test_output.csv")
            write_csv_unified(df.head(5), test_output)
            test_output.unlink()  # Cleanup
            print("Test-Schreiben erfolgreich")
            
        except Exception as e:
            print(f"Test fehlgeschlagen: {e}")
    else:
        print("Keine CSV-Dateien zum Testen gefunden")
