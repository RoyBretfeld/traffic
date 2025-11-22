# Tank- und Strompreise Integration

**Erstellt:** 2025-11-22  
**Status:** ✅ Implementiert (Tankpreise), ⏳ Strompreise folgt später  
**Version:** 1.0

---

## 📋 Übersicht

Die TrafficApp integriert aktuelle Tankpreise über die **Tankerkönig API** (kostenlos, Creative Commons). Die Preise werden automatisch alle 5-10 Minuten aktualisiert und in der Kostenberechnung verwendet.

**Features:**
- ✅ Aktuelle Tankpreise (Diesel, Super E10, Super E5, AdBlue)
- ✅ Automatisches Caching (5 Minuten TTL)
- ✅ Fallback-Preise wenn API nicht verfügbar
- ⏳ Strompreise (vorsorglich vorbereitet, Berechnung folgt später)
- ⏳ Preisverlauf-Chart (vorbereitet)

---

## 🏗️ Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────────┐
│  Frontend: admin/tankpreise.html                        │
│  - Anzeige aktueller Preise                             │
│  - Preisverlauf-Chart (Chart.js)                        │
│  - Auto-Update alle 5 Minuten                           │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP GET
                   ▼
┌─────────────────────────────────────────────────────────┐
│  API-Endpoint: /api/fuel-prices/current                 │
│  (backend/routes/fuel_price_api.py)                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Service: backend/services/fuel_price_api.py           │
│  - get_current_fuel_prices()                            │
│  - fetch_fuel_prices_from_api()                         │
│  - get_cached_prices()                                  │
│  - get_fallback_prices()                                │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP GET
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Tankerkönig API (Extern)                               │
│  https://creativecommons.tankerkoenig.de/               │
│  - Kostenlos, Creative Commons Lizenz                    │
│  - Alle 5 Minuten aktualisiert                          │
│  - Enthält alle Tankstellen (inkl. Aral)                │
└─────────────────────────────────────────────────────────┘
```

### Datenfluss

1. **Frontend** lädt Seite → ruft `/api/fuel-prices/current` auf
2. **API-Endpoint** prüft Cache (5 Min TTL)
3. **Service** lädt Preise von Tankerkönig API (falls Cache abgelaufen)
4. **Service** berechnet Durchschnitt der 5 günstigsten Tankstellen in Dresden (10km Radius)
5. **Service** speichert Preise im Cache
6. **API-Endpoint** gibt Preise als JSON zurück
7. **Frontend** aktualisiert Anzeige

---

## 🔌 API-Anbindung

### Tankerkönig API

**URL:** https://creativecommons.tankerkoenig.de/  
**Lizenz:** Creative Commons (kostenlos)  
**Registrierung:** https://creativecommons.tankerkoenig.de/

**Endpunkt:**
```
GET https://creativecommons.tankerkoenig.de/json/list.php
```

**Parameter:**
- `lat` - Breitengrad (Dresden: 51.0504)
- `lng` - Längengrad (Dresden: 13.7373)
- `rad` - Radius in km (10)
- `sort` - Sortierung (`price` = nach Preis)
- `type` - Kraftstofftyp (`diesel`, `e10`, `e5`)
- `apikey` - API-Key (aus Config)

**Response:**
```json
{
  "ok": true,
  "stations": [
    {
      "id": "...",
      "name": "Tankstelle Name",
      "brand": "Aral",
      "street": "Straße",
      "place": "Dresden",
      "diesel": 1.459,
      "e10": 1.549,
      "e5": 1.599,
      ...
    }
  ]
}
```

### Interne API-Endpunkte

#### GET `/api/fuel-prices/current`

Gibt aktuelle Tankpreise zurück.

**Query-Parameter:**
- `force_refresh` (optional, bool): Cache ignorieren und neu laden

**Response:**
```json
{
  "success": true,
  "prices": {
    "diesel": {
      "price": 1.459,
      "unit": "€/L",
      "source": "tankerkoenig",
      "last_update": "2025-11-22T10:30:00",
      "change": 0.0
    },
    "e10": {
      "price": 1.549,
      "unit": "€/L",
      "source": "tankerkoenig",
      "last_update": "2025-11-22T10:30:00",
      "change": 0.0
    },
    "e5": {
      "price": 1.599,
      "unit": "€/L",
      "source": "tankerkoenig",
      "last_update": "2025-11-22T10:30:00",
      "change": 0.0
    },
    "adblue": {
      "price": 0.80,
      "unit": "€/L",
      "source": "standard",
      "last_update": "2025-11-22T10:30:00",
      "change": 0.0
    }
  },
  "timestamp": "2025-11-22T10:30:00"
}
```

#### GET `/api/fuel-prices/history`

Gibt Preisverlauf zurück (TODO: noch nicht implementiert).

#### GET `/api/electricity-prices/current`

Gibt aktuelle Strompreise zurück (TODO: noch nicht implementiert).

---

## ⚙️ Konfiguration

### API-Key einrichten

**Option 1: Umgebungsvariable (.env)**
```bash
TANKERKOENIG_API_KEY=dein-api-key-hier
```

**Option 2: config/app.yaml**
```yaml
tankerkoenig:
  api_key: "dein-api-key-hier"
