#!/usr/bin/env python3
"""
Tests für die zentrale Adress-Normalisierung
"""
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.normalize import normalize_address

def test_pipes_become_commas_and_trim():
    """Test: Pipes werden zu Kommas und Whitespace wird bereinigt"""
    assert normalize_address('Fröbelstraße 1 | Dresden') == 'Fröbelstraße 1, Dresden'
    assert normalize_address(' A | B |  C ') == 'A, B, C'
    assert normalize_address('A||B') == 'A, B'
    assert normalize_address('Naumannstraße 12 | Halle 14, 01809 Heidenau') == 'Naumannstraße 12, Halle 14, 01809 Heidenau'

def test_multiple_commas_and_spaces():
    """Test: Mehrfach-Trenner werden bereinigt"""
    assert normalize_address('A, ,  B ; ; C') == 'A, B, C'
    assert normalize_address('A;;B,,C') == 'A, B, C'

def test_safe_mojibake_fixes_only():
    """Test: Sichere Mojibake-Fixes werden angewendet"""
    assert normalize_address('FrÃ¶belstraÃŸe 1, Dresden') == 'Fröbelstraße 1, Dresden'
    assert normalize_address('MÃ¼llerstraÃŸe 5') == 'Müllerstraße 5'

def test_edge_cases():
    """Test: Edge Cases"""
    assert normalize_address(None) == ""
    assert normalize_address("") == ""
    assert normalize_address("   ") == ""
    assert normalize_address("A") == "A"
    assert normalize_address("A, B") == "A, B"

def test_dreihundert_specific():
    """Test: Spezifischer Fall für Dreihundert Dresden"""
    dreihundert_addr = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    expected = "Naumannstraße 12, Halle 14, 01809 Heidenau"
    result = normalize_address(dreihundert_addr)
    assert result == expected, f"Expected '{expected}', got '{result}'"

def run_tests():
    """Führe alle Tests aus"""
    tests = [
        test_pipes_become_commas_and_trim,
        test_multiple_commas_and_spaces,
        test_safe_mojibake_fixes_only,
        test_edge_cases,
        test_dreihundert_specific
    ]
    
    print("🧪 Teste zentrale Adress-Normalisierung...")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("="*60)
    print(f"📊 Ergebnis: {passed} bestanden, {failed} fehlgeschlagen")
    
    if failed == 0:
        print("🎉 Alle Tests erfolgreich!")
        return True
    else:
        print("⚠️ Einige Tests fehlgeschlagen!")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
