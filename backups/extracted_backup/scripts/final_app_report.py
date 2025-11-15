#!/usr/bin/env python3
"""Finaler App-Status Report"""

import sys
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = "http://127.0.0.1:8111"

print("=" * 70)
print("FAMO TRAFFICAPP - FINALER STATUS REPORT")
print("=" * 70)

# Funktionierende Features
print("\n[OK] FUNKTIONIERT:")
features_ok = []

# Health & Database
try:
    resp = httpx.get(f"{BASE_URL}/health/db", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        tables_str = data.get('tables', '')
        table_count = len(tables_str.split(', ')) if tables_str else 0
        features_ok.append(f"[OK] Datenbank online ({table_count} Tabellen)")
except:
    pass

# Summary
try:
    resp = httpx.get(f"{BASE_URL}/summary", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        features_ok.append(f"[OK] Summary API ({data.get('kunden', 0)} Kunden, {data.get('touren', 0)} Touren)")
except:
    pass

# Workflow API
try:
    resp = httpx.get(f"{BASE_URL}/api/workflow/status", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        llm_status = data.get('llm_status', 'unknown')
        features_ok.append(f"[OK] Workflow API (LLM: {llm_status})")
except:
    pass

# Test Dashboard
try:
    resp = httpx.get(f"{BASE_URL}/api/tests/status", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        passed = data.get('passed', 0)
        total = data.get('total', 0)
        features_ok.append(f"[OK] Test Dashboard ({passed}/{total} Tests bestanden)")
except:
    pass

# Frontend
try:
    resp = httpx.get(f"{BASE_URL}/", timeout=5)
    if resp.status_code == 200:
        features_ok.append("[OK] Frontend erreichbar")
except:
    pass

# API Docs
try:
    resp = httpx.get(f"{BASE_URL}/docs", timeout=5)
    if resp.status_code == 200:
        features_ok.append("[OK] API Dokumentation (Swagger)")
except:
    pass

for feature in features_ok:
    print(f"  {feature}")

# Probleme
print("\n[WARN] PROBLEME:")
problems = []

# Address Recognition
try:
    resp = httpx.get(f"{BASE_URL}/api/address-recognition/status", timeout=5)
    if resp.status_code == 404:
        problems.append("[WARN] Address Recognition API gibt 404 (Router möglicherweise nicht geladen)")
except Exception as e:
    problems.append(f"[WARN] Address Recognition API: {e}")

if not problems:
    problems.append("Keine bekannten Probleme")

for problem in problems:
    print(f"  {problem}")

# System-Info
print("\n[INFO] SYSTEM-INFORMATIONEN:")
print(f"  Server URL: {BASE_URL}")
print(f"  Frontend: {BASE_URL}")
print(f"  API Docs: {BASE_URL}/docs")
print(f"  Health Check: {BASE_URL}/health")
print(f"  Database: {BASE_URL}/health/db")

# LLM + OSRM Status
print("\n[INFO] LLM + OSRM INTEGRATION:")
try:
    from services.llm_optimizer import LLMOptimizer
    optimizer = LLMOptimizer()
    
    llm_status = "[OK] Aktiv" if optimizer.enabled else "[WARN] Deaktiviert"
    print(f"  LLM: {llm_status} ({optimizer.model if optimizer.enabled else 'kein API-Key'})")
    
    osrm_status = "[OK] Konfiguriert" if optimizer.osrm_base else "[WARN] Nicht konfiguriert"
    print(f"  OSRM: {osrm_status} ({optimizer.osrm_base if optimizer.osrm_base else 'OSRM_BASE_URL nicht gesetzt'})")
    
    if optimizer.enabled and optimizer.osrm_base:
        print(f"  Integration: [OK] LLM + OSRM verbunden")
    elif optimizer.enabled:
        print(f"  Integration: [WARN] LLM aktiv, aber OSRM nicht konfiguriert")
    else:
        print(f"  Integration: [WARN] LLM deaktiviert")
except Exception as e:
    print(f"  Status: [FEHLER] {e}")

print("\n" + "=" * 70)
print("NACHSTE SCHRITTE:")
print("  1. App im Browser offnen: http://127.0.0.1:8111")
print("  2. API Dokumentation: http://127.0.0.1:8111/docs")
print("  3. Test Dashboard: http://127.0.0.1:8111/ui/test-dashboard")
print("  4. Falls Address Recognition 404: Server neu starten (Reload)")
print("=" * 70)
