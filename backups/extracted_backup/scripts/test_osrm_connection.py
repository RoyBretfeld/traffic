#!/usr/bin/env python3
"""Test: OSRM-Verbindung und Zugriff"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

import httpx
import asyncio

print("=" * 70)
print("OSRM-VERBINDUNGS-TEST")
print("=" * 70)

# 1. Konfiguration prüfen
osrm_url = os.getenv("OSRM_BASE_URL", "http://localhost:5000")
print(f"\n[1] Konfiguration:")
print(f"  OSRM_BASE_URL: {osrm_url}")
print(f"  OSRM_PROFILE: {os.getenv('OSRM_PROFILE', 'driving')}")

# 2. Health-Check (Service erreichbar?)
print(f"\n[2] Service-Erreichbarkeit:")
try:
    response = httpx.get(f"{osrm_url}/route/v1/driving/13.7373,51.0504;13.7500,51.0700?overview=false", timeout=5.0)
    if response.status_code == 200:
        data = response.json()
        if "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]
            distance_km = route.get("distance", 0) / 1000.0
            duration_min = route.get("duration", 0) / 60.0
            print(f"  Status: [OK] OSRM erreichbar und funktioniert!")
            print(f"  Test-Route: {distance_km:.2f} km, {duration_min:.1f} min")
        else:
            print(f"  Status: [WARN] OSRM antwortet, aber keine Route gefunden")
    else:
        print(f"  Status: [FEHLER] HTTP {response.status_code}")
except httpx.ConnectError:
    print(f"  Status: [FEHLER] OSRM nicht erreichbar - Service läuft nicht?")
    print(f"  Lösung: Docker starten mit 'docker-compose up osrm' oder Service starten")
except Exception as e:
    print(f"  Status: [FEHLER] {e}")

# 3. Integration prüfen
print(f"\n[3] Integration im Code:")
try:
    from backend.services.real_routing import RealRoutingService
    routing = RealRoutingService()
    
    if routing.osrm_base:
        print(f"  Status: [OK] RealRoutingService verwendet: {routing.osrm_base}")
    else:
        print(f"  Status: [WARN] RealRoutingService hat keine OSRM-URL")
        
except Exception as e:
    print(f"  Status: [FEHLER] {e}")

# 4. Docker-Status prüfen
print(f"\n[4] Docker-Status:")
try:
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=osrm", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if "osrm" in result.stdout.lower():
        print(f"  Status: [OK] OSRM Container läuft")
        print(f"  Container: {result.stdout.strip()}")
    else:
        print(f"  Status: [WARN] OSRM Container läuft nicht")
        print(f"  Lösung: 'docker-compose up -d osrm' ausführen")
except FileNotFoundError:
    print(f"  Status: [SKIP] Docker nicht verfügbar")
except Exception as e:
    print(f"  Status: [INFO] Docker-Status nicht prüfbar: {e}")

print("\n" + "=" * 70)
print("FAZIT:")
print(f"  OSRM muss konfiguriert und erreichbar sein für AI-Integration")
print("=" * 70)

