# Export & Live-Daten-Plan (TrafficApp)

**Erstellt:** 2025-01-10  
**Status:** Geplant  
**Zweck:** Die "letzten drei" Bausteine: Maps-Export, Baustellen-Overlay, Speedcams (mit Legal-Guard)

---

## 1) "An Fahrer schicken": Google-/Apple-Maps-Export

### Ziel
Aus einer (Unter-)Route klickbare Navigations-Links generieren und bequem aufs Handy bekommen.

### Backend

**Endpoints:**
- `GET /api/export/maps?tour_id=...&provider=google|apple&max_stops=20`
- `GET /api/export/maps/qr?...` (QR-Code PNG je Segment)

**Logik:**
- Wegpunkte aus DB (Subtour) → (lat,lon)-Liste
- In handliche Chunks teilen (z.B. 20 Stopps pro Link; Limit ist plattformabhängig, daher konfigurierbar)
- URLs bauen:
  - **Google:** `https://www.google.com/maps/dir/?api=1&origin=...&destination=...&waypoints=...&travelmode=driving`
  - **Apple:** `http://maps.apple.com/?saddr=...&daddr=...&dirflg=d`
- Rückgabe: `[{segment:1, url:"..."}, ...]`

**Optional:** QR-Code (PNG) je Segment

### Frontend

- In der Tourübersicht: Button "Export" → Auswahl Google / Apple / QR
- QR-Dialog je Segment; Copy-Link
- (Später) SMS/E-Mail

### (Später) SMS/E-Mail

- `POST /api/export/send-sms` (Twilio/SMTP via .env)
- Logging in `route_exports`

### Tests

- **Unit:** URL-Encoding, Chunking, ≤ max_stops
- **Integration:** `/api/export/maps` für 3 Beispiel-Touren
- **E2E:** QR scannen → Handy öffnet korrekte Route

---

## 2) Live-Daten: Baustellen & "Blitzer" (mit Legal-Guard)

### Baustellen (Autobahn)

**Quelle:** Offizielle Autobahn API (roadworks, closures). Cachen, dann auf der Karte als Overlay zeigen.

**Endpoints:**
- `GET /api/traffic/autobahn/bbox?...` (aus Cache)
- `POST /api/traffic/autobahn/refresh` (pull + persist)

### Speedcams ("Blitzer") – vorsichtig & optional

**Quelle:** OpenStreetMap (`highway=speed_camera`) über Overpass API; regelmäßig cachen.

**⚠️ Rechtlicher Hinweis (DE):**
Die Nutzung von Geräten/Apps zur Warnung während der Fahrt ist nach **§ 23 StVO unzulässig** (Geräte/Funktionen zur Anzeige von Verkehrsüberwachung). Gerichte bestätigen das (z. B. OLG-Rechtsprechung).

**Deshalb:**
- Feature **opt-in**, standardmäßig **aus**
- Klare Warnung im UI
- UI/Settings: Toggle "Speedcams (rechtlich heikel in DE)" + Hinweis
- Auto-Deaktivierung, wenn "Fahrmodus aktiv" gesetzt ist

### Tests

- Smoke-Fetch (Autobahn/Overpass) + Schema-Validierung
- Map-Overlay-Rendering bei 100/1000 Markern
- Toggle respektiert (DE-Legal-Mode an/aus)

---

## 3) Akzeptanzkriterien & Mini-Schema

### Akzeptanz

- Export erzeugt für jede Unterroute ≥1 funktionierende Link-/QR-Variante
- Baustellen erscheinen binnen ≤15 min nach Refresh im Overlay
- Speedcam-Overlay ist **off by default**; Einschalten zeigt Warn-Dialog

### DB (leichtgewichtig ergänzen)

```sql
CREATE TABLE IF NOT EXISTS route_exports (
    id INTEGER PRIMARY KEY,
    tour_id TEXT NOT NULL,
    segment_idx INTEGER NOT NULL,
    provider TEXT NOT NULL,  -- 'google' | 'apple'
    url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS live_roadworks (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,  -- 'autobahn_api'
    payload_json TEXT NOT NULL,
    geom TEXT,  -- GeoJSON oder BBox
    valid_to TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS speed_cameras (
    osm_id TEXT PRIMARY KEY,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    meta_json TEXT,  -- direction, maxspeed, etc.
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 4) Tasks für Cursor (sofort startklar)

### Backend

- `routes/export_maps.py` – Endpoints `GET /api/export/maps`, `GET /api/export/maps/qr`
- `services/exporter.py` – URL-Builder (Google/Apple), Chunking
- `services/qr.py` – PNG-QR erzeugen
- `services/autobahn_client.py` – Pull + Cache
- `services/overpass_client.py` – Speedcams Pull + Cache
- Migrations-Snip für 3 Tabellen oben

### Frontend (Vanilla)

- `frontend/index.html` – Export-Button in Tourliste
- `frontend/js/export.js` – Modal, QR anzeigen, Copy-Link
- `frontend/js/overlays.js` – Layer "Baustellen/Speedcams" + Toggles + Warnhinweis

### Tests

- Pytests: `test_exporter_url.py`, `test_export_chunking.py`
- API-Tests: `/api/export/maps` (200, Links gültig)
- Overlay-Smoke: Mock-Payload → Marker-Count

---

## Kurzer Realitätscheck & Empfehlungen

### Waypoints-Limit
- Variiert je Plattform/Client – wir gehen defensiv mit `max_stops` (Default 20) und splitten automatisch

### Recht & Haftung (Speedcams)
- Feature ist hilfreich, in DE aber heikel
- **Default aus**, klarer Disclaimer im UI
- Admin-Schalter "Legal-Mode=DE" erzwingt OFF
- (Siehe § 23 StVO und gängige Auslegung)

### "Senden ans Handy"
- QR-Codes jetzt
- SMS/E-Mail später per .env aktivierbar

---

## Implementierungsreihenfolge

1. **Phase 1:** Maps-Export (Google/Apple URLs + QR)
2. **Phase 2:** Baustellen-Overlay (Autobahn API)
3. **Phase 3:** Speedcams-Overlay (mit Legal-Guard, opt-in)

---

**Vollständiger Plan:** Verfügbar im Cursor-Plan-Tool mit allen Details, Dateien, Aufgaben und Acceptance-Kriterien.

