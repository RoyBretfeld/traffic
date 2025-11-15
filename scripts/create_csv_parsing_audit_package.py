#!/usr/bin/env python3
"""
Erstellt ein ZIP-Archiv mit allen CSV-Parsing-relevanten Dateien für Code-Audit
"""

import zipfile
from pathlib import Path
import sys

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent

# CSV-Parsing-relevante Dateien
CSV_PARSING_FILES = [
    # Core CSV Processing
    "ingest/reader.py",
    "ingest/csv_reader.py",
    "ingest/http_responses.py",
    
    # Strict CSV Parser
    "backend/pipeline/csv_ingest_strict.py",
    "backend/pipeline/__init__.py",
    
    # Parsers
    "backend/parsers/tour_plan_parser.py",
    
    # Normalization & Cleaning
    "common/normalize.py",
    "common/text_cleaner.py",
    "backend/services/text_normalize.py",
    
    # Synonyms
    "backend/services/synonyms.py",
    
    # API Routes
    "routes/upload_csv.py",
    "routes/workflow_api.py",
    "routes/ai_test_api.py",
    "routes/tourplan_match.py",
    
    # Services
    "services/geocode_fill.py",
    
    # Database/Migrations
    "db/migrations/003_synonyms.sql",
    
    # Tests
    "tests/test_csv_ingest_strict.py",
    "tests/test_encoding_fixes.py",
]

# Zusätzliche Kontext-Dateien
CONTEXT_FILES = [
    "backend/app.py",  # Enthält read_tourplan_csv Funktion
    "README.md",
    "requirements.txt",
]

def create_csv_parsing_package():
    """Erstellt ZIP-Paket mit allen CSV-Parsing-Dateien"""
    
    output_zip = PROJECT_ROOT / "CSV_PARSING_AUDIT_PACKAGE.zip"
    
    print("=" * 70)
    print("CSV Parsing Audit Package Creator")
    print("=" * 70)
    print(f"\nErstelle ZIP-Archiv: {output_zip.name}")
    print(f"Projekt-Root: {PROJECT_ROOT}\n")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        all_files = CSV_PARSING_FILES + CONTEXT_FILES
        added_files = []
        missing_files = []
        
        for file_path in all_files:
            full_path = PROJECT_ROOT / file_path
            
            if full_path.exists():
                zipf.write(full_path, file_path)
                added_files.append(file_path)
                print(f"  [OK] {file_path}")
            else:
                missing_files.append(file_path)
                print(f"  [FEHLT] {file_path}")
        
        # Erstelle README für das Paket
        readme_content = f"""CSV Parsing Audit Package
==========================

Dieses Paket enthält alle Dateien, die mit CSV-Parsing, -Normalisierung 
und -Verarbeitung zu tun haben.

Erstellt am: {Path(__file__).stat().st_mtime}

Dateien im Paket:
-----------------

Core CSV Processing:
- ingest/reader.py - Zentraler CSV-Reader
- ingest/csv_reader.py - CSV-Reader Modul
- ingest/http_responses.py - HTTP-Response-Handler

Strict CSV Parser:
- backend/pipeline/csv_ingest_strict.py - Deterministischer CSV-Parser
- backend/pipeline/__init__.py - Pipeline-Package

Parsers:
- backend/parsers/tour_plan_parser.py - Tourplan-Parser

Normalization & Cleaning:
- common/normalize.py - Adress-Normalisierung
- common/text_cleaner.py - Text-Bereinigung (Mojibake-Reparatur)
- backend/services/text_normalize.py - Text-Normalisierung

Synonyms:
- backend/services/synonyms.py - Synonym-Verwaltung
- db/migrations/003_synonyms.sql - Synonym-Datenbank-Schema

API Routes:
- routes/upload_csv.py - CSV-Upload-Endpoint
- routes/workflow_api.py - Workflow mit CSV-Verarbeitung
- routes/ai_test_api.py - AI-Test mit CSV-Analyse
- routes/tourplan_match.py - Tourplan-Matching

Services:
- services/geocode_fill.py - Geocoding-Fill mit CSV

Database:
- db/migrations/003_synonyms.sql - Synonym-Migration

Tests:
- tests/test_csv_ingest_strict.py - Tests für strict CSV-Parser
- tests/test_encoding_fixes.py - Encoding-Tests

Context:
- backend/app.py - Enthält read_tourplan_csv Funktion
- README.md - Projekt-README
- requirements.txt - Python-Dependencies

Zusammenfassung:
- Gesamt: {len(added_files)} Dateien hinzugefügt
- Fehlend: {len(missing_files)} Dateien

Fehlende Dateien:
{chr(10).join(f'  - {f}' for f in missing_files) if missing_files else '  (Keine)'
}

Hinweise:
---------
1. Dieses Paket enthält alle CSV-Parsing-relevanten Dateien
2. Die Dateien können zum Code-Audit verwendet werden
3. Um zum Kern zurückzukehren, fokussiere auf:
   - ingest/csv_reader.py (zentraler Reader)
   - backend/pipeline/csv_ingest_strict.py (striker Parser)
   - common/normalize.py (Normalisierung)
"""
        
        zipf.writestr("AUDIT_README.txt", readme_content)
        print(f"\n  [OK] AUDIT_README.txt erstellt")
    
    print("\n" + "=" * 70)
    print(f"ZIP-Archiv erfolgreich erstellt: {output_zip}")
    print(f"Größe: {output_zip.stat().st_size / 1024:.2f} KB")
    print(f"Dateien: {len(added_files)}")
    if missing_files:
        print(f"\nWarnung: {len(missing_files)} Dateien fehlen!")
    print("=" * 70)
    
    return output_zip

if __name__ == "__main__":
    try:
        zip_file = create_csv_parsing_package()
        print(f"\n✓ Erfolgreich: {zip_file.name}")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

