#!/usr/bin/env python3
"""Status-Check: App-Funktionalität prüfen"""

import sys
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = "http://127.0.0.1:8111"
TIMEOUT = 10.0

print("=" * 70)
print("APP STATUS-CHECK")
print("=" * 70)

def check_endpoint(path: str, method: str = "GET", data: dict = None) -> tuple:
    """Prüft einen Endpoint und gibt Status zurück"""
    try:
        url = f"{BASE_URL}{path}"
        if method == "GET":
            response = httpx.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = httpx.post(url, json=data, timeout=TIMEOUT)
        else:
            return False, f"Unbekannte Methode: {method}"
        
        if response.status_code == 200:
            return True, response.json() if response.headers.get("content-type", "").startswith("application/json") else "OK"
        else:
            return False, f"HTTP {response.status_code}"
    except httpx.ConnectError:
        return False, "Server nicht erreichbar"
    except Exception as e:
        return False, str(e)

# 1. Health Check
print("\n[1] HEALTH CHECK")
ok, msg = check_endpoint("/health")
if ok:
    print(f"  Status: [OK] Server läuft")
    if isinstance(msg, dict):
        print(f"  Details: {msg.get('status', 'OK')}")
else:
    print(f"  Status: [FEHLER] {msg}")

# 2. Database Health
print("\n[2] DATABASE")
ok, msg = check_endpoint("/health/db")
if ok:
    print(f"  Status: [OK] Datenbank erreichbar")
    if isinstance(msg, dict):
        tables = msg.get('tables', [])
        print(f"  Tabellen: {len(tables)} gefunden")
else:
    print(f"  Status: [FEHLER] {msg}")

# 3. Summary API
print("\n[3] SUMMARY API")
ok, msg = check_endpoint("/summary")
if ok:
    print(f"  Status: [OK] Summary verfügbar")
    if isinstance(msg, dict):
        print(f"  Kunden: {msg.get('kunden', 0)}")
        print(f"  Touren: {msg.get('touren', 0)}")
else:
    print(f"  Status: [WARN] {msg}")

# 4. Address Recognition
print("\n[4] ADDRESS RECOGNITION")
ok, msg = check_endpoint("/api/address-recognition/status")
if ok:
    print(f"  Status: [OK] Erkennungsrate verfügbar")
    if isinstance(msg, dict):
        rate = msg.get('recognition_rate', 0)
        print(f"  Erkennungsrate: {rate:.1f}%")
        print(f"  Geocodiert: {msg.get('geocoded_count', 0)}")
        print(f"  Gesamt: {msg.get('total_addresses', 0)}")
else:
    print(f"  Status: [WARN] {msg}")

# 5. Test Dashboard
print("\n[5] TEST DASHBOARD")
ok, msg = check_endpoint("/api/tests/status")
if ok:
    print(f"  Status: [OK] Test-Dashboard verfügbar")
    if isinstance(msg, dict):
        print(f"  Tests: {msg.get('passed', 0)}/{msg.get('total', 0)} bestanden")
else:
    print(f"  Status: [WARN] {msg}")

# 6. Frontend
print("\n[6] FRONTEND")
try:
    response = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT)
    if response.status_code == 200:
        print(f"  Status: [OK] Frontend erreichbar")
    else:
        print(f"  Status: [WARN] HTTP {response.status_code}")
except Exception as e:
    print(f"  Status: [FEHLER] {e}")

# 7. API Docs
print("\n[7] API DOCS")
try:
    response = httpx.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
    if response.status_code == 200:
        print(f"  Status: [OK] Swagger UI erreichbar")
        print(f"  URL: {BASE_URL}/docs")
    else:
        print(f"  Status: [WARN] HTTP {response.status_code}")
except Exception as e:
    print(f"  Status: [FEHLER] {e}")

# 8. Workflow API
print("\n[8] WORKFLOW API")
ok, msg = check_endpoint("/api/workflow/status")
if ok:
    print(f"  Status: [OK] Workflow API verfügbar")
    if isinstance(msg, dict):
        llm_status = msg.get('llm_status', 'unknown')
        print(f"  LLM Status: {llm_status}")
        endpoints = msg.get('endpoints', {})
        print(f"  Verfügbare Endpoints: {len(endpoints)}")
else:
    print(f"  Status: [WARN] {msg}")

print("\n" + "=" * 70)
print("ZUSAMMENFASSUNG:")
print(f"  Server: http://127.0.0.1:8111")
print(f"  Frontend: http://127.0.0.1:8111")
print(f"  API Docs: http://127.0.0.1:8111/docs")
print("=" * 70)

