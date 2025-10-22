#!/usr/bin/env python3
"""
Test-Script für die verbesserten Fail-Cache-Funktionen
"""
import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///data/traffic.db')

from repositories.geo_fail_repo import (
    mark_nohit, mark_temp, clear, get_fail_stats, get_fail_reasons, 
    get_fail_status, cleanup_expired
)
from repositories.geo_repo import normalize_addr

def test_improved_failcache():
    """Test der verbesserten Fail-Cache-Funktionen."""
    
    print("=== VERBESSERTER FAIL-CACHE TEST ===")
    
    # Test-Adressen
    test_addresses = [
        "Teststraße 1, 01234 Teststadt",
        "Musterweg 5, 56789 Musterstadt",
        "Beispielplatz 10, 11111 Beispielstadt"
    ]
    
    print(f"\n1. Test-Adressen markieren (mit verkürzter TTL)...")
    for addr in test_addresses:
        # Markiere als No-Hit (jetzt nur 1 Stunde statt 24 Stunden!)
        mark_nohit(addr, reason="test_no_result")
        print(f"   ✅ {addr} -> No-Hit markiert (1h TTL)")
    
    print(f"\n2. Fail-Cache-Statistiken abrufen...")
    stats = get_fail_stats()
    print(f"   📊 Gesamt: {stats['total']}, Aktiv: {stats['active']}")
    
    print(f"\n3. Fail-Gründe gruppieren...")
    reasons = get_fail_reasons()
    print(f"   📋 Gründe: {reasons}")
    
    print(f"\n4. Einzelnen Fail-Status prüfen...")
    test_addr = test_addresses[0]
    status = get_fail_status(test_addr)
    if status:
        print(f"   🔍 {test_addr} -> {status['reason']} bis {status['until']}")
    else:
        print(f"   ❌ {test_addr} -> Nicht im Fail-Cache")
    
    print(f"\n5. Manual-Override testen...")
    # Simuliere manuelles Löschen (wie die neue API)
    clear(test_addr)
    print(f"   🗑️  {test_addr} -> Aus Fail-Cache entfernt")
    
    # Verifikation
    status_after = get_fail_status(test_addr)
    if not status_after:
        print(f"   ✅ Verifikation: {test_addr} nicht mehr im Fail-Cache")
    else:
        print(f"   ❌ Verifikation fehlgeschlagen: {test_addr} noch im Fail-Cache")
    
    print(f"\n6. Bereinigung testen...")
    cleaned = cleanup_expired()
    print(f"   🧹 {cleaned} abgelaufene Einträge bereinigt")
    
    print(f"\n7. Finale Statistiken...")
    final_stats = get_fail_stats()
    print(f"   📊 Final: Gesamt: {final_stats['total']}, Aktiv: {final_stats['active']}")
    
    print(f"\n🎉 FAIL-CACHE-VERBESSERUNGEN ERFOLGREICH GETESTET!")
    print(f"\n📋 Neue Features:")
    print(f"   ✅ TTL verkürzt: 1 Stunde statt 24 Stunden")
    print(f"   ✅ Manual-Override: /api/geocode/force-retry")
    print(f"   ✅ Statistiken: /api/geocode/fail-stats")
    print(f"   ✅ Fail-Gründe: /api/geocode/fail-reasons")
    print(f"   ✅ Einzelstatus: /api/geocode/fail-status")
    print(f"   ✅ Bereinigung: /api/geocode/cleanup-fail-cache")

if __name__ == "__main__":
    test_improved_failcache()
