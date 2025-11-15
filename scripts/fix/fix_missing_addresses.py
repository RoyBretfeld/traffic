#!/usr/bin/env python3
"""
Tool zur Behebung der 88 fehlenden Adressen für 100% Erkennungsrate
Analysiert die recognition_rate_analysis.json und bietet Lösungen
"""
import json
import sys
from pathlib import Path
import requests
from typing import List, Dict, Any

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def load_missing_addresses() -> List[Dict[str, Any]]:
    """Lädt alle fehlenden Adressen aus der Analyse"""
    with open("config/recognition_rate_analysis.json", "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    missing_addresses = []
    for result in data["results"]:
        if "missing_addresses" in result and result["missing_addresses"]:
            for addr in result["missing_addresses"]:
                missing_addresses.append({
                    "file": result["file"],
                    "address": addr,
                    "total_customers": result.get("total_customers", 0),
                    "missing_count": result.get("missing", 0)
                })
    
    return missing_addresses

def analyze_address_patterns(missing_addresses: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Analysiert Muster in den fehlenden Adressen"""
    patterns = {
        "pipe_separated": [],      # Adressen mit | (Pipe)
        "halle_mentions": [],     # Halle-Erwähnungen
        "ot_mentions": [],        # OT (Ortsteil) Erwähnungen
        "slash_separated": [],    # Adressen mit /
        "empty_or_invalid": [],   # Leere oder ungültige Adressen
        "other": []               # Sonstige
    }
    
    for item in missing_addresses:
        addr = item["address"]
        
        if "|" in addr:
            patterns["pipe_separated"].append(item)
        elif "Halle" in addr:
            patterns["halle_mentions"].append(item)
        elif "OT" in addr:
            patterns["ot_mentions"].append(item)
        elif "/" in addr:
            patterns["slash_separated"].append(item)
        elif not addr or addr.strip() == "" or len(addr.strip()) < 5:
            patterns["empty_or_invalid"].append(item)
        else:
            patterns["other"].append(item)
    
    return patterns

def suggest_fixes(patterns: Dict[str, List[str]]) -> Dict[str, List[Dict[str, str]]]:
    """Schlägt automatische Fixes vor"""
    fixes = {}
    
    # Pipe-Separated Adressen: Nach Pipe abschneiden
    fixes["pipe_separated"] = []
    for item in patterns["pipe_separated"]:
        original = item["address"]
        fixed = original.split("|")[0].strip()
        fixes["pipe_separated"].append({
            "original": original,
            "suggested": fixed,
            "file": item["file"],
            "method": "remove_after_pipe"
        })
    
    # Halle-Erwähnungen: Halle-Teil entfernen
    fixes["halle_mentions"] = []
    for item in patterns["halle_mentions"]:
        original = item["address"]
        # Entferne "/ Halle XX" oder "Halle XX" Teile
        import re
        fixed = re.sub(r'\s*/\s*Halle\s+\w+', '', original)
        fixed = re.sub(r'\s*Halle\s+\w+', '', fixed)
        fixed = fixed.strip()
        fixes["halle_mentions"].append({
            "original": original,
            "suggested": fixed,
            "file": item["file"],
            "method": "remove_halle_mention"
        })
    
    # OT-Erwähnungen: OT-Teil entfernen
    fixes["ot_mentions"] = []
    for item in patterns["ot_mentions"]:
        original = item["address"]
        import re
        fixed = re.sub(r'\s*OT\s+\w+', '', original)
        fixed = fixed.strip()
        fixes["ot_mentions"].append({
            "original": original,
            "suggested": fixed,
            "file": item["file"],
            "method": "remove_ot_mention"
        })
    
    # Slash-Separated: Ersten Teil nehmen
    fixes["slash_separated"] = []
    for item in patterns["slash_separated"]:
        original = item["address"]
        fixed = original.split("/")[0].strip()
        fixes["slash_separated"].append({
            "original": original,
            "suggested": fixed,
            "file": item["file"],
            "method": "take_first_part"
        })
    
    return fixes

def test_geocoding(address: str) -> Dict[str, Any]:
    """Testet Geocoding für eine Adresse"""
    try:
        response = requests.get(f"http://localhost:8111/api/geocode", 
                               params={"address": address}, 
                               timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🔍 ANALYSE DER FEHLENDEN ADRESSEN")
    print("="*80)
    
    # Lade fehlende Adressen
    missing_addresses = load_missing_addresses()
    print(f"📊 Gefunden: {len(missing_addresses)} fehlende Adressen")
    
    # Analysiere Muster
    patterns = analyze_address_patterns(missing_addresses)
    
    print("\n📋 ADRESS-MUSTER:")
    for pattern_name, items in patterns.items():
        if items:
            print(f"  {pattern_name}: {len(items)} Adressen")
    
    # Generiere Fix-Vorschläge
    fixes = suggest_fixes(patterns)
    
    print("\n🔧 AUTOMATISCHE FIX-VORSCHLÄGE:")
    print("="*80)
    
    total_fixes = 0
    successful_tests = 0
    
    for fix_type, fix_list in fixes.items():
        if fix_list:
            print(f"\n{fix_type.upper()}:")
            for fix in fix_list:
                print(f"  Original: {fix['original']}")
                print(f"  Vorschlag: {fix['suggested']}")
                print(f"  Datei: {fix['file']}")
                
                # Teste Geocoding
                result = test_geocoding(fix['suggested'])
                if result.get('success'):
                    print(f"  ✅ Geocoding erfolgreich!")
                    successful_tests += 1
                else:
                    print(f"  ❌ Geocoding fehlgeschlagen: {result.get('error', 'Unbekannt')}")
                
                print()
                total_fixes += 1
    
    print(f"\n📊 ZUSAMMENFASSUNG:")
    print(f"  Gesamte Fix-Vorschläge: {total_fixes}")
    print(f"  Erfolgreiche Tests: {successful_tests}")
    print(f"  Erfolgsrate: {successful_tests/total_fixes*100:.1f}%" if total_fixes > 0 else "  Keine Tests")
    
    # Zeige problematische Adressen
    print(f"\n⚠️ PROBLEMATISCHE ADRESSEN:")
    for item in patterns["empty_or_invalid"] + patterns["other"]:
        print(f"  {item['address']} (aus {item['file']})")
    
    print(f"\n🎯 NÄCHSTE SCHRITTE:")
    print(f"  1. Automatische Fixes implementieren")
    print(f"  2. Address-Mappings erweitern")
    print(f"  3. Manuelle Korrekturen für problematische Adressen")
    print(f"  4. Ziel: 100% Erkennungsrate erreichen")

if __name__ == "__main__":
    main()
