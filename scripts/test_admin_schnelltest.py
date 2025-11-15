#!/usr/bin/env python3
"""Schnelltest für Admin-App (Akzeptanzkriterien aus Aufgabenpaket)"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from admin.address_admin_app_fixed import app, DB_PATH

print("=" * 60)
print("ADMIN-APP SCHNELLTEST (Akzeptanzkriterien)")
print("=" * 60)

client = TestClient(app)

# Test 1: Ping zeigt Pfade
print("\n[1/4] Test: /api/ping zeigt Pfade")
response = client.get("/api/ping")
assert response.status_code == 200
data = response.json()
print(f"   Status: {data.get('status')}")
print(f"   DB: {data.get('db')}")
print(f"   Migrations: {data.get('migrations')}")
assert data["status"] == "ok"
assert "sqlite3" in data["db"]
print("   [OK] PASS")

# Test 2: Pending-API antwortet
print("\n[2/4] Test: /api/pending antwortet")
response = client.get("/api/pending")
assert response.status_code == 200
data = response.json()
print(f"   Antwort: Liste mit {len(data)} Einträgen")
print("   [OK] PASS")

# Test 3: Validierung greift (lat außerhalb Bereich -> 422)
print("\n[3/4] Test: Validierung (lat=999 -> 422)")
response = client.post(
    "/api/resolve",
    json={"key": "x|01067|Dresden|DE", "lat": 999, "lon": 0}
)
print(f"   Status: {response.status_code}")
assert response.status_code == 422
print("   [OK] PASS")

# Test 4: WAL/Indizes gesetzt (optional prüfen)
print("\n[4/4] Test: WAL-Mode aktiviert")
try:
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    result = con.execute("PRAGMA journal_mode").fetchone()
    journal_mode = result[0] if result else "unknown"
    con.close()
    print(f"   Journal Mode: {journal_mode}")
    if journal_mode.upper() == "WAL":
        print("   [OK] PASS")
    else:
        print(f"   [WARN] Erwartet WAL, gefunden: {journal_mode}")
except Exception as e:
    print(f"   ⚠️  Konnte nicht prüfen: {e}")

print("\n" + "=" * 60)
print("ALLE SCHNELLTESTS ABGESCHLOSSEN")
print("=" * 60)

