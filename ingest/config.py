#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale Encoding-Konfiguration für FAMO TrafficApp
==================================================

Dieses Modul stellt die zentrale Encoding-Konfiguration bereit.
"""

# Zentrale Encoding-Konfiguration
CSV_INPUT_ENCODING = "cp850"  # Windows-Standard für CSV-Exporte
CSV_OUTPUT_ENCODING = "utf-8"  # Standard für alle Ausgaben
HTTP_CHARSET = "utf-8"  # Standard für HTTP-Responses
LOG_ENCODING = "utf-8"  # Standard für Logging

# Encoding-Priorität für CSV-Ingest
ENCODING_PRIORITY = [
    "cp850",      # Windows-Standard
    "utf-8-sig",  # UTF-8 mit BOM
    "utf-8",      # UTF-8 ohne BOM
    "latin-1",    # Fallback
]

# Mojibake-Marker (aus guards.py importiert)
from ingest.guards import BAD_MARKERS

# Export-Konfiguration
EXPORT_CONFIG = {
    "csv": {
        "encoding": "utf-8",
        "sep": ";",
        "index": False
    },
    "excel": {
        "encoding": "utf-8-sig",  # Mit BOM für Excel-Kompatibilität
        "index": False
    },
    "json": {
        "ensure_ascii": False,  # Unicode-Zeichen beibehalten
        "indent": 2
    }
}

if __name__ == "__main__":
    print("Encoding-Konfiguration:")
    print(f"CSV Input: {CSV_INPUT_ENCODING}")
    print(f"CSV Output: {CSV_OUTPUT_ENCODING}")
    print(f"HTTP Charset: {HTTP_CHARSET}")
    print(f"Log Encoding: {LOG_ENCODING}")
    print(f"Encoding Priority: {ENCODING_PRIORITY}")
    print(f"Bad Markers: {len(BAD_MARKERS)} gefunden")