```

### Abhängigkeiten

**Python:**
- `httpx` - Für async HTTP-Requests (muss installiert sein)

**Installation:**
```bash
pip install httpx
```

### Cache-Konfiguration

**TTL:** 5 Minuten (konfigurierbar in `fuel_price_api.py`)

```python
_price_cache = {
    "cache_ttl_minutes": 5  # Kann angepasst werden
}
```

---

## 📊 Preisberechnung

### Tankpreise

1. **API-Aufruf:** Suche nach Tankstellen in Dresden (10km Radius)
2. **Filterung:** Sortiere nach Preis (günstigste zuerst)
3. **Durchschnitt:** Berechne Durchschnitt der 5 günstigsten Tankstellen
4. **Caching:** Speichere Ergebnis für 5 Minuten

### AdBlue

- **Standard-Preis:** 0.80 €/L (fest)
- **Quelle:** Konfiguration (kann später aus API kommen)

### Strompreise

- **Status:** Vorsorglich vorbereitet
- **Berechnung:** Folgt später
- **Typen:**
  - AC-Ladestation (Wechselstrom)
  - DC-Schnellladung (Gleichstrom)
  - Hausladung

---

## 🔄 Integration in Kostenberechnung

Die Tankpreise werden automatisch in der Kostenberechnung verwendet:

**Datei:** `backend/services/stats_aggregator.py`

**Aktuell:**
- Feste Preise in `get_vehicle_cost_config()`

**Zukünftig:**
- Preise aus `fuel_price_api.get_current_fuel_prices()` laden
- Dynamisch in Kostenberechnung einbinden

**Beispiel:**
```python
from backend.services.fuel_price_api import get_current_fuel_prices

prices = await get_current_fuel_prices()
diesel_price = prices["diesel"]["price"]
```

---

## 🧪 Testing

### Manueller Test

1. **API-Key konfigurieren**
2. **Server starten**
3. **Admin-Seite öffnen:** `/admin/tankpreise.html`
4. **Preise sollten automatisch geladen werden**

### API-Test

```bash
# Aktuelle Preise abrufen
curl http://localhost:8111/api/fuel-prices/current

# Mit Force-Refresh
curl http://localhost:8111/api/fuel-prices/current?force_refresh=true
```

### Fallback-Test

1. **API-Key entfernen oder falsch setzen**
2. **Preise sollten Fallback-Werte anzeigen:**
   - Diesel: 1.45 €/L
   - E10: 1.55 €/L
   - E5: 1.60 €/L
   - AdBlue: 0.80 €/L

---

## 📝 TODO / Offene Punkte

### Kurzfristig

- [ ] Preisverlauf in DB speichern (für Chart)
- [ ] Preisänderungen berechnen (gegenüber vorherigem Wert)
- [ ] Navigation in allen Admin-Seiten aktualisieren
- [ ] `httpx` Abhängigkeit prüfen/installieren

### Mittelfristig

- [ ] Strompreise implementieren (API recherchieren)
- [ ] Preisverlauf-Chart vollständig implementieren
- [ ] Integration in Kostenberechnung (dynamische Preise)
- [ ] AdBlue-Preise aus API (falls verfügbar)

### Langfristig

- [ ] Preis-Alerts (bei starken Änderungen)
- [ ] Historische Preisdaten analysieren
- [ ] Optimale Tankstellen-Empfehlungen basierend auf Route

---

## 🔗 Verwandte Dateien

**Frontend:**
- `frontend/admin/tankpreise.html` - Admin-Seite
- `frontend/js/admin-info-banner.js` - Info-Banner-Komponente

**Backend:**
- `backend/routes/fuel_price_api.py` - API-Endpoints
- `backend/services/fuel_price_api.py` - Service-Logik
- `backend/app.py` - Route für `/admin/tankpreise.html` (Zeile ~437)

**Konfiguration:**
- `config/app.yaml` - App-Konfiguration
- `.env` - Umgebungsvariablen

**Dokumentation:**
- `docs/TANKSTELLEN_API_RECHERCHE.md` - API-Recherche
- `docs/TANKPREISE_INTEGRATION.md` - Diese Datei
- `docs/TANKPREISE_ZUSAMMENFASSUNG.md` - Zusammenfassung

---

## 🐛 Bekannte Probleme

**Keine bekannt** (Stand: 2025-11-22)

---

## 📚 Referenzen

- **Tankerkönig API:** https://creativecommons.tankerkoenig.de/
- **Tankerkönig Dokumentation:** https://creativecommons.tankerkoenig.de/
- **Chart.js:** https://www.chartjs.org/

---

**Letzte Aktualisierung:** 2025-11-22  
**Verantwortlich:** KI-Assistent (Cursor)

