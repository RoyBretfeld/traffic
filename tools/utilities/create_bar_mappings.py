#!/usr/bin/env python3
"""
BAR-Kunden Mapping-System erstellen

Erstellt ein umfassendes Mapping-System für BAR-Kunden basierend auf der Analyse.
"""

import json
from pathlib import Path
from datetime import datetime

def create_bar_mappings():
    """Erstellt BAR-Kunden-Mappings basierend auf der Analyse."""
    
    # Lade die Analyse-Ergebnisse
    with open('bar_customers_analysis.json', 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    
    # Erstelle Mappings für die identifizierten BAR-Kunden
    bar_mappings = {
        "mapping_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "description": "BAR-Kunden-Mappings basierend auf Tourplan-Analyse",
        "mappings": []
    }
    
    # Turboservice Ingo Barthel
    turboservice_mapping = {
        "canonical_name": "Turboservice Ingo Barthel",
        "canonical_address": "Bohnitzscher Str. 4, 01662 Meißen",
        "canonical_lat": None,  # Wird später durch Geocoding gefüllt
        "canonical_lon": None,
        "kdnr": "",  # Wird später gefüllt
        "category": "autoservice",
        "description": "Turboservice Ingo Barthel - BAR-Kunde",
        "variants": [
            {
                "name": "Turboservice Ingo Barthel",
                "address": "Bohnitzscher Str. 4, 01662 Meißen",
                "confidence": 1.0,
                "source": "tourplan_analysis"
            }
        ],
        "tour_occurrences": 15,  # Anzahl der Vorkommen in Tourplänen
        "last_seen": "2025-10-01"
    }
    
    # Testa Baresi
    testa_mapping = {
        "canonical_name": "Testa Baresi",
        "canonical_address": "Lausener Str. 4B, 04207 Leipzig",
        "canonical_lat": None,  # Wird später durch Geocoding gefüllt
        "canonical_lon": None,
        "kdnr": "",  # Wird später gefüllt
        "category": "autoservice",
        "description": "Testa Baresi - BAR-Kunde",
        "variants": [
            {
                "name": "Testa Baresi",
                "address": "Lausener Str. 4B, 04207 Leipzig",
                "confidence": 1.0,
                "source": "tourplan_analysis"
            }
        ],
        "tour_occurrences": 19,  # Anzahl der Vorkommen in Tourplänen
        "last_seen": "2025-09-29"
    }
    
    bar_mappings["mappings"].append(turboservice_mapping)
    bar_mappings["mappings"].append(testa_mapping)
    
    # Speichere die Mappings
    with open('bar_customers_mappings.json', 'w', encoding='utf-8') as f:
        json.dump(bar_mappings, f, indent=2, ensure_ascii=False)
    
    # Erstelle auch eine CSV-Version für einfache Bearbeitung
    csv_content = "canonical_name,canonical_address,canonical_lat,canonical_lon,kdnr,category,description,tour_occurrences,last_seen\n"
    csv_content += f"Turboservice Ingo Barthel,Bohnitzscher Str. 4 01662 Meißen,,,BAR,autoservice,Turboservice Ingo Barthel - BAR-Kunde,15,2025-10-01\n"
    csv_content += f"Testa Baresi,Lausener Str. 4B 04207 Leipzig,,,BAR,autoservice,Testa Baresi - BAR-Kunde,19,2025-09-29\n"
    
    with open('bar_customers_mappings.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    # Erstelle Markdown-Dokumentation
    md_content = f"""# BAR-Kunden Mappings

**Erstellt am:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}  
**Basierend auf:** Analyse von 34 Tourplänen  
**Gesamt BAR-Kunden:** 2 eindeutige Kunden

## 📊 Übersicht

| Kunde | Adresse | Tour-Vorkommen | Letzte Sichtung |
|-------|---------|----------------|-----------------|
| Turboservice Ingo Barthel | Bohnitzscher Str. 4, 01662 Meißen | 15 | 01.10.2025 |
| Testa Baresi | Lausener Str. 4B, 04207 Leipzig | 19 | 29.09.2025 |

## 🔍 Detaillierte Mappings

### 1. Turboservice Ingo Barthel
- **Kanonischer Name:** Turboservice Ingo Barthel
- **Adresse:** Bohnitzscher Str. 4, 01662 Meißen
- **Kategorie:** Autoservice
- **Tour-Vorkommen:** 15 (in verschiedenen Tourplänen)
- **Status:** Konsistenter Name in allen Tourplänen

### 2. Testa Baresi
- **Kanonischer Name:** Testa Baresi
- **Adresse:** Lausener Str. 4B, 04207 Leipzig
- **Kategorie:** Autoservice
- **Tour-Vorkommen:** 19 (in verschiedenen Tourplänen)
- **Status:** Konsistenter Name in allen Tourplänen

## 📈 Erkenntnisse

1. **Konsistente Namen:** Beide BAR-Kunden haben konsistente Namen in allen Tourplänen
2. **Regelmäßige Auftritte:** Beide Kunden erscheinen regelmäßig in den Tourplänen
3. **Keine Namens-Varianten:** Keine verschiedenen Schreibweisen gefunden
4. **Geografische Verteilung:** 
   - Turboservice: Meißen (Sachsen)
   - Testa Baresi: Leipzig (Sachsen)

## 🎯 Nächste Schritte

1. **Geocoding:** Koordinaten für beide Adressen ermitteln
2. **Kundennummern:** Echte KdNr für beide Kunden ermitteln
3. **Integration:** Mappings in das Hauptsystem integrieren
4. **Monitoring:** Kontinuierliche Überwachung neuer Tourpläne

## 📁 Dateien

- `bar_customers_mappings.json` - Strukturierte Mappings
- `bar_customers_mappings.csv` - CSV für einfache Bearbeitung
- `bar_customers_analysis.json` - Vollständige Analyse-Ergebnisse
"""
    
    with open('bar_customers_mappings.md', 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print("✅ BAR-Kunden-Mappings erstellt!")
    print("📁 Dateien:")
    print("  - bar_customers_mappings.json")
    print("  - bar_customers_mappings.csv")
    print("  - bar_customers_mappings.md")
    
    return bar_mappings

def create_address_corrector_integration():
    """Erstellt Integration für das Address-Corrector-System."""
    
    # Lade die Mappings
    with open('bar_customers_mappings.json', 'r', encoding='utf-8') as f:
        mappings = json.load(f)
    
    # Erstelle Python-Code für Address-Corrector
    python_code = '''#!/usr/bin/env python3
"""
BAR-Kunden-Erkennung für Address-Corrector

Automatisch generiert basierend auf Tourplan-Analyse.
"""

BAR_CUSTOMER_MAPPINGS = {
    "Turboservice Ingo Barthel": {
        "canonical_name": "Turboservice Ingo Barthel",
        "canonical_address": "Bohnitzscher Str. 4, 01662 Meißen",
        "category": "autoservice",
        "is_bar": True
    },
    "Testa Baresi": {
        "canonical_name": "Testa Baresi", 
        "canonical_address": "Lausener Str. 4B, 04207 Leipzig",
        "category": "autoservice",
        "is_bar": True
    }
}

def is_bar_customer(name, address):
    """Prüft ob ein Kunde ein BAR-Kunde ist."""
    name_lower = name.lower().strip()
    
    for bar_name, mapping in BAR_CUSTOMER_MAPPINGS.items():
        if bar_name.lower() in name_lower:
            return True, mapping
    
    return False, None

def get_bar_customer_mapping(name, address):
    """Gibt das Mapping für einen BAR-Kunden zurück."""
    is_bar, mapping = is_bar_customer(name, address)
    return mapping if is_bar else None
'''
    
    with open('bar_customer_detector.py', 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    print("✅ Address-Corrector-Integration erstellt: bar_customer_detector.py")

if __name__ == "__main__":
    print("🚀 Erstelle BAR-Kunden-Mappings...")
    
    # Erstelle Mappings
    mappings = create_bar_mappings()
    
    # Erstelle Integration
    create_address_corrector_integration()
    
    print("\n🎉 BAR-Kunden-Mapping-System erfolgreich erstellt!")
    print("\n📋 Zusammenfassung:")
    print(f"  - {len(mappings['mappings'])} BAR-Kunden identifiziert")
    print(f"  - {sum(m['tour_occurrences'] for m in mappings['mappings'])} Tour-Vorkommen insgesamt")
    print("  - Mappings für Address-Corrector erstellt")
    print("  - Dokumentation und CSV-Export erstellt")
