#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt Test-Hindernisse für die Route-Details-API
"""
import sys
from pathlib import Path
import requests
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Beispiel-Hindernisse in Dresden (nahe typischen Routen)
test_incidents = [
    {
        "incident_id": "test_construction_001",
        "type": "construction",
        "lat": 51.0504,  # Nähe Hauptbahnhof
        "lon": 13.7373,
        "severity": "medium",
        "description": "Test-Baustelle: Hauptbahnhof Dresden - rechte Spur gesperrt",
        "delay_minutes": 5,
        "radius_km": 0.3
    },
    {
        "incident_id": "test_closure_001",
        "type": "closure",
        "lat": 51.0522,  # Nähe Altmarkt
        "lon": 13.7380,
        "severity": "high",
        "description": "Test-Sperrung: Altmarkt Dresden - Straße voll gesperrt",
        "delay_minutes": 10,
        "radius_km": 0.5
    },
    {
        "incident_id": "test_accident_001",
        "type": "accident",
        "lat": 51.0489,  # Nähe Prager Straße
        "lon": 13.7412,
        "severity": "critical",
        "description": "Test-Unfall: Prager Straße - Verkehrsbehinderung",
        "delay_minutes": 15,
        "radius_km": 0.2
    }
]

print("="*80)
print("TEST-HINDERNISSE ERSTELLEN")
print("="*80)
print()

base_url = "http://localhost:8111"  # Standard-Port

for incident in test_incidents:
    try:
        response = requests.post(
            f"{base_url}/api/traffic/incidents",
            json=incident,
            timeout=5
        )
        if response.status_code == 200:
            print(f"[OK] {incident['incident_id']}: {incident['description']}")
        else:
            print(f"[FEHLER] {incident['incident_id']}: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"[FEHLER] Server nicht erreichbar auf {base_url}")
        print("  -> Stelle sicher, dass der Server läuft!")
        break
    except Exception as e:
        print(f"[FEHLER] {incident['incident_id']}: {e}")

print()
print("="*80)
print("Fertig! Pruefe mit: python scripts/check_traffic_incidents.py")
print("="*80)

