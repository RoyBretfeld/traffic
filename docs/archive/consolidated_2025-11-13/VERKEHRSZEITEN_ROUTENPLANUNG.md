# Verkehrszeiten-basierte Routenplanung

## Übersicht

**Ziel:** Routenplanung berücksichtigt Verkehrszeiten → Unterschiedliche Routen je nach Uhrzeit.

**Beispiel:**
- **Sonntag 10:00 Uhr:** Wenig Verkehr → Direktere Route möglich
- **Montag 8:00 Uhr:** Berufsverkehr → Alternative Route, die Staus umgeht
- **Montag 17:00 Uhr:** Feierabendverkehr → Wieder andere Route

---

## Verkehrszeiten-Kategorien

### 1. Sonntag / Feiertage
- **Verkehr:** Minimal
- **Routen:** Direkt, kürzeste Strecke
- **Fahrzeit:** Basis-Zeit × 1.0

### 2. Normalverkehr (Mo-Fr, 10-15 Uhr)
- **Verkehr:** Normal
- **Routen:** Standard-Routen
- **Fahrzeit:** Basis-Zeit × 1.1

### 3. Morgenverkehr (Mo-Fr, 6-9 Uhr)
- **Verkehr:** Hohes Aufkommen (Arbeitsweg)
- **Routen:** Stau-Umfahrungen
- **Fahrzeit:** Basis-Zeit × 1.3-1.5

### 4. Nachmittagsverkehr (Mo-Fr, 15-16 Uhr)
- **Verkehr:** Erhöht (Schulschluss)
- **Routen:** Schulgebiete meiden wenn möglich
- **Fahrzeit:** Basis-Zeit × 1.2

### 5. Feierabendverkehr (Mo-Fr, 17-19 Uhr)
- **Verkehr:** Sehr hoch (Rush Hour)
- **Routen:** Umfahrungen, Hauptstraßen meiden
- **Fahrzeit:** Basis-Zeit × 1.4-1.6

---

## Implementierung

### Schritt 1: Verkehrszeit-Erkennung

**Datei:** `services/traffic_time_service.py` (neu)

```python
from datetime import datetime, time
from typing import Dict, Tuple

class TrafficTimeService:
    """Erkennt aktuelle Verkehrszeit und liefert Multiplikator"""
    
    def get_traffic_multiplier(self, tour_time: datetime) -> float:
        """
        Gibt Multiplikator für Fahrzeit basierend auf Verkehrszeit zurück
        
        Returns:
            1.0 = Sonntag/Minimal
            1.1 = Normal
            1.3 = Morgenverkehr
            1.2 = Nachmittags
            1.5 = Feierabend
        """
        weekday = tour_time.weekday()  # 0=Montag, 6=Sonntag
        hour = tour_time.hour
        
        # Sonntag
        if weekday == 6:
            return 1.0
        
        # Wochentage
        if 6 <= hour < 9:  # Morgenverkehr
            return 1.4
        elif 15 <= hour < 16:  # Nachmittags
            return 1.2
        elif 17 <= hour < 19:  # Feierabend
            return 1.5
        else:  # Normal
            return 1.1
```

---

### Schritt 2: In Routenoptimierung einbauen

**Datei:** `routes/workflow_api.py` → `optimize_tour_with_ai()`

```python
from services.traffic_time_service import TrafficTimeService

traffic_service = TrafficTimeService()

# Tour-Zeit aus Request (z.B. "W-07.00" → 07:00 Uhr)
tour_time = parse_tour_time(tour_id)  # z.B. datetime(2025, 11, 2, 7, 0)

# Verkehrs-Multiplikator
traffic_multiplier = traffic_service.get_traffic_multiplier(tour_time)

# In LLM-Prompt:
prompt += f"\nWICHTIG: Aktuelle Zeit ist {tour_time.strftime('%H:%M')} am {tour_time.strftime('%A')}"
prompt += f"\nVerkehrslage: {'Rush Hour' if traffic_multiplier > 1.3 else 'Normal'}"
prompt += f"\nBerücksichtige Staus und wähle Routen die Staus umgehen."

# In Zeitberechnung:
driving_time = _calculate_tour_time(optimized_stops) * traffic_multiplier
```

---

### Schritt 3: OSRM mit Verkehrsdaten

**OSRM unterstützt Verkehrsdaten über externe Services:**

