#!/usr/bin/env python3
"""
Test der Server-Integration für Dreihundert Dresden
"""
import requests
import json

def test_server_integration():
    """Test: Prüfe ob der Server die Normalisierung verwendet"""
    print("🧪 Teste Server-Integration für Dreihundert Dresden...")
    
    try:
        # API-Call an den Server
        url = "http://localhost:8111/api/tourplan/match"
        params = {"file": "tourplaene/Tourenplan 06.10.2025.csv"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Suche nach Dreihundert Dresden
        dreihundert = [item for item in data['items'] if 'Dreihundert' in item.get('customer_name', '')]
        
        print(f"📊 Dreihundert Dresden gefunden: {len(dreihundert)}")
        print(f"📊 Gesamt Kunden: {data.get('rows', 0)}")
        print(f"📊 OK: {data.get('ok', 0)}, Warn: {data.get('warn', 0)}, Bad: {data.get('bad', 0)}")
        
        for i, item in enumerate(dreihundert[:3]):
            name = item.get('customer_name', 'UNBEKANNT')
            address = item.get('address', 'KEINE ADRESSE')
            has_pipe = '|' in address
            
            print(f"  {i+1}. {name}")
            print(f"     Address: {address}")
            print(f"     Pipe in Address: {has_pipe}")
            print()
        
        # Prüfe alle Adressen auf Pipes
        pipe_addresses = [item for item in data['items'] if '|' in item.get('address', '')]
        print(f"⚠️ Kunden mit Pipe in Adresse: {len(pipe_addresses)}")
        
        if len(pipe_addresses) > 0:
            print("❌ PROBLEM: Es gibt noch Adressen mit Pipe-Zeichen!")
            for item in pipe_addresses[:3]:
                print(f"  - {item.get('customer_name', 'UNBEKANNT')}: {item.get('address', '')}")
        else:
            print("✅ ERFOLG: Alle Adressen sind normalisiert!")
            
        return len(pipe_addresses) == 0
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        return False

if __name__ == "__main__":
    success = test_server_integration()
    print(f"\n🎯 Server-Test {'erfolgreich' if success else 'fehlgeschlagen'}!")
