#!/usr/bin/env python3
from backend.db.dao import geocache_get
import traceback

def test_geocache_get():
    try:
        result = geocache_get('Naumannstraße 12, 01809 Heidenau')
        print(f'Ergebnis: {result}')
        print(f'Typ: {type(result)}')
    except Exception as e:
        print(f'Fehler: {e}')
        traceback.print_exc()

if __name__ == "__main__":
    test_geocache_get()
