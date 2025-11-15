# Live-Daten API-Recherche & Integration

**Erstellt:** 2025-01-10  
**Zweck:** Konkrete Anleitung für echte API-Integrationen

---

## 📍 Wo suchen? - Konkrete Quellen

### 1. Autobahn-Baustellen & Verkehrsinfo

#### Option A: Autobahn GmbH des Bundes
**URL:** https://www.autobahn.de/
**Kontakt:** 
- E-Mail: info@autobahn.de
- Telefon: 030 40369-0
**Was fragen:**
- Gibt es eine öffentliche API für Baustellen-Daten?
- Welche Datenformate werden unterstützt (JSON, XML)?
- Gibt es Rate-Limits oder Kosten?
- Benötigt man einen API-Key?

**Aktueller Stand:** Keine öffentliche API bekannt, aber direkter Kontakt könnte helfen.

---

#### Option B: ADAC Verkehrsinfo
**URL:** https://www.adac.de/verkehr/verkehrsinfo/
**Kontakt:**
- E-Mail: verkehrsinfo@adac.de
- Telefon: 089 7676-0
**Was fragen:**
- Gibt es eine API für Verkehrsinformationen?
- Partnerschaftsmöglichkeiten für kommerzielle Nutzung?
- Datenformate und Zugangsbedingungen?

**Aktueller Stand:** ADAC bietet Verkehrsinfo an, aber API-Zugang unklar.

---

#### Option C: Mobileye Live Traffic
**URL:** https://www.mobileye.com/
**Dokumentation:** https://static.mobileye.com/website/en/data/files/Mobileye-Live-Traffic-DE.pdf
**Was bietet es:**
- Echtzeit-Verkehrsflussdaten
- Baustellen-Informationen
- Verkehrsereignisse
**Kontakt:**
- E-Mail: info@mobileye.com
- API-Zugang: Muss angefragt werden

**Aktueller Stand:** Bietet Echtzeit-Daten, aber kommerzielle Nutzung muss geklärt werden.

---

#### Option D: OpenStreetMap Overpass API (Bereits implementiert)
**URL:** https://overpass-api.de/
**Status:** ✅ **BEREITS IMPLEMENTIERT**
**Datei:** `backend/services/live_traffic_data.py:183-229`
**Was es bietet:**
- Straßensperrungen (construction=yes, access=no)
- Kostenlos und öffentlich
- Keine API-Key nötig

**Verbesserungen möglich:**
- Erweiterte Queries für mehr Datentypen
- Baustellen-Tags (construction:type, construction:date)
- Temporäre Sperrungen (temporary=yes)

---

### 2. Blitzer/Radar-Daten

#### Option A: Blitzer.de (Direkter Kontakt)
**URL:** https://www.blitzer.de/
**Kontakt:**
- E-Mail: info@blitzer.de
- Telefon: Auf Website finden
**Was fragen:**
- Gibt es eine Partnerschaftsmöglichkeit?
- API-Zugang für kommerzielle Nutzung?
- Nutzungsbedingungen und Kosten?
- Rechtliche Aspekte klären

**Aktueller Stand:** Keine öffentliche API, aber direkter Kontakt könnte helfen.

**WICHTIGER RECHTLICHER HINWEIS:**
- Blitzer.de Nutzungsbedingungen verbieten kommerzielle Nutzung ohne Genehmigung
- Bitte rechtliche Aspekte vor Integration prüfen

---

#### Option B: SCDB.info (Alternative)
**URL:** https://www.scdb.info/
**Was es bietet:**
- Nutzt Datenbasis von Blitzer.de und atudo
- Häufig genutzte mobile Blitzerstandorte
- Als zusätzliche Warnhinweise
**Kontakt:**
- E-Mail: Auf Website finden
- API-Zugang: Muss angefragt werden

**Aktueller Stand:** Alternative Datenquelle, aber auch hier rechtliche Prüfung nötig.

---

#### Option C: Eigene Datenbank (Aktuell implementiert)
**Status:** ✅ **BEREITS IMPLEMENTIERT**
**Datei:** `backend/services/live_traffic_data.py:470-542`
**Was es bietet:**
- Manuelle Datenerfassung
- Import via API-Endpunkte
- Vollständige Kontrolle
- Keine rechtlichen Probleme

**Nächste Schritte:**
- GPX-Import implementieren
- CSV-Import für Bulk-Daten
- Community-Daten sammeln

---

### 3. Unfälle & Staus

#### Option A: Google Maps Traffic API
**URL:** https://developers.google.com/maps/documentation/traffic
**Was es bietet:**
- Echtzeit-Verkehrsdaten
- Unfälle
- Staus
- Baustellen
**Kosten:**
- Kostenpflichtig (Pay-as-you-go)
- Ab 200$ pro Monat
**API-Key:**
- Benötigt Google Cloud Account
- API-Key registrieren

**Aktueller Stand:** Kommerziell verfügbar, aber kostenpflichtig.

---