```python
# OSRM Route API mit Verkehrsdaten
url = f"{osrm_base}/route/v1/{profile}/{coordinates}"
params = {
    "overview": "full",
    "geometries": "geojson",
    "steps": "true",
    # Verkehrsdaten (falls verfügbar)
    "alternatives": "true"  # Alternative Routen wenn Staus
}

response = requests.get(url, params=params)
```

**Alternative:** Google Maps / TomTom Traffic API (kostenpflichtig)

---

### Schritt 4: UI-Anzeige

**Frontend:** `frontend/index.html`

```javascript
// Zeige Verkehrslage für Tour
function getTrafficStatus(tourTime) {
    const hour = new Date(tourTime).getHours();
    const weekday = new Date(tourTime).getDay();
    
    if (weekday === 0) return "Minimal (Sonntag)";
    if (hour >= 6 && hour < 9) return "Morgenverkehr ⚠️";
    if (hour >= 17 && hour < 19) return "Feierabendverkehr ⚠️⚠️";
    return "Normal";
}

// In Tour-Card anzeigen
<div class="traffic-status">
    Verkehr: {getTrafficStatus(tour.time)}
</div>
```

---

## Beispiel: W-07.00 Uhr Tour

### Sonntag 07:00 Uhr
```
Verkehr: Minimal
Fahrzeit-Multiplikator: 1.0
Route: Direkt, kürzeste Strecke
Gesamtzeit: 58 Min
```

### Montag 07:00 Uhr
```
Verkehr: Morgenverkehr ⚠️
Fahrzeit-Multiplikator: 1.4
Route: Umfährt Hauptstraßen, nutzt Nebenstraßen
Gesamtzeit: 58 × 1.4 = 81 Min → Über 60! → Muss gesplittet werden
```

### Montag 17:00 Uhr
```
Verkehr: Feierabendverkehr ⚠️⚠️
Fahrzeit-Multiplikator: 1.5
Route: Stau-Umfahrungen, alternative Routen
Gesamtzeit: 58 × 1.5 = 87 Min → Über 60! → Muss gesplittet werden
```

---

## Datenquellen für Verkehrsdaten

### Option 1: OSRM (kostenlos)
- Basis-Routing
- Keine Live-Verkehrsdaten
- Alternative Routen möglich

### Option 2: Google Maps Traffic API (kostenpflichtig)
- Live-Verkehrsdaten
- Stau-Informationen
- $5-10 pro 1000 Requests

### Option 3: TomTom Traffic API (kostenpflichtig)
- Live-Verkehrsdaten
- Gute Abdeckung in Deutschland
- $5-15 pro 1000 Requests

### Option 4: Historische Daten (kostenlos)
- Durchschnittliche Verkehrszeiten basierend auf Wochentag/Uhrzeit
- Keine Live-Daten, aber gute Schätzung
- Implementierung: Multiplikator-Tabelle

---

## Implementierungs-Plan

### Phase 1: Historische Verkehrsdaten (Morgen möglich)
- [ ] `TrafficTimeService` erstellen
- [ ] Multiplikator-Tabelle implementieren
- [ ] In Zeitberechnung einbauen
- [ ] UI-Anzeige für Verkehrslage

### Phase 2: OSRM-Integration (Nächste Woche)
- [ ] OSRM-Route API integrieren
- [ ] Alternative Routen bei Staus
- [ ] Verkehrszeiten in OSRM-Requests

### Phase 3: Live-Verkehrsdaten (Später)
- [ ] Google Maps / TomTom API evaluieren
- [ ] Kosten vs. Nutzen analysieren
- [ ] Implementierung wenn sinnvoll

---

## Konfiguration

**Umgebungsvariablen:**
```bash
# .env
TRAFFIC_DATA_ENABLED=true
TRAFFIC_DATA_PROVIDER=historical  # historical, osrm, google, tomtom
GOOGLE_MAPS_API_KEY=...  # Falls Google verwendet wird
```

---

## Vorteile

✅ **Realistische Zeitberechnung:** Berücksichtigt tatsächlichen Verkehr  
✅ **Bessere Optimierung:** KI wählt Routen die Staus umgehen  
✅ **Warnungen:** Benutzer sieht wenn Verkehrslage kritisch ist  
✅ **Professionell:** Wie kommerzielle Navigation-Apps  

---

**Status:** 📋 Geplant - Historische Verkehrsdaten können morgen implementiert werden, Live-Daten später.

