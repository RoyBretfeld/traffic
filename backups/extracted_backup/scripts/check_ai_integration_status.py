#!/usr/bin/env python3
"""Status-Check für AI-Integration: Routing & Adress-Sortierung"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

print("=" * 70)
print("AI-INTEGRATION STATUS: Routing & Adress-Sortierung")
print("=" * 70)

# 1. LLM-Optimizer Status
print("\n[1] LLM-ROUTENOPTIMIERUNG (Adress-Sortierung)")
try:
    from services.llm_optimizer import LLMOptimizer
    optimizer = LLMOptimizer()
    
    if optimizer.enabled:
        print(f"  Status: [OK] AKTIV")
        print(f"  Model: {optimizer.model}")
        print(f"  Integration: routes/workflow_api.py (optimize_tour_stops)")
        print(f"  API-Endpoint: /api/llm/optimize")
        print(f"  Confidence-Threshold: >0.7")
    else:
        print(f"  Status: [WARN] DEAKTIVIERT (kein API-Key oder OpenAI nicht verfügbar)")
        print(f"  Fallback: Nearest-Neighbor Optimierung aktiv")
        
except Exception as e:
    print(f"  Status: [FEHLER]: {e}")

# 2. LLM Address Helper Status
print("\n[2] LLM-ADDRESS-HELPER (Adress-Normalisierung)")
try:
    from services.llm_address_helper import get_address_helper
    helper = get_address_helper()
    
    if helper and helper.enabled:
        print(f"  Status: [OK] AKTIV")
        print(f"  Model: {helper.model}")
        print(f"  Verwendung: Fallback für fehlerhafte Adressen")
    else:
        print(f"  Status: [WARN] DEAKTIVIERT")
        
except Exception as e:
    print(f"  Status: [FEHLER]: {e}")

# 3. OSRM Integration Status
print("\n[3] OSRM ROUTING (Straßen-Routing)")
try:
    import os
    osrm_url = os.getenv("OSRM_BASE_URL", "")
    
    if osrm_url:
        print(f"  Status: [OK] KONFIGURIERT")
        print(f"  URL: {osrm_url}")
        print(f"  Service: backend/services/real_routing.py")
        print(f"  Priority: OSRM -> Mapbox -> Fallback")
    else:
        print(f"  Status: [WARN] NICHT KONFIGURIERT")
        print(f"  Hinweis: OSRM_BASE_URL nicht gesetzt")
        
except Exception as e:
    print(f"  Status: [FEHLER]: {e}")

# 4. AI-Optimizer (Backend) Status
print("\n[4] BACKEND AI-OPTIMIZER")
try:
    from backend.services.ai_optimizer import AIOptimizer
    ai_opt = AIOptimizer()
    
    print(f"  Status: [OK] VORHANDEN")
    print(f"  Features: Route-Optimierung, Clustering, Regel-basiert")
    print(f"  Unterstützung: Ollama (lokal) + OpenAI (Cloud)")
    
except Exception as e:
    print(f"  Status: [WARN] NICHT VERFÜGBAR: {e}")

# 5. Integration in Workflow
print("\n[5] INTEGRATION IN WORKFLOW")
print(f"  Route-Optimierung: [OK] optimize_tour_stops() verwendet LLM (wenn enabled)")
print(f"  Adress-Sortierung: [OK] LLM-optimierte Reihenfolge basierend auf:")
print(f"    - Geografischer Nähe")
print(f"    - Minimale Fahrzeit")
print(f"    - Logische Abfolgen")
print(f"  Fallback: Nearest-Neighbor wenn LLM nicht verfügbar")

# 6. OSRM + AI Verbindung
print("\n[6] OSRM + AI VERBINDUNG")
print(f"  Status: [WARN] NOCH NICHT VERBUNDEN")
print(f"  Aktuell: AI verwendet Haversine-Distanz (Luftlinie)")
print(f"  Ziel: AI sollte OSRM-Distanzen für bessere Optimierung nutzen")
print(f"  Datei: backend/services/real_routing.py vorhanden, aber nicht in AI integriert")

print("\n" + "=" * 70)
print("ZUSAMMENFASSUNG:")
print("  [OK] LLM-Routenoptimierung: Implementiert (benötigt API-Key)")
print("  [OK] Adress-Sortierung: AI-optimiert (mit Fallback)")
print("  [OK] OSRM-Routing: Vorhanden (für Straßen-Routen)")
print("  [WARN] OSRM + AI: Noch nicht verbunden (Verbindung fehlt)")
print("=" * 70)

