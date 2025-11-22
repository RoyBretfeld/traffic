#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Täglicher Fehler-Report: Zeigt alle dokumentierten Fehler und Statistiken.
"""
import sys
import io
from pathlib import Path
from datetime import datetime
import re

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def parse_lessons_log():
    """Parst LESSONS_LOG.md und extrahiert Fehler-Einträge."""
    lessons_path = project_root / "Regeln" / "LESSONS_LOG.md"
    
    if not lessons_path.exists():
        return {
            "total_errors": 0,
            "errors": [],
            "last_update": None
        }
    
    content = lessons_path.read_text(encoding='utf-8')
    
    # Suche nach Fehler-Einträgen (## mit Datum oder ## mit Nummer)
    error_pattern = r'^##\s+(?:(\d{4}-\d{2}-\d{2})\s*–\s*(.+)|#?\s*(\d+)\.?\s+(.+))$'
    errors = []
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        match = re.match(error_pattern, line)
        if match:
            if match.group(1):  # Datum-Format: "2025-11-22 – Titel"
                error_date = match.group(1)
                error_title = match.group(2).strip()
                error_num = None
            else:  # Nummer-Format: "## #1 Titel"
                error_num = match.group(3)
                error_title = match.group(4).strip()
                error_date = None
            
            # Sammle Details bis zum nächsten Eintrag
            details = []
            for j in range(i + 1, min(i + 20, len(lines))):
                if re.match(error_pattern, lines[j]):
                    break
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    details.append(lines[j].strip())
            
            errors.append({
                "number": int(error_num) if error_num else None,
                "date": error_date,
                "title": error_title,
                "details": '\n'.join(details[:5])  # Erste 5 Zeilen
            })
    
    # Finde letztes Update-Datum
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    dates = re.findall(date_pattern, content)
    last_update = dates[-1] if dates else None
    
    return {
        "total_errors": len(errors),
        "errors": errors,
        "last_update": last_update
    }


def check_error_catalog():
    """Prüft ERROR_CATALOG.md für weitere Fehler."""
    catalog_path = project_root / "docs" / "ERROR_CATALOG.md"
    
    if not catalog_path.exists():
        return {
            "exists": False,
            "count": 0
        }
    
    content = catalog_path.read_text(encoding='utf-8')
    
    # Zähle Fehler-Kategorien (## Überschriften)
    categories = len(re.findall(r'^##\s+', content, re.MULTILINE))
    
    return {
        "exists": True,
        "count": categories
    }


def check_recent_docs():
    """Prüft auf neue Dokumentation mit Fehlern."""
    docs_path = project_root / "docs"
    today = datetime.now().strftime("%Y-%m-%d")
    
    recent_docs = []
    for doc_file in docs_path.glob("*.md"):
        if doc_file.stat().st_mtime > (datetime.now().timestamp() - 86400):  # Letzte 24h
            content = doc_file.read_text(encoding='utf-8', errors='ignore')
            if any(keyword in content.lower() for keyword in ['fehler', 'error', 'bug', 'problem', 'fix']):
                recent_docs.append(doc_file.name)
    
    return recent_docs


def main():
    print("=" * 60)
    print("TÄGLICHER FEHLER-REPORT")
    print("=" * 60)
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. LESSONS_LOG.md
    print("1. LESSONS_LOG.md (Dokumentierte Fehler):")
    print("-" * 60)
    lessons_data = parse_lessons_log()
    print(f"   Gesamtanzahl dokumentierter Fehler: {lessons_data['total_errors']}")
    if lessons_data['last_update']:
        print(f"   Letztes Update: {lessons_data['last_update']}")
    print()
    
    if lessons_data['errors']:
        print("   Fehler-Übersicht (letzte 10):")
        for error in lessons_data['errors'][-10:]:  # Letzte 10
            if error['date']:
                print(f"   - {error['date']}: {error['title']}")
            elif error['number']:
                print(f"   - #{error['number']}: {error['title']}")
            else:
                print(f"   - {error['title']}")
        if len(lessons_data['errors']) > 10:
            print(f"   ... und {len(lessons_data['errors']) - 10} weitere")
    print()
    
    # 2. ERROR_CATALOG.md
    print("2. ERROR_CATALOG.md (Fehler-Katalog):")
    print("-" * 60)
    catalog_data = check_error_catalog()
    if catalog_data['exists']:
        print(f"   Fehler-Kategorien: {catalog_data['count']}")
    else:
        print("   ERROR_CATALOG.md nicht gefunden")
    print()
    
    # 3. Neue Dokumentation heute
    print("3. Neue Dokumentation (letzte 24h):")
    print("-" * 60)
    recent_docs = check_recent_docs()
    if recent_docs:
        print(f"   {len(recent_docs)} Dokument(e) mit Fehler-Referenzen:")
        for doc in recent_docs:
            print(f"   - {doc}")
    else:
        print("   Keine neuen Dokumente mit Fehler-Referenzen")
    print()
    
    # 4. Zusammenfassung
    print("=" * 60)
    print("ZUSAMMENFASSUNG:")
    print(f"   Dokumentierte Fehler (LESSONS_LOG): {lessons_data['total_errors']}")
    print(f"   Fehler-Kategorien (ERROR_CATALOG): {catalog_data['count'] if catalog_data['exists'] else 0}")
    print(f"   Neue Dokumente heute: {len(recent_docs)}")
    print("=" * 60)
    print()
    print("Tipp: Fuehre dieses Script taeglich aus, um den Ueberblick zu behalten.")


if __name__ == "__main__":
    main()