#### Option B: TomTom Traffic API
**URL:** https://developer.tomtom.com/traffic-api
**Was es bietet:**
- Echtzeit-Verkehrsdaten
- Unfälle
- Baustellen
- Staus
**Kosten:**
- Kostenpflichtig
- Verschiedene Pricing-Tiers
**API-Key:**
- Benötigt TomTom Developer Account

**Aktueller Stand:** Kommerziell verfügbar, aber kostenpflichtig.

---

#### Option C: HERE Traffic API
**URL:** https://developer.here.com/products/traffic
**Was es bietet:**
- Echtzeit-Verkehrsdaten
- Unfälle
- Baustellen
**Kosten:**
- Kostenpflichtig
- Free Tier verfügbar (begrenzt)
**API-Key:**
- Benötigt HERE Developer Account

**Aktueller Stand:** Kommerziell verfügbar, Free Tier für Tests.

---

## 🔧 Implementierungs-Schritte

### Schritt 1: API-Recherche & Kontaktaufnahme

1. **Autobahn-Baustellen:**
   - [ ] Kontakt mit Autobahn GmbH aufnehmen
   - [ ] ADAC Verkehrsinfo anfragen
   - [ ] Mobileye Live Traffic prüfen
   - [ ] OSM Overpass erweitern (bereits vorhanden)

2. **Blitzer-Daten:**
   - [ ] Blitzer.de kontaktieren (Partnerschaft)
   - [ ] SCDB.info prüfen
   - [ ] Rechtliche Aspekte klären
   - [ ] Eigene Datenbank erweitern (GPX-Import)

3. **Unfälle & Staus:**
   - [ ] Google Maps Traffic API prüfen (kostenpflichtig)
   - [ ] TomTom Traffic API prüfen (kostenpflichtig)
   - [ ] HERE Traffic API prüfen (Free Tier verfügbar)

---

### Schritt 2: API-Integration implementieren

**Datei:** `backend/services/live_traffic_data.py`

#### Für Autobahn-Baustellen:

```python
def _fetch_autobahn_construction(self, bounds: Tuple[float, float, float, float]) -> List[TrafficIncident]:
    """
    Holt Baustellen von der Autobahn API.
    
    TODO: Ersetze Mock-Daten mit echter API-Integration
    """
    incidents = []
    min_lat, min_lon, max_lat, max_lon = bounds
    
    # Option 1: Autobahn GmbH API (wenn verfügbar)
    try:
        api_key = os.environ.get("AUTOBAHN_API_KEY")
        if not api_key:
            self.logger.warning("AUTOBAHN_API_KEY nicht gesetzt")
            return []
        
        url = "https://api.autobahn.de/v1/construction"  # Beispiel-URL
        params = {
            "bounds": f"{min_lat},{min_lon},{max_lat},{max_lon}",
            "api_key": api_key
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("constructions", []):
                incidents.append(TrafficIncident(
                    incident_id=f"autobahn_{item['id']}",
                    type="construction",
                    lat=item["lat"],
                    lon=item["lon"],
                    severity=self._map_severity(item.get("severity")),
                    description=item.get("description", ""),
                    delay_minutes=item.get("delay_minutes", 0),
                    radius_km=item.get("radius_km", 2.0),
                    affected_roads=[item.get("road", "")]
                ))
    except Exception as e:
        self.logger.error(f"Autobahn API Fehler: {e}")
    
    return incidents
```

**Wo implementieren:**
- Zeile 163-181 in `backend/services/live_traffic_data.py`
- Ersetze Mock-Daten mit echter API-Integration

---

#### Für Blitzer-Daten:

**Aktuell:** Eigene Datenbank (bereits implementiert)

**Erweiterungen:**
1. **GPX-Import** implementieren
2. **CSV-Import** für Bulk-Daten
3. **Community-Daten** sammeln

**Datei:** `routes/live_traffic_api.py`
- Neuer Endpoint: `POST /api/traffic/cameras/import/gpx`
- Neuer Endpoint: `POST /api/traffic/cameras/import/csv`

---

### Schritt 3: Konfiguration

**Datei:** `config/app.yaml`

```yaml
live_traffic:
  enabled: true
  sources:
    autobahn_api:
      enabled: false  # Auf true setzen wenn API-Key vorhanden
      api_key: ""  # Aus Umgebungsvariable: AUTOBAHN_API_KEY
      base_url: "https://api.autobahn.de/v1"
    osm_overpass:
      enabled: true  # Bereits aktiv
      base_url: "https://overpass-api.de/api/interpreter"
    google_traffic:
      enabled: false  # Optional, kostenpflichtig
      api_key: ""  # Aus Umgebungsvariable: GOOGLE_MAPS_API_KEY
    here_traffic:
      enabled: false  # Optional, Free Tier verfügbar
      api_key: ""  # Aus Umgebungsvariable: HERE_API_KEY
  cache_duration_minutes: 15
  camera_cache_duration_minutes: 60
```

---

### Schritt 4: Umgebungsvariablen

**Datei:** `.env` (oder System-Umgebungsvariablen)

