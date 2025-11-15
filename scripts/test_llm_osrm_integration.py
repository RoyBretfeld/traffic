#!/usr/bin/env python3
"""Test: LLM + OSRM Integration"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

# Setze OSRM-URL für Test
os.environ["OSRM_BASE_URL"] = os.getenv("OSRM_BASE_URL", "http://localhost:5000")

print("=" * 70)
print("TEST: LLM + OSRM INTEGRATION")
print("=" * 70)

# Test mit echten Dresdner Koordinaten
test_stops = [
    {
        "name": "FAMO Depot",
        "lat": 51.0504,
        "lon": 13.7373,
        "address": "Stuttgarter Str. 33, 01189 Dresden"
    },
    {
        "name": "Kunde 1",
        "lat": 51.0700,
        "lon": 13.7500,
        "address": "Hauptstraße 1, 01097 Dresden"
    },
    {
        "name": "Kunde 2",
        "lat": 51.0600,
        "lon": 13.7300,
        "address": "Bahnhofstraße 5, 01099 Dresden"
    },
    {
        "name": "Kunde 3",
        "lat": 51.0550,
        "lon": 13.7400,
        "address": "Altmarkt 10, 01067 Dresden"
    },
]

print(f"\n[TEST] Optimierung mit {len(test_stops)} Stopps...")
print(f"OSRM_URL: {os.getenv('OSRM_BASE_URL')}")

try:
    from services.llm_optimizer import LLMOptimizer
    optimizer = LLMOptimizer()
    
    if not optimizer.enabled:
        print("\n[FEHLER] LLM nicht aktiviert - kein API-Key")
        sys.exit(1)
    
    print(f"  LLM Status: [OK] Aktiv ({optimizer.model})")
    print(f"  OSRM Status: {'[OK] Konfiguriert' if optimizer.osrm_base else '[WARN] Nicht konfiguriert'}")
    
    print(f"\n  Starte Optimierung (inkl. OSRM-Distanzen)...")
    result = optimizer.optimize_route(test_stops, region="Dresden")
    
    print(f"\n  Ergebnis:")
    print(f"    Route: {result.optimized_route}")
    print(f"    Confidence: {result.confidence_score:.2f}")
    print(f"    Tokens: {result.tokens_used}")
    print(f"    Zeit: {result.processing_time:.2f}s")
    print(f"    Model: {result.model_used}")
    
    if result.reasoning:
        print(f"\n    Reasoning (Auszug):")
        print(f"    {result.reasoning[:200]}...")
    
    print(f"\n  [OK] Integration funktioniert!")
    
except Exception as e:
    print(f"\n[FEHLER] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)

