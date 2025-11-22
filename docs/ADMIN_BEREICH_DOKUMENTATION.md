# FAMO TrafficApp 3.0 – Admin-Bereich Dokumentation

**Version:** 1.1  
**Stand:** 2025-11-20  
**Zweck:** Vollständige Dokumentation des Admin-Bereichs für Entwickler und KI-Assistenten

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#1-übersicht)
2. [Architektur & Struktur](#2-architektur--struktur)
3. [Authentifizierung](#3-authentifizierung)
4. [Navigation](#4-navigation)
5. [Admin-Seiten im Detail](#5-admin-seiten-im-detail)
6. [Backend-Routen](#6-backend-routen)
7. [API-Endpoints](#7-api-endpoints)
8. [Konsistenz-Standards](#8-konsistenz-standards)
9. [Erweiterung des Admin-Bereichs](#9-erweiterung-des-admin-bereichs)

---

## 1. Übersicht

Der Admin-Bereich der FAMO TrafficApp 3.0 ist ein geschützter Bereich für Systemverwaltung, Monitoring und Konfiguration. Er besteht aus mehreren separaten HTML-Seiten mit einer konsistenten Navigation.

### Hauptfunktionen

- **System-Monitoring**: Health-Checks für Server, OSRM, Datenbank, Workflow-Engine und LLM-Integration
- **Statistiken**: Tägliche und monatliche KPIs, Charts und Export-Funktionen
- **Systemregeln**: Verwaltung von System-Konfigurationsregeln
- **DB-Verwaltung**: Datenbank-Informationen, Tabellen-Übersicht und Batch-Geocoding
- **Tour-Filter**: Verwaltung von Ignore- und Allow-Listen für Touren
- **Tour-Import**: Upload und Verarbeitung von Tourenplänen
- **Tourplan-Übersicht**: Gesamt-KPIs und Details für ausgewählte Tourpläne
- **Geo-Cache Vorverarbeitung**: Batch-Geocoding für historische Tourpläne
- **Datenfluss**: Visualisierung des System-Datenflusses

### Zugriff

- **URL-Pfad**: `/admin.html` (Hauptseite) oder direkte Seiten wie `/admin/system.html`
- **Authentifizierung**: Erforderlich (siehe [Authentifizierung](#3-authentifizierung))
- **Port**: 8111 (Standard)

---

## 2. Architektur & Struktur

### 2.1 Dateistruktur

```
frontend/
├── admin.html                    # Admin-Hauptseite (Übersicht/Landing)
├── admin/
│   ├── login.html               # Login-Seite
│   ├── system.html              # System/Health
│   ├── statistik.html           # Statistiken
│   ├── systemregeln.html        # Systemregeln
│   ├── db-verwaltung.html       # DB-Verwaltung
│   ├── tour-filter.html         # Tour-Filter
│   ├── tour-import.html         # Tour-Import
│   ├── tourplan-uebersicht.html # Tourplan-Übersicht
│   ├── geo-cache-vorverarbeitung.html # Geo-Cache Vorverarbeitung
│   └── dataflow.html            # Datenfluss-Visualisierung
```

### 2.2 Architektur-Prinzipien

**Separate HTML-Seiten:**
- Jeder Admin-Bereich hat eine eigene HTML-Seite
- Alle Seiten teilen eine konsistente Navigation (siehe [Navigation](#4-navigation))
- Jede Seite ist über eine eindeutige URL erreichbar

**Konsistenz:**
- Einheitliches Layout (Bootstrap 5.3.0)
- Konsistente Navigation auf allen Seiten
- Einheitliche Styling-Standards (siehe [Konsistenz-Standards](#8-konsistenz-standards))

**Authentifizierung:**
- Alle Admin-Seiten sind geschützt
- Redirect zu `/admin/login.html` bei fehlender Authentifizierung
- Session-basierte Authentifizierung

---

## 3. Authentifizierung

### 3.1 Login-Prozess

**Login-Seite:** `/admin/login.html`

**Login-Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response (200):**
```json
{
  "ok": true,
  "session_id": "abc123...",
  "message": "Login erfolgreich"
}
```

**Response (401):**
```json
{
  "ok": false,
  "error": "Ungültige Anmeldedaten"
}
```

### 3.2 Session-Verwaltung

- **Session-ID**: Wird im Cookie gespeichert (`session_id`)
- **Gültigkeit**: Standardmäßig 24 Stunden
- **Prüfung**: Jede Admin-Seite prüft die Session beim Laden

### 3.3 Logout

**Logout-Endpoint:** `POST /api/auth/logout`

**Status-Endpoint:** `GET /api/auth/status`

**Response:**
```json
{
  "authenticated": true,
  "username": "admin"
}
```

### 3.4 Backend-Implementierung

Alle Admin-HTML-Routen in `backend/app.py` prüfen die Authentifizierung:

```python
@app.get("/admin/system.html", response_class=HTMLResponse)
async def admin_system_page(request: Request):
    """System/Health Seite (geschützt)."""
    from backend.routes.auth_api import get_session_from_request
    session_id = get_session_from_request(request)
    if not session_id:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url="/admin/login.html?redirect=/admin/system.html", 
            status_code=302
        )
    # ... Seite laden
```

---

## 4. Navigation

### 4.1 Navigations-Bar

Alle Admin-Seiten haben eine einheitliche Navigationsleiste ("cool band") mit Gradient-Hintergrund:

**Styling:**
- **Gradient**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- **Border-Radius**: 8px
- **Box-Shadow**: `0 4px 15px rgba(102, 126, 234, 0.3)`
- **Hover-Effekt**: Leichtes Anheben (`translateY(-2px)`)
- **Active-State**: Weißer Hintergrund mit 20% Opacity, weiße Unterstreichung

**HTML-Struktur:**
```html
<nav class="admin-nav-bar">
    <div class="admin-nav-items">
        <a href="/admin/system.html" class="admin-nav-item active">
            <i class="fas fa-heartbeat"></i>
            <span>System/Health</span>
        </a>
        <!-- Weitere Nav-Items -->
    </div>
</nav>
```

### 4.2 Navigations-Punkte

| Nav-Punkt | URL | Icon | Beschreibung |
|-----------|-----|------|--------------|
| System/Health | `/admin/system.html` | `fa-heartbeat` | Health-Checks für alle Systemkomponenten |
| Statistik | `/admin/statistik.html` | `fa-chart-bar` | KPIs, Charts, Export |
| Systemregeln | `/admin/systemregeln.html` | `fa-book` | System-Konfigurationsregeln |
| DB-Verwaltung | `/admin/db-verwaltung.html` | `fa-database` | DB-Info, Tabellen, Batch-Geocoding |
| Tour-Filter | `/admin/tour-filter.html` | `fa-filter` | Ignore/Allow-Listen für Touren |
| Tour-Import | `/admin/tour-import.html` | `fa-upload` | Upload und Verarbeitung von Tourenplänen |
| Tourplan-Übersicht | `/admin/tourplan-uebersicht.html` | `fa-map-marked-alt` | Gesamt-KPIs und Details für ausgewählte Tourpläne |
| Geo-Cache Vorverarbeitung | `/admin/geo-cache-vorverarbeitung.html` | `fa-globe` | Batch-Geocoding für historische Tourpläne |
| Datenfluss | `/admin/dataflow.html` | `fa-project-diagram` | Datenfluss-Visualisierung |

### 4.3 Top-Navigation

Jede Admin-Seite hat zusätzlich eine Top-Navigation (Bootstrap Navbar):

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
        <a class="navbar-brand" href="/">FAMO TrafficApp</a>
        <div class="navbar-nav">
            <a class="nav-link" href="/">Hauptseite</a>
            <a class="nav-link active" href="/admin.html">Admin</a>
        </div>
    </div>
</nav>
```

---

## 5. Admin-Seiten im Detail

### 5.1 System/Health (`/admin/system.html`)

**Zweck:** Überwachung des System-Status aller Komponenten

**Funktionen:**
- Health-Checks für:
  - **Server**: Allgemeiner Server-Status
  - **OSRM**: Routing-Service-Verfügbarkeit
  - **Datenbank**: DB-Verbindung und Tabellen-Status
  - **Workflow-Engine**: Engine-Status
  - **LLM-Integration**: LLM-Service-Verfügbarkeit

**API-Endpoints:**
- `GET /api/health/status` - Gesamt-Status
- `GET /health/osrm` - OSRM-Status
- `GET /health/db` - DB-Status
- `GET /api/workflow/status` - Workflow-Status
- `GET /api/llm/monitoring` - LLM-Status

**UI-Elemente:**
- Health-Cards mit Status-Indikatoren (OK/Error/Warning)
- Latency-Anzeige
- Auto-Refresh (alle 30 Sekunden)

---

### 5.2 Statistik (`/admin/statistik.html`)

**Zweck:** Anzeige von KPIs, Charts und Export-Funktionen

**Funktionen:**
- **KPIs:**
  - Touren (gesamt, heute, diesen Monat)
  - Stops (gesamt, heute, diesen Monat)
  - Kilometer (gesamt, heute, diesen Monat)
  - Verspätungen (gesamt, heute, diesen Monat)
  - Erfolgs-Score (%)

- **Charts:**
  - Tägliche Statistiken (Chart.js)
  - Monatliche Statistiken (Chart.js)

- **Export:**
  - CSV-Export
  - JSON-Export

**API-Endpoints:**
- `GET /api/stats/daily` - Tägliche Statistiken
- `GET /api/stats/monthly` - Monatliche Statistiken
- `GET /api/stats/export/csv` - CSV-Export
- `GET /api/stats/export/json` - JSON-Export

**UI-Elemente:**
- KPI-Cards mit Hover-Effekten
- Chart.js-Diagramme
- Export-Buttons

---

### 5.3 Systemregeln (`/admin/systemregeln.html`)

**Zweck:** Verwaltung von System-Konfigurationsregeln

**Funktionen:**
- **Regeln anzeigen**: Aktuelle Systemregeln aus Datei laden
- **Regeln bearbeiten**: Text-Editor für Regeln
- **Regeln speichern**: Speicherung in `config/system_rules.txt`
- **Regeln zurücksetzen**: Zurücksetzen auf Standard-Regeln

**API-Endpoints:**
- `GET /api/system/rules` - Regeln laden
- `POST /api/system/rules` - Regeln speichern
- `POST /api/system/rules/reset` - Regeln zurücksetzen

**UI-Elemente:**
- Textarea für Regeln-Editor
- Speichern-Button
- Zurücksetzen-Button
- Aktuelle Regeln-Anzeige

---

### 5.4 DB-Verwaltung (`/admin/db-verwaltung.html`)

**Zweck:** Datenbank-Verwaltung und Informationen

**Funktionen:**
- **DB-Informationen:**
  - Datenbank-Pfad
  - Tabellen-Anzahl
  - Gesamt-Größe

- **Tabellen-Übersicht:**
  - Liste aller Tabellen
  - Zeilen-Anzahl pro Tabelle
  - Schema-Anzeige

**API-Endpoints:**
- `GET /api/db/info` - DB-Informationen
- `GET /api/db/stats` - DB-Statistiken
- `GET /api/db/tables` - Tabellen-Liste

**UI-Elemente:**
- Info-Cards
- Tabellen-Liste mit Bootstrap-Table
- Schema-Anzeige (Collapsible)

---

### 5.5 Tour-Filter (`/admin/tour-filter.html`)

**Zweck:** Verwaltung von Ignore- und Allow-Listen für Touren

**Funktionen:**
- **Ignorierte Touren:**
  - Liste von Tour-Namen, die bei der Verarbeitung übersprungen werden
  - Hinzufügen/Entfernen von Einträgen

- **Erlaubte Touren:**
  - Liste von Tour-Namen, die verarbeitet werden
  - Automatisch alle Touren, die nicht in der Ignore-Liste stehen

**UI-Elemente:**
- Zwei Spalten (Ignoriert / Erlaubt)
- Drag & Drop (geplant)
- Add/Remove-Buttons

**Hinweis:** Die Funktionalität zum Hinzufügen/Entfernen von Einträgen ist noch in Entwicklung.

---

### 5.6 Tour-Import (`/admin/tour-import.html`)

**Zweck:** Upload und Verarbeitung von Tourenplänen

**Funktionen:**
- **Upload-Bereich:**
  - Drag & Drop für CSV-Dateien
  - Datei-Auswahl
  - Upload-Status

- **Batch-Geocoding:**
  - Geocoding für alle Tourenpläne
  - Geocoding für einen spezifischen Tourenplan
  - Progress-Anzeige

**API-Endpoints:**
- `GET /api/import/stats` - Import-Statistiken
- `GET /api/import/available-tourplans` - Verfügbare Tourenpläne
- `POST /api/import/upload-tourplan` - Tourenplan-Upload
- `POST /api/import/geocode-all` - Geocoding für alle
- `POST /api/import/geocode-tourplan` - Geocoding für einen Plan

**UI-Elemente:**
- Upload-Area mit Drag & Drop
- Progress-Bars
- Tourenpläne-Tabelle
- Batch-Actions

---

### 5.7 Tourplan-Übersicht (`/admin/tourplan-uebersicht.html`)

**Zweck:** Gesamt-KPIs und Details für ausgewählte Tourpläne

**Funktionen:**
- **Tourplan-Auswahl:**
  - Dropdown mit verfügbaren Tourplänen (aus DB und Dateien)
  - Anzeige von Datum und Dateiname
  - Datei-Upload für neue Tourpläne

- **Gesamt-KPIs:**
  - Total Tours
  - Total Stops
  - Total KM
  - Total Time
  - Total Cost
  - Durchschnittswerte (KM/Tour, Stops/Tour, Time/Tour)

- **Tour-Details:**
  - Tabelle mit allen Touren des ausgewählten Tourplans
  - Details pro Tour: Stops, Distanz, Zeit, Kosten
  - Status-Anzeige (hat Distanz/Zeit)

**API-Endpoints:**
- `GET /api/tourplan/list` - Liste aller verfügbaren Tourpläne
- `GET /api/tourplan/overview?datum=YYYY-MM-DD` - Gesamt-KPIs für einen Tourplan
- `GET /api/tourplan/tours?datum=YYYY-MM-DD` - Details für alle Touren eines Tourplans
- `POST /api/tourplan/upload` - Upload eines neuen Tourplans

---

### 5.8 Geo-Cache Vorverarbeitung (`/admin/geo-cache-vorverarbeitung.html`)

**Zweck:** Batch-Geocoding für historische Tourpläne zur Vorverarbeitung des Geo-Caches

**Funktionen:**
- **Datei-Upload:**
  - Drag & Drop für CSV-Dateien
  - Mehrere Dateien möglich (max. 20 Dateien, je max. 50 MB)
  - Datei-Auswahl und -Entfernung

- **Verarbeitung:**
  - Asynchrones Geocoding (nicht blockierend)
  - Progress-Anzeige pro Datei
  - Cache-Hit-Rate Tracking

- **Statistiken:**
  - Dateien verarbeitet
  - Adressen gefunden
  - Bereits im Cache (mit Prozent)
  - Neu geocodiert
  - Fehler (für manuelle Bearbeitung)

**API-Endpoints:**
- `POST /api/tourplan/batch-geocode` - Batch-Geocoding für einen Tourplan

**Vorteile:**
- ✅ 80%+ der Kunden sind wiederkehrende Kunden
- ✅ Beschleunigt den Workflow erheblich (meiste Adressen bereits im Cache)
- ✅ Asynchrones Geocoding verhindert Blocking

---

### 5.9 Datenfluss (`/admin/dataflow.html`)

**Zweck:** Visualisierung des System-Datenflusses

**Funktionen:**
- **SVG-Diagramm:**
  - Visualisierung des Datenflusses zwischen Komponenten
  - Phasen-Gruppen (Upload, Geocoding, Routing, etc.)
  - Datenbank-Symbole
  - Pfeile für Datenfluss

- **Statistiken:**
  - Live-Statistiken zum Datenfluss
  - Metriken pro Phase

**UI-Elemente:**
- SVG-Diagramm (max-height: 400px)
- Stat-Cards
- Hover-Effekte auf Diagramm-Elementen

---

## 6. Backend-Routen

### 6.1 HTML-Routen

Alle Admin-HTML-Seiten werden über explizite Routen in `backend/app.py` bereitgestellt:

```python
@app.get("/admin.html", response_class=HTMLResponse)
@app.get("/admin/login.html", response_class=HTMLResponse)
@app.get("/admin/system.html", response_class=HTMLResponse)
@app.get("/admin/statistik.html", response_class=HTMLResponse)
@app.get("/admin/systemregeln.html", response_class=HTMLResponse)
@app.get("/admin/db-verwaltung.html", response_class=HTMLResponse)
@app.get("/admin/tour-filter.html", response_class=HTMLResponse)
@app.get("/admin/tour-import.html", response_class=HTMLResponse)
@app.get("/admin/dataflow.html", response_class=HTMLResponse)
```

**Pattern:**
- Alle Routen prüfen die Authentifizierung
- Redirect zu `/admin/login.html?redirect=<ziel-url>` bei fehlender Session
- HTML-Dateien werden über `read_frontend_file()` geladen

### 6.2 Static Files

Statische Dateien (CSS, JS, Bilder) werden über FastAPI StaticFiles bereitgestellt:

```python
app.mount("/static", StaticFiles(directory="frontend"), name="static")
```

---

## 7. API-Endpoints

### 7.1 Health & Monitoring

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `GET /api/health/status` | GET | Gesamt-Status aller Komponenten |
| `GET /health/osrm` | GET | OSRM-Status |
| `GET /health/db` | GET | Datenbank-Status |
| `GET /api/workflow/status` | GET | Workflow-Engine-Status |
| `GET /api/llm/monitoring` | GET | LLM-Status |

### 7.2 Statistiken

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `GET /api/stats/daily` | GET | Tägliche Statistiken |
| `GET /api/stats/monthly` | GET | Monatliche Statistiken |
| `GET /api/stats/export/csv` | GET | CSV-Export |
| `GET /api/stats/export/json` | GET | JSON-Export |

### 7.3 Systemregeln

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `GET /api/system/rules` | GET | Regeln laden |
| `POST /api/system/rules` | POST | Regeln speichern |
| `POST /api/system/rules/reset` | POST | Regeln zurücksetzen |

### 7.4 Datenbank

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `GET /api/db/info` | GET | DB-Informationen |
| `GET /api/db/stats` | GET | DB-Statistiken |
| `GET /api/db/tables` | GET | Tabellen-Liste |

### 7.5 Tour-Import

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `GET /api/import/stats` | GET | Import-Statistiken |
| `GET /api/import/available-tourplans` | GET | Verfügbare Tourenpläne |
| `POST /api/import/upload-tourplan` | POST | Tourenplan-Upload |
| `POST /api/import/geocode-all` | POST | Geocoding für alle |
| `POST /api/import/geocode-tourplan` | POST | Geocoding für einen Plan |

### 7.6 Authentifizierung

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `POST /api/auth/login` | POST | Login |
| `POST /api/auth/logout` | POST | Logout |
| `GET /api/auth/status` | GET | Auth-Status |

---

## 8. Konsistenz-Standards

### 8.1 Layout-Standards

**Body-Styling:**
```css
body {
    background-color: #f8f9fa;
    padding-top: 20px;
}
```

**Container:**
- Alle Seiten verwenden `container-fluid` mit `mt-4` (margin-top)
- Konsistente Abstände zwischen Elementen

### 8.2 Navigation-Standards

**CSS-Klassen:**
- `.admin-nav-bar` - Container für Navigation
- `.admin-nav-items` - Flex-Container für Nav-Items
- `.admin-nav-item` - Einzelnes Nav-Item
- `.admin-nav-item.active` - Aktives Nav-Item

**Styling:**
- Gradient-Hintergrund (siehe [Navigation](#4-navigation))
- Hover-Effekte
- Active-State mit weißer Unterstreichung

### 8.3 Top-Navigation

- Alle Seiten haben eine Top-Navigation mit `navbar-dark bg-dark`
- Links: "Hauptseite" und "Admin"
- Konsistente Branding ("FAMO TrafficApp")

### 8.4 Icons

- Font Awesome 6.0.0
- Konsistente Icon-Verwendung pro Nav-Punkt
- Icons in Nav-Items und Headings

---

## 9. Erweiterung des Admin-Bereichs

### 9.1 Neue Admin-Seite hinzufügen

**Schritte:**

1. **HTML-Datei erstellen:**
   - Erstelle `frontend/admin/<name>.html`
   - Kopiere die Grundstruktur von einer bestehenden Seite
   - Passe Titel, Navigation und Content an

2. **Backend-Route hinzufügen:**
   ```python
   @app.get("/admin/<name>.html", response_class=HTMLResponse)
   async def admin_<name>_page(request: Request):
       """<Name> Seite (geschützt)."""
       from backend.routes.auth_api import get_session_from_request
       session_id = get_session_from_request(request)
       if not session_id:
           from fastapi.responses import RedirectResponse
           return RedirectResponse(
               url=f"/admin/login.html?redirect=/admin/<name>.html", 
               status_code=302
           )
       
       try:
           from backend.utils.path_helpers import read_frontend_file
           content = read_frontend_file(f"admin/<name>.html")
           return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
       except FileNotFoundError:
           raise HTTPException(status_code=404, detail="<Name>-Seite nicht gefunden")
   ```

3. **Navigation erweitern:**
   - Füge Nav-Item in allen Admin-Seiten hinzu
   - Verwende konsistentes Icon und Label
   - Markiere als `active` auf der neuen Seite

4. **API-Endpoints (falls nötig):**
   - Erstelle neue Endpoints in `backend/routes/`
   - Registriere in `backend/app.py`

### 9.2 Best Practices

**✅ Immer:**
- Konsistente Navigation auf allen Seiten
- Authentifizierung prüfen
- Einheitliches Styling
- Responsive Design (Bootstrap)

**❌ Nie:**
- Separate Navigationssysteme einführen
- Authentifizierung umgehen
- Inkompatible Styling-Änderungen
- Doppelte Navigation

### 9.3 Dokumentation aktualisieren

Bei neuen Admin-Seiten:
- Diese Dokumentation aktualisieren
- API-Endpoints dokumentieren
- UI-Elemente beschreiben

---

## 📚 Verwandte Dokumentation

- [`Regeln/ADMIN_NAVIGATION_STANDARDS.md`](../Regeln/ADMIN_NAVIGATION_STANDARDS.md) - Navigation-Standards (veraltet, siehe Hinweis)
- [`docs/API.md`](API.md) - Vollständige API-Dokumentation
- [`docs/ARCHITEKTUR_KOMPLETT.md`](ARCHITEKTUR_KOMPLETT.md) - System-Architektur
- [`PROJECT_PROFILE.md`](../PROJECT_PROFILE.md) - Projekt-Kontext

**⚠️ Hinweis:** `ADMIN_NAVIGATION_STANDARDS.md` beschreibt noch die alte Tab-basierte Struktur. Die aktuelle Implementierung verwendet separate HTML-Seiten mit konsistenter Navigation.

---

## 🎯 Zusammenfassung

Der Admin-Bereich der FAMO TrafficApp 3.0 besteht aus:

- **7 Hauptseiten** mit spezifischen Funktionen
- **Konsistente Navigation** auf allen Seiten
- **Session-basierte Authentifizierung**
- **RESTful API-Endpoints** für alle Funktionen
- **Bootstrap 5.3.0** für Layout und Styling
- **Font Awesome 6.0.0** für Icons

**Zugriff:** `/admin.html` oder direkte Seiten-URLs

**Port:** 8111 (Standard)

---

**Version:** 1.0  
**Stand:** 2025-11-19  
**Projekt:** FAMO TrafficApp 3.0