```bash
# Autobahn API (wenn verfügbar)
AUTOBAHN_API_KEY=your_api_key_here

# Google Maps Traffic API (optional, kostenpflichtig)
GOOGLE_MAPS_API_KEY=your_api_key_here

# HERE Traffic API (optional, Free Tier)
HERE_API_KEY=your_api_key_here

# TomTom Traffic API (optional, kostenpflichtig)
TOMTOM_API_KEY=your_api_key_here
```

---

## 📋 Konkrete To-Do-Liste

### Diese Woche:

1. **Kontaktaufnahme:**
   - [ ] Autobahn GmbH kontaktieren (info@autobahn.de)
   - [ ] ADAC Verkehrsinfo anfragen (verkehrsinfo@adac.de)
   - [ ] Blitzer.de kontaktieren (info@blitzer.de)
   - [ ] Mobileye Live Traffic prüfen

2. **API-Dokumentation prüfen:**
   - [ ] HERE Traffic API (Free Tier) - https://developer.here.com/products/traffic
   - [ ] Google Maps Traffic API - https://developers.google.com/maps/documentation/traffic
   - [ ] TomTom Traffic API - https://developer.tomtom.com/traffic-api

3. **OSM Overpass erweitern:**
   - [ ] Erweiterte Queries für Baustellen
   - [ ] Temporäre Sperrungen
   - [ ] Baustellen-Details (Typ, Datum)

### Nächste Woche:

4. **API-Integration implementieren:**
   - [ ] Autobahn API (wenn verfügbar)
   - [ ] HERE Traffic API (Free Tier testen)
   - [ ] OSM Overpass erweitern

5. **GPX-Import für Blitzer:**
   - [ ] GPX-Parser implementieren
   - [ ] Import-Endpoint erstellen
   - [ ] Validierung und Duplikatsprüfung

---

## 🔍 Wo genau suchen?

### 1. Autobahn-Baustellen:

**Websites:**
- https://www.autobahn.de/ (Autobahn GmbH)
- https://www.adac.de/verkehr/verkehrsinfo/ (ADAC)
- https://www.mobileye.com/ (Mobileye)

**Suchbegriffe:**
- "Autobahn Baustellen API"
- "Germany highway construction API"
- "ADAC Verkehrsinfo API"
- "Mobileye Live Traffic API"

**Kontakte:**
- Autobahn GmbH: info@autobahn.de
- ADAC: verkehrsinfo@adac.de
- Mobileye: info@mobileye.com

---

### 2. Blitzer-Daten:

**Websites:**
- https://www.blitzer.de/ (Hauptquelle, aber keine API)
- https://www.scdb.info/ (Alternative)

**Suchbegriffe:**
- "Blitzer API Deutschland"
- "Speed camera API Germany"
- "Radar API legal"
- "SCDB.info API"

**Kontakte:**
- Blitzer.de: info@blitzer.de
- SCDB.info: Auf Website finden

---

### 3. Unfälle & Staus:

**Websites:**
- https://developer.here.com/products/traffic (HERE - Free Tier)
- https://developers.google.com/maps/documentation/traffic (Google - kostenpflichtig)
- https://developer.tomtom.com/traffic-api (TomTom - kostenpflichtig)

**Suchbegriffe:**
- "Traffic API Germany"
- "Real-time traffic API"
- "Accident API Germany"
- "HERE Traffic API free"

---

## ⚠️ Wichtige Hinweise

1. **Rechtliche Aspekte:**
   - Blitzer-Daten: Rechtliche Prüfung nötig
   - Nutzungsbedingungen der APIs prüfen
   - Datenschutz beachten

2. **Kosten:**
   - Google Maps: Kostenpflichtig (ab 200$/Monat)
   - TomTom: Kostenpflichtig
   - HERE: Free Tier verfügbar
   - OSM: Kostenlos

3. **Rate-Limits:**
   - Alle APIs haben Rate-Limits
   - Caching ist wichtig (bereits implementiert: 15 Min)

4. **Fallback-Strategie:**
   - Immer Fallback auf eigene Datenbank
   - OSM Overpass als kostenlose Alternative
   - Graceful Degradation bei API-Fehlern

---

## 🎯 Empfohlene Reihenfolge

1. **Sofort (kostenlos):**
   - OSM Overpass erweitern (bereits vorhanden)
   - Eigene Datenbank nutzen (bereits vorhanden)

2. **Kurzfristig (Free Tier):**
   - HERE Traffic API testen (Free Tier)
   - Kontaktaufnahme mit Autobahn GmbH

3. **Mittelfristig (kostenpflichtig):**
   - Google Maps Traffic API (wenn Budget vorhanden)
   - TomTom Traffic API (wenn Budget vorhanden)

4. **Langfristig:**
   - Blitzer.de Partnerschaft (rechtliche Klärung)
   - Eigene Community-Daten sammeln

---

**Stand:** 2025-01-10  
**Nächste Aktualisierung:** Nach Kontaktaufnahme mit APIs

