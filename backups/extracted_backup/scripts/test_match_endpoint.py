#!/usr/bin/env python3
"""Test Match-Endpoint"""
import requests
import urllib.parse
from pathlib import Path

file_path = Path("data/staging/1762276034_Tourenplan_08.10.2025.csv").resolve()
url = f'http://localhost:8111/api/tourplan/match?file={urllib.parse.quote(str(file_path))}'

print(f"Teste Match-Endpoint...")
print(f"Datei: {file_path}")
print(f"Existiert: {file_path.exists()}")
print(f"URL: {url}")
print()

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Fehler: {response.text[:500]}")
    else:
        data = response.json()
        print(f"OK - {len(data.get('items', []))} Items gefunden")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()

