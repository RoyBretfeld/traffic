#!/usr/bin/env python3
"""Praktischer Test: Funktioniert das LLM wirklich?"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

print("=" * 70)
print("PRAKTISCHER LLM-TEST")
print("=" * 70)

# Test 1: LLM-Optimizer praktisch testen
print("\n[TEST 1] LLM-Routenoptimierung (praktischer Test)")
try:
    from services.llm_optimizer import LLMOptimizer
    optimizer = LLMOptimizer()
    
    if not optimizer.enabled:
        print("  Status: [SKIP] LLM deaktiviert - kein API-Key")
    else:
        # Test mit einfachen Koordinaten
        test_stops = [
            {"name": "Depot", "lat": 51.0504, "lon": 13.7373, "address": "Stuttgarter Str. 33, 01189 Dresden"},
            {"name": "Kunde 1", "lat": 51.0700, "lon": 13.7500, "address": "Hauptstraße 1, 01097 Dresden"},
            {"name": "Kunde 2", "lat": 51.0600, "lon": 13.7300, "address": "Bahnhofstraße 5, 01099 Dresden"},
            {"name": "Kunde 3", "lat": 51.0550, "lon": 13.7400, "address": "Altmarkt 10, 01067 Dresden"},
        ]
        
        print(f"  Teste mit {len(test_stops)} Stopps...")
        result = optimizer.optimize_route(test_stops, region="Dresden")
        
        print(f"  Status: [OK] LLM funktioniert!")
        print(f"  Optimierte Route: {result.optimized_route}")
        print(f"  Confidence: {result.confidence_score:.2f}")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Zeit: {result.processing_time:.2f}s")
        print(f"  Model: {result.model_used}")
        print(f"  Reasoning: {result.reasoning[:100]}...")
        
except Exception as e:
    print(f"  Status: [FEHLER] {e}")
    import traceback
    traceback.print_exc()

# Test 2: LLM Address Helper praktisch testen
print("\n[TEST 2] LLM-Address-Helper (praktischer Test)")
try:
    from services.llm_address_helper import get_address_helper
    helper = get_address_helper()
    
    if not helper or not helper.enabled:
        print("  Status: [SKIP] LLM Address Helper deaktiviert")
    else:
        # Test mit problematischer Adresse
        test_address = "Hauptstr. 1, 01809 Heidenau"  # Bekanntes Problem (Hauptstr. vs Hauptstraße)
        print(f"  Teste Adresse: '{test_address}'")
        
        suggestion = helper.suggest(test_address)
        if suggestion:
            print(f"  Status: [OK] LLM funktioniert!")
            print(f"  Original: {test_address}")
            print(f"  Vorschlag: {suggestion.formatted_address}")
            print(f"  Confidence: {suggestion.confidence:.2f}")
        else:
            print(f"  Status: [WARN] Kein Vorschlag erhalten")
        
except Exception as e:
    print(f"  Status: [FEHLER] {e}")

print("\n" + "=" * 70)

