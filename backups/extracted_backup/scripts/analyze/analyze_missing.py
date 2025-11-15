#!/usr/bin/env python3
"""
Einfaches Tool zur Behebung der fehlenden Adressen
"""
import json
import requests
import re

def load_and_analyze():
    """Lädt und analysiert die fehlenden Adressen"""
    try:
        with open('config/recognition_rate_analysis.json', 'r', encoding='latin-1') as f:
            data = json.load(f)
    except:
        print("Fehler beim Laden der Datei")
        return
    
    missing_addresses = []
    for result in data['results']:
        if 'missing_addresses' in result and result['missing_addresses']:
            for addr in result['missing_addresses']:
                missing_addresses.append(addr)
    
    print(f"🔍 GEFUNDEN: {len(missing_addresses)} fehlende Adressen")
    print("="*80)
    
    # Analysiere Muster
    patterns = {
        "pipe_separated": [],
        "halle_mentions": [],
        "ot_mentions": [],
        "slash_separated": [],
        "other": []
    }
    
    for addr in missing_addresses:
        if "|" in addr:
            patterns["pipe_separated"].append(addr)
        elif "Halle" in addr:
            patterns["halle_mentions"].append(addr)
        elif "OT" in addr:
            patterns["ot_mentions"].append(addr)
        elif "/" in addr:
            patterns["slash_separated"].append(addr)
        else:
            patterns["other"].append(addr)
    
    print("📋 ADRESS-MUSTER:")
    for pattern_name, items in patterns.items():
        if items:
            print(f"  {pattern_name}: {len(items)} Adressen")
    
    # Generiere Fixes
    print("\n🔧 AUTOMATISCHE FIX-VORSCHLÄGE:")
    print("="*80)
    
    fixes = []
    
    # Pipe-Separated: Nach Pipe abschneiden
    for addr in patterns["pipe_separated"]:
        fixed = addr.split("|")[0].strip()
        fixes.append({"original": addr, "fixed": fixed, "method": "remove_pipe"})
    
    # Halle-Erwähnungen: Halle-Teil entfernen
    for addr in patterns["halle_mentions"]:
        fixed = re.sub(r'\s*/\s*Halle\s+\w+', '', addr)
        fixed = re.sub(r'\s*Halle\s+\w+', '', fixed)
        fixed = fixed.strip()
        fixes.append({"original": addr, "fixed": fixed, "method": "remove_halle"})
    
    # OT-Erwähnungen: OT-Teil entfernen
    for addr in patterns["ot_mentions"]:
        fixed = re.sub(r'\s*OT\s+\w+', '', addr)
        fixed = fixed.strip()
        fixes.append({"original": addr, "fixed": fixed, "method": "remove_ot"})
    
    # Slash-Separated: Ersten Teil nehmen
    for addr in patterns["slash_separated"]:
        fixed = addr.split("/")[0].strip()
        fixes.append({"original": addr, "fixed": fixed, "method": "remove_slash"})
    
    # Teste Geocoding
    print(f"\n🧪 TESTE GEOCODING FÜR {len(fixes)} FIXES:")
    print("="*80)
    
    successful = 0
    for i, fix in enumerate(fixes[:10]):  # Teste nur erste 10
        print(f"\n{i+1}. {fix['method'].upper()}:")
        print(f"   Original: {fix['original']}")
        print(f"   Fixed:    {fix['fixed']}")
        
        try:
            response = requests.get("http://localhost:8111/api/geocode", 
                                  params={"address": fix['fixed']}, 
                                  timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ Geocoding erfolgreich!")
                    successful += 1
                else:
                    print(f"   ❌ Geocoding fehlgeschlagen")
            else:
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    print(f"\n📊 ERGEBNIS:")
    print(f"  Getestet: {min(10, len(fixes))}")
    print(f"  Erfolgreich: {successful}")
    print(f"  Erfolgsrate: {successful/min(10, len(fixes))*100:.1f}%")
    
    # Zeige alle Fixes
    print(f"\n📝 ALLE FIX-VORSCHLÄGE:")
    print("="*80)
    for i, fix in enumerate(fixes):
        print(f"{i+1:2d}. [{fix['method']}] {fix['original']} → {fix['fixed']}")
    
    print(f"\n🎯 NÄCHSTE SCHRITTE:")
    print(f"  1. Diese Fixes in address_mappings.json implementieren")
    print(f"  2. Server neu starten")
    print(f"  3. Erkennungsrate erneut prüfen")
    print(f"  4. Ziel: 100% Erkennungsrate")

if __name__ == "__main__":
    load_and_analyze()
