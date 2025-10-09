#!/usr/bin/env python3
"""
Smoke-Test für FAMO TrafficApp
Testet die Kernpfade: list → match → geocode-missing (dry) → status
"""
from __future__ import annotations
import os
import json
import sys
from urllib.parse import urlencode

# API-Base-URL aus Umgebungsvariablen
API = os.getenv("API_BASE", "http://127.0.0.1:8111")

try:
    import httpx
except ImportError:
    print("ERROR: httpx nicht installiert. Führe 'pip install httpx' aus.")
    sys.exit(1)

# Farbige Ausgabe für bessere Lesbarkeit (Windows-kompatibel)
OK = "[OK]"    # Grün
BAD = "[ERROR]"  # Rot
INFO = "[INFO]"  # Blau

def _get(client, path, **params):
    """HTTP GET-Anfrage mit Parametern."""
    url = f"{API}{path}" + ("?" + urlencode(params) if params else "")
    try:
        r = client.get(url, timeout=15)
        return r.status_code, r.headers.get('content-type', ''), r.text
    except httpx.TimeoutException:
        return 408, '', "Timeout"
    except httpx.ConnectError:
        return 503, '', "Connection Error"

def main():
    """Führt den Smoke-Test durch."""
    print(f"{INFO} Smoke-Test für FAMO TrafficApp")
    print(f"{INFO} API-Base: {API}")
    print()
    
    with httpx.Client() as c:
        # 1) List - Verfügbare CSVs abrufen
        print("1. Teste /api/tourplaene/list...")
        code, ct, body = _get(c, "/api/tourplaene/list")
        if code != 200:
            print(f"{BAD} list: HTTP {code} - {ct}")
            print(f"   Response: {body[:300]}")
            return 2
        
        try:
            j = json.loads(body)
            files = j.get("files", [])
            if not files:
                print(f"{BAD} list: Keine CSV-Dateien im ORIG_DIR gefunden")
                return 3
            file_path = files[0]["path"]
            print(f"{OK} list: {files[0]['name']} gefunden")
        except json.JSONDecodeError:
            print(f"{BAD} list: Ungültiges JSON - {body[:100]}")
            return 3

        # 2) Match - Adressen gegen Cache matchen
        print("2. Teste /api/tourplan/match...")
        code, ct, body = _get(c, "/api/tourplan/match", file=file_path)
        if code != 200:
            print(f"{BAD} match: HTTP {code} - {ct}")
            print(f"   Response: {body[:300]}")
            return 4
        
        try:
            m = json.loads(body)
            ok_count = m.get('ok', 0)
            warn_count = m.get('warn', 0)
            bad_count = m.get('bad', 0)
            print(f"{OK} match: ok={ok_count}, warn={warn_count}, bad={bad_count}")
        except json.JSONDecodeError:
            print(f"{BAD} match: Ungültiges JSON - {body[:100]}")
            return 4

        # 3) Geocode-missing (dry run) - Fehlende Adressen geokodieren
        print("3. Teste /api/tourplan/geocode-missing (dry run)...")
        code, ct, body = _get(c, "/api/tourplan/geocode-missing", 
                             file=file_path, limit=5, dry_run=True)
        if code != 200:
            print(f"{BAD} geofill: HTTP {code} - {ct}")
            print(f"   Response: {body[:300]}")
            return 5
        
        try:
            g = json.loads(body)
            processed = g.get('processed', 0)
            print(f"{OK} geofill dry: {processed} Adressen verarbeitet")
        except json.JSONDecodeError:
            print(f"{BAD} geofill: Ungültiges JSON - {body[:100]}")
            return 5

        # 4) Status - Status-Zähler abrufen
        print("4. Teste /api/tourplan/status...")
        code, ct, body = _get(c, "/api/tourplan/status", file=file_path)
        if code != 200:
            print(f"{BAD} status: HTTP {code} - {ct}")
            print(f"   Response: {body[:300]}")
            return 6
        
        try:
            s = json.loads(body)
            total = s.get('total', 0)
            cached = s.get('cached', 0)
            missing = s.get('missing', 0)
            print(f"{OK} status: total={total}, cached={cached}, missing={missing}")
        except json.JSONDecodeError:
            print(f"{BAD} status: Ungültiges JSON - {body[:100]}")
            return 6

    print()
    print(f"{OK} Smoke-Test erfolgreich abgeschlossen!")
    print(f"{INFO} Alle Kernpfade funktionieren korrekt.")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{BAD} Smoke-Test abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n{BAD} Unerwarteter Fehler: {e}")
        sys.exit(1)
