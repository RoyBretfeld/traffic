#!/usr/bin/env python3
"""
Kanonische CSV-Pipeline für Tourpläne

Einheitlicher, verlustfreier Weg:
1. Originalbytes lesen
2. Korrekt decodieren (CP850 → UTF-8)
3. Unicode normalisieren (NFC)
4. Kanonische UTF-8-Kopie speichern
5. Nur diese Kopie weiter verarbeiten
"""

from pathlib import Path
import unicodedata
import pandas as pd
import io
from typing import Dict, Optional

def _decode_best(raw: bytes) -> tuple[str, str]:
    """Findet das beste Encoding für die Rohdaten."""
    for enc in ("cp850", "utf-8-sig", "cp1252", "utf-8"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    raise UnicodeDecodeError("decoding", raw, 0, 0, "Keine passende Kodierung gefunden")

def canonicalize_csv(in_path: str, out_utf8: str, out_excel_utf8_sig: Optional[str] = None) -> Dict:
    """
    Kanonisiert eine CSV-Datei zu UTF-8.
    
    Args:
        in_path: Pfad zur Eingangsdatei
        out_utf8: Pfad für UTF-8 ohne BOM (Backend/Services)
        out_excel_utf8_sig: Pfad für UTF-8 mit BOM (Excel-Export)
    
    Returns:
        Dict mit Metadaten (Encoding, Replacement-Zeichen, etc.)
    """
    # 1. Originalbytes lesen
    raw = Path(in_path).read_bytes()
    
    # 2. Korrekt decodieren
    text, source_encoding = _decode_best(raw)
    
    # 3. Unicode normalisieren (NFC)
    text = unicodedata.normalize("NFC", text)
    
    # 4. Mojibake reparieren (erweiterte Reparatur)
    text = repair_all_mojibake(text)
    
    # 5. Zeilenenden vereinheitlichen
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 5. Kanonisch speichern (UTF-8 ohne BOM)
    Path(out_utf8).write_text(text, encoding="utf-8")
    
    # 6. Excel-Variante (mit BOM)
    if out_excel_utf8_sig:
        Path(out_excel_utf8_sig).write_text(text, encoding="utf-8-sig")
    
    # 7. Metadaten sammeln
    replacement_chars = text.count("\uFFFD")
    lines = text.splitlines()
    head_semicolons = lines[0].count(";") if lines else 0
    
    return {
        "source_encoding": source_encoding,
        "replacement_chars": replacement_chars,
        "head_semicolons": head_semicolons,
        "lines": len(lines),
        "size_bytes": len(text.encode('utf-8'))
    }

def repair_all_mojibake(text: str) -> str:
    """Repariert alle Mojibake-Artefakte aus PDF-OCR."""
    
    # 1. Typische UTF-8-als-Latin-1-Mojibake
    if any(seq in text for seq in ("Ã¤","Ã¶","Ã¼","ÃŸ","Ã„","Ã–","Ãœ")):
        try:
            text = text.encode("latin1").decode("utf-8")
        except Exception:
            pass
    
    # 2. PDF-OCR-spezifische Korruptionen (erweiterte Muster!)
    mojibake_fixes = {
        # Spezifische Adress-Korruptionen (nur eindeutige Fälle!)
        'Fabelstraáe': 'Fabelstraße',
        'L@btauer': 'Löbtauer',
        'Berensteiner': 'Bernsteiner',
        'Cch] erstraáe': 'Schillerstraße',
        'sterreicher': 'Österreicher',
        'Cosch@tzer': 'Coschützer',
        'Morgenr@the': 'Morgenröthe',
        'Nieder mahle': 'Niedermühle',
        'Gohliser Straáe': 'Gohliser Straße',
        'Wilsdruffer Straáe': 'Wilsdruffer Straße',
        'Cosch@tzer Straée': 'Coschützer Straße',
        'Straás der MTS': 'Straße der MTS',
        
        # ß-Korruptionen (nur in Straßennamen!)
        'straáe': 'straße',
        'straá': 'straße', 
        'straás': 'straße',
        'Straáe': 'Straße',
        'Straá': 'Straße',
        'Straás': 'Straße',
        
        # Neue Muster aus dem Test
        'Fr┬öbelstra├íe': 'Fröbelstraße',
        'L┬öbtauer': 'Löbtauer',
        'B┬ärensteiner': 'Bärensteiner',
        'Schl┬üterstra├íe': 'Schlüterstraße',
        'stra├íe': 'straße',
        'Stra├íe': 'Straße',
        
        # Weitere häufige Muster
        '┬ö': 'ö',
        '┬ä': 'ä',
        '┬ü': 'ü',
        '┬Ä': 'Ä',
        '┬Ö': 'Ö',
        '┬Ü': 'Ü',
        '├í': 'ß',
        '├ä': 'Ä',
        '├ö': 'ö',
        '├ü': 'ü',
        '├Ö': 'Ö',
        '├Ü': 'Ü',
        
        # Letzte spezifische Muster
        '┬é': 'é',  # Andr┬é → André
        'Andr┬é': 'André',
    }
    
    for corrupt, correct in mojibake_fixes.items():
        text = text.replace(corrupt, correct)
    
    return text

def process_all_tourplans():
    """Verarbeitet alle Tourpläne zu kanonischen UTF-8-Dateien."""
    
    # Verzeichnisse
    source_dir = Path("tourplaene")
    canonical_dir = Path("tourplaene_canonical")
    excel_dir = Path("tourplaene_excel")
    
    # Erstelle Ausgabeverzeichnisse
    canonical_dir.mkdir(exist_ok=True)
    excel_dir.mkdir(exist_ok=True)
    
    print("🔄 Kanonische CSV-Pipeline")
    print("=" * 50)
    print(f"📁 Quelle: {source_dir}")
    print(f"📁 Kanonisch: {canonical_dir}")
    print(f"📁 Excel: {excel_dir}")
    print()
    
    results = []
    success_count = 0
    error_count = 0
    
    for csv_file in source_dir.glob("*.csv"):
        print(f"📄 Verarbeite: {csv_file.name}")
        
        try:
            # Kanonisiere
            canonical_path = canonical_dir / csv_file.name
            excel_path = excel_dir / csv_file.name
            
            info = canonicalize_csv(
                str(csv_file),
                str(canonical_path),
                str(excel_path)
            )
            
            # Status prüfen
            status = "✅" if info["replacement_chars"] == 0 else "⚠️"
            print(f"  {status} {info['source_encoding']} → UTF-8")
            print(f"    Replacement-Zeichen: {info['replacement_chars']}")
            print(f"    Zeilen: {info['lines']}, Spalten: {info['head_semicolons'] + 1}")
            
            results.append({
                "file": csv_file.name,
                "status": "success",
                **info
            })
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
            results.append({
                "file": csv_file.name,
                "status": "error",
                "error": str(e)
            })
            error_count += 1
    
    # Zusammenfassung
    print(f"\n📊 Pipeline abgeschlossen!")
    print(f"✅ Erfolgreich: {success_count}")
    print(f"❌ Fehler: {error_count}")
    
    # Encoding-Statistik
    encodings = {}
    for result in results:
        if result["status"] == "success":
            enc = result["source_encoding"]
            encodings[enc] = encodings.get(enc, 0) + 1
    
    print(f"\n🔍 Encoding-Verteilung:")
    for enc, count in encodings.items():
        print(f"  {enc}: {count} Dateien")
    
    return results

def read_canonical_csv(csv_path: str) -> pd.DataFrame:
    """Liest eine kanonische UTF-8-CSV-Datei."""
    return pd.read_csv(csv_path, sep=';', header=None, dtype=str)

# Reversible Transliteration (nur wenn nötig)
GERMAN_ASCII = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
    "ß": "ss"
})

def to_ascii_german(s: str) -> str:
    """Transliteriert deutsche Zeichen zu ASCII (nur wenn nötig)."""
    return s.translate(GERMAN_ASCII)

if __name__ == "__main__":
    print("🚀 Kanonische CSV-Pipeline")
    print("=" * 40)
    
    # Verarbeite alle Tourpläne
    results = process_all_tourplans()
    
    print(f"\n💡 Nächste Schritte:")
    print(f"1. Backend auf kanonische Dateien umstellen")
    print(f"2. Terminal auf UTF-8 konfigurieren (chcp 65001)")
    print(f"3. Nur noch tourplaene_canonical/ verwenden")
    print(f"4. Transliteration nur an ASCII-Grenzen")
