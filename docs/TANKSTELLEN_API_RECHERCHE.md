# Tankstellen-API Recherche & Integration

**Erstellt:** 2025-11-22  
**Zweck:** Recherche und Integration von Tankstellen-APIs für aktuelle Preise

---

## 🚗 Verfügbare Tankstellen-APIs

### 1. Tankerkönig API (Empfohlen) ⭐

**URL:** https://creativecommons.tankerkoenig.de/  
**Status:** ✅ **KOSTENLOS** (Creative Commons Lizenz)  
**Dokumentation:** https://creativecommons.tankerkoenig.de/

**Was es bietet:**
- Aktuelle Spritpreise (Diesel, Super, E10, E5)
- Alle Tankstellen in Deutschland (MTS-K Daten)
- Standort-basierte Suche (Radius)
- Echtzeit-Preise (alle 5 Minuten aktualisiert)
- **Enthält auch Aral-Tankstellen!**

**API-Endpunkte:**
- `GET /stations/v1/search` - Suche nach Tankstellen
- `GET /stations/v1/detail` - Details einer Tankstelle
- `GET /prices/v1/prices` - Aktuelle Preise

**Beispiel:**
```json
GET https://creativecommons.tankerkoenig.de/json/list.php?lat=51.05&lng=13.73&rad=5&sort=price&type=diesel&apikey=YOUR_KEY
```

**API-Key:**
- Kostenlos erhältlich
- Registrierung: https://creativecommons.tankerkoenig.de/

**Vorteile:**
- ✅ Kostenlos
- ✅ Enthält alle Tankstellen (inkl. Aral)
- ✅ Aktuelle Preise (alle 5 Min)
- ✅ Keine Rate-Limits (für normale Nutzung)

---

### 2. Benzinpreis-Aktuell API

**URL:** https://www.benzinpreis-aktuell.de/  
**Dokumentation:** https://www.benzinpreis-aktuell.de/docs/api.pdf

**Was es bietet:**
- Tankstellen-Informationen
- Preise (Diesel, Super, E10, E5)
- Standort-basierte Suche

**Status:** Kommerziell, Preise auf Anfrage

---

### 3. TankBillig API

**URL:** https://tankbillig.info/  
**API:** https://tankbillig.info/get-databroker-rest-api-interface-daten-benzinpreise-spritpreise-tankstellen-super-diesel-deutschland-oesterreich-schweiz-spanien-frankreich

**Was es bietet:**
- REST-API für Benzinpreise
- Tankstellen in mehreren Ländern
- Deutschland, Österreich, Schweiz, Spanien, Frankreich

**Status:** Kommerziell, Preise auf Anfrage

---

### 4. Shell API DIRECT (Nur Shell-Tankstellen)

**URL:** https://www.shell.de/geschaeftskunden/shell-card-tankkarten/digitale-services-und-sicherheit/shell-apis.html

**Was es bietet:**
- Shell-spezifische Funktionen
- Tankkarten-Verwaltung
- Transaktionsdaten
- **KEINE Preise** (nur für Shell Card Kunden)

**Status:** Nur für Shell Card Geschäftskunden

---

## 🎯 Empfehlung: Tankerkönig API

**Warum Tankerkönig?**
1. ✅ **Kostenlos** (Creative Commons)
2. ✅ **Enthält Aral-Tankstellen** (alle MTS-K Tankstellen)
3. ✅ **Aktuelle Preise** (alle 5 Minuten)
4. ✅ **Einfache Integration** (REST-API)
5. ✅ **Keine Rate-Limits** (für normale Nutzung)

**Integration:**
- API-Key kostenlos registrieren
- Service erstellen: `backend/services/fuel_price_api.py`
- Preise cachen (alle 5-10 Minuten aktualisieren)
- In Kostenberechnung integrieren

---

## 📊 Was sonst noch über APIs verfügbar ist?

### Bereits integriert:

1. **OSRM Routing API** ✅
   - Route-Berechnung
   - Distanz-Matrizen
   - Lokaler Server (Docker/Proxmox)

2. **Geoapify Geocoding API** ✅
   - Adressen → Koordinaten
   - Mit API-Key (kostenpflichtig, aber Free Tier)

3. **OpenAI API** ✅
   - KI-Code-Verbesserungen
   - Route-Optimierung
   - Mit API-Key (kostenpflichtig)

4. **OpenStreetMap Overpass API** ✅
   - Baustellen & Sperrungen
   - Kostenlos, keine API-Key nötig

### Verfügbar, aber noch nicht integriert:

1. **Tankerkönig API** (Tankstellen-Preise)
   - Siehe oben

2. **HERE Traffic API** (Verkehrsdaten)
   - Echtzeit-Verkehr
   - Unfälle & Staus
   - Free Tier verfügbar

3. **TomTom Traffic API** (Verkehrsdaten)
   - Echtzeit-Verkehr
   - Kostenpflichtig

4. **Google Maps Traffic API** (Verkehrsdaten)
   - Echtzeit-Verkehr
   - Kostenpflichtig (ab 200$/Monat)

---

## 🔧 Integration-Plan für Tankerkönig API

### Schritt 1: Service erstellen
- `backend/services/fuel_price_api.py`
- Lädt aktuelle Preise von Tankerkönig
- Cacht Preise (5-10 Minuten TTL)

### Schritt 2: Kostenberechnung erweitern
- Verwendet aktuelle Preise statt feste Werte
- Berücksichtigt Fahrzeugtyp (Diesel, E-Auto, Benzin)

### Schritt 3: Konfiguration
- API-Key in `config/app.yaml` oder `.env`
- Standard-Preise als Fallback

---

## 💡 Nächste Schritte

1. **Tankerkönig API-Key registrieren** (kostenlos)
2. **Service implementieren** (`fuel_price_api.py`)
3. **In Kostenberechnung integrieren**
4. **Preise automatisch aktualisieren** (alle 5-10 Minuten)

Soll ich die Integration implementieren?

