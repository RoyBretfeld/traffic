#!/usr/bin/env python3
"""
OSRM Health-Check Script
Prüft ob OSRM erreichbar ist und gibt detaillierte Informationen zurück.
"""
import sys
from pathlib import Path

# Füge Projektroot zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
import time
from backend.config import get_osrm_settings
from services.osrm_client import OSRMClient

def test_osrm_direct(url: str, timeout: float = 5.0):
    """Direkter HTTP-Test auf OSRM."""
    print(f"\n[TEST] Teste OSRM direkt auf {url}...")
    start = time.time()
    try:
        # Test mit nearest endpoint (billig)
        r = httpx.get(f"{url}/nearest/v1/driving/13.7373,51.0504", timeout=timeout)
        latency_ms = int((time.time() - start) * 1000)
        
        if r.status_code == 200:
            print(f"   [OK] OSRM erreichbar")
            print(f"   Status: {r.status_code}")
            print(f"   Latenz: {latency_ms}ms")
            return True
        else:
            print(f"   [WARN] OSRM antwortet mit Status {r.status_code}")
            print(f"   Latenz: {latency_ms}ms")
            return False
    except httpx.TimeoutException:
        latency_ms = int((time.time() - start) * 1000)
        print(f"   [ERROR] Timeout nach {latency_ms}ms")
        return False
    except httpx.ConnectError:
        print(f"   [ERROR] Verbindungsfehler - OSRM laeuft nicht auf {url}")
        return False
    except Exception as e:
        print(f"   [ERROR] Fehler: {e}")
        return False

def test_osrm_client():
    """Test mit OSRMClient."""
    print(f"\n[TEST] Teste OSRM mit OSRMClient...")
    try:
        client = OSRMClient()
        health = client.check_health()
        
        # Pydantic-Modell: Attribut-Zugriff statt .get()
        print(f"   Base URL: {health.base_url}")
        print(f"   Reachable: {health.reachable}")
        print(f"   Sample OK: {health.sample_ok}")
        print(f"   Message: {health.message or 'unknown'}")
        print(f"   Circuit Breaker: {health.circuit_breaker_state}")
        
        if health.reachable and health.sample_ok:
            print(f"   [OK] OSRM-Client meldet: OK")
            return True
        else:
            print(f"   [WARN] OSRM-Client meldet: nicht erreichbar oder Sample fehlgeschlagen")
            return False
    except Exception as e:
        print(f"   [ERROR] Fehler beim OSRM-Client-Test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("OSRM Health-Check")
    print("=" * 70)
    
    # Lade Konfiguration
    settings = get_osrm_settings()
    print(f"\n[CONFIG] Konfiguration:")
    print(f"   OSRM URL: {settings.OSRM_BASE_URL}")
    print(f"   Timeout: {settings.OSRM_TIMEOUT_S}s")
    
    # Teste konfigurierte URL
    url = settings.OSRM_BASE_URL
    result1 = test_osrm_direct(url, timeout=float(settings.OSRM_TIMEOUT_S))
    
    # Teste auch Port 5000 (falls unterschiedlich)
    if ":5011" in url:
        url_5000 = url.replace(":5011", ":5000")
        print(f"\n[TEST] Teste auch Port 5000 ({url_5000})...")
        result2 = test_osrm_direct(url_5000, timeout=5.0)
    else:
        result2 = None
    
    # Teste mit OSRMClient
    result3 = test_osrm_client()
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("Zusammenfassung:")
    print("=" * 70)
    print(f"   Direkter Test ({url}): {'[OK]' if result1 else '[FEHLER]'}")
    if result2 is not None:
        print(f"   Direkter Test (Port 5000): {'[OK]' if result2 else '[FEHLER]'}")
    print(f"   OSRMClient-Test: {'[OK]' if result3 else '[FEHLER]'}")
    
    if result1 or result2 or result3:
        print("\n[OK] OSRM ist erreichbar!")
        return 0
    else:
        print("\n[ERROR] OSRM ist NICHT erreichbar!")
        print("\n[HINWEIS] Moegliche Loesungen:")
        print("   - Pruefe ob OSRM laeuft: docker ps | grep osrm")
        print("   - Starte OSRM: docker-compose up osrm")
        print("   - Oder setze OSRM_BASE_URL auf oeffentlichen Service")
        return 1

if __name__ == "__main__":
    sys.exit(main())

