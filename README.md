# FAMO TrafficApp 3.0

On-Prem Routenplanung mit KI für die FAMO GmbH. Dieses System ermöglicht die Verarbeitung von Tourplan-CSVs mit automatischer Geocodierung und Adresserkennung.

---

## 📘 **NEU: Zentrale Dokumentation**

### 🌍 **Globale Standards (projektübergreifend)**

**Für alle Cursor-Projekte:**
- → [`Global/GLOBAL_STANDARDS.md`](Global/GLOBAL_STANDARDS.md) - Universelle Entwicklungs-Standards
- → [`Global/PROJEKT_TEMPLATE.md`](Global/PROJEKT_TEMPLATE.md) - Quick-Start für neue Projekte

### 📋 **Projektprofil (FAMO TrafficApp)**

**Technischer Überblick für dieses Projekt:**
- → [`PROJECT_PROFILE.md`](PROJECT_PROFILE.md) - Stack, Infrastruktur, Module, Teststrategie

### 📘 **Projekt-Regeln & Standards**

**Projektspezifische Standards:**
- → [`Regeln/`](Regeln/) - 8 Kern-Dokumente (STANDARDS.md, AUDIT_CHECKLISTE.md, etc.)

**Siehe auch:** [`REGELN_HIER.md`](REGELN_HIER.md) für Schnellzugriff

---

## 📋 Neue Features

### Adaptive Pattern Engine (Kostenlos & Selbstlernend)

**Problem gelöst:** AI-Kosten vs. statischer Python-Code

**Lösung:** Selbstlernendes System, das Pattern automatisch erkennt und speichert - ohne API-Kosten.

**Details:** Siehe `docs/FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md`

**Vorteile:**
- ✅ 100% kostenlos (keine API-Aufrufe)
- ✅ 100-500x schneller als AI (1ms vs. 500ms)
- ✅ Selbstlernend (keine manuelle Pflege)
- ✅ Deterministisch (immer gleiches Ergebnis)

**Ersparnis:** $30-300/Monat (je nach Nutzung)

## 📊 Projektstatus

**Aktueller Stand:** ~80-85% abgeschlossen

✅ **Fertiggestellt:**
- CSV-Parsing mit Synonym-Integration
- DB-First Geocoding (Geoapify, Mapbox, Nominatim)
- Tour-Optimierung (LLM + Nearest-Neighbor)
- Sub-Routen Generator für große Touren
- Automatische DB-Backups
- Test Dashboard

🚧 **In Arbeit:**
- UI-Aufräumarbeiten (nächste Woche)
- Reasoning-Feld in UI integrieren
- Cloud-Synchronisation
- AI-Integration finalisieren

**Details:** Siehe `docs/PROJECT_STATUS.md`

---

## 🤖 Für Cursor-KI: Code-Audits

### **Standard-Workflow für Bug-Fixes:**

**⭐ Lies zuerst:** [`Regeln/CURSOR_WORKFLOW.md`](Regeln/CURSOR_WORKFLOW.md) → **Kompletter 6-Schritt-Prozess!**

1. **Problem klarziehen** (Beschreibung + Logs + Screenshots)
2. **Audit-ZIP vorbereiten** (relevante Dateien + README)
3. **Template wählen** (CURSOR_PROMPT_TEMPLATE.md → #1 oder #10)
4. **Änderung einbauen** (nur wenn verständlich + standards-konform)
5. **Tests & Health-Checks** (Server starten + manuell testen)
6. **Lessons aktualisieren** (LESSONS_LOG + REGELN bei neuem Pattern)

**Wichtige Regeln:**
- ⚠️ **Multi-Layer-Pflicht:** Backend + Frontend + DB + Infra
- ❌ **Kein Ghost-Refactoring:** Nur explizit genannte Dateien
- ✅ **Tests schreiben:** Min. 1 Regressionstest pro Fix
- 🏥 **Health-Checks:** Vor Abschluss prüfen
- 📝 **Dokumentieren:** LESSONS_LOG aktualisieren

### **Quick-Links:**
- 🔄 [6-Schritt-Workflow](Regeln/CURSOR_WORKFLOW.md) ⭐ **NEU!**
- 📖 [Vollständige Standards](Regeln/STANDARDS.md)
- 🚀 [Schnellreferenz](Regeln/STANDARDS_QUICK_REFERENCE.md)
- 🤖 [12 Cursor-Templates](Regeln/CURSOR_PROMPT_TEMPLATE.md)

---

## 🚀 Schnellstart

### Setup in 60 Sekunden

1. **Umgebungsvariablen einrichten**
   ```bash
   cp env.example .env
   # Optional: DATABASE_URL anpassen
   ```

2. **Original-CSV-Dateien ablegen**
   ```bash
   # Kopiere deine CSV-Dateien nach ./Tourplaene/
   # Diese werden NICHT verändert (read-only)
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Pre-commit optional**
   ```bash
   pip install pre-commit && pre-commit install
   ```

5. **Starten & prüfen**
   ```bash
   # Integrität der Original-CSVs prüfen
   python -m tools.orig_integrity build
   
   # App starten
   python backend/app.py
   
   # Health-Check
   curl http://127.0.0.1:8111/health/db
   # Sollte {"ok": true} zurückgeben
   
   # CSV-Liste prüfen
   curl http://127.0.0.1:8111/api/tourplaene/list
   # Sollte verfügbare CSVs anzeigen
   
   # App öffnen
   # http://127.0.0.1:8111
   ```

### Smoke-Test (lokal)

Backend starten, dann:
```bash
python -m tools.smoke
```

**Erwartet:**
- ✔ list (mind. eine CSV)
- ✔ match (zeigt ok/warn/bad Summen)
- ✔ geofill dry (HTTP 200)
- ✔ status (Zähler sichtbar)

### Docker-Entwicklung

1. **Mit Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **App öffnen**
   ```
   http://localhost:8111
   ```

## 🔄 Git-Synchronisation

Für automatische Git-Synchronisation stehen Scripts zur Verfügung:

### PowerShell (Empfohlen)
```powershell
.\scripts\git_sync.ps1 "Commit-Nachricht"
```

### Batch (Windows)
```batch
scripts\git_sync.bat "Commit-Nachricht"
```

Die Scripts führen automatisch aus:
- ✅ `git add .` (alle Änderungen)
- ✅ `git commit` (mit Zeitstempel)
- ✅ `git push` (zu Remote-Repository)

**Hinweis:** Bei erstmaliger Verwendung muss ein Remote-Repository konfiguriert werden:
```bash
git remote add origin <URL>
git push -u origin main
```

## 📁 Projektstruktur

```
TrafficApp/
├── backend/           # FastAPI Backend
├── frontend/          # HTML/CSS/JS Frontend
├── data/              # Daten-Verzeichnisse
│   ├── staging/       # Staging-Bereich
│   └── output/        # Ausgabe-Verzeichnis
├── Tourplaene/        # Original-CSVs (read-only)
├── routen/            # Backup-Verzeichnis
├── scripts/           # Hilfsskripte
│   └── hooks/         # Pre-commit-Hooks
├── tests/             # Unit-Tests
└── docs/              # Dokumentation
```

## 📋 PF/BAR-Synonyme

PF-Kunden („Jochen – PF", „Sven – PF") werden **nicht** geocodiert, sondern aus Synonym-Stammdaten bedient.

### Funktionsweise

- **Synonym-Resolver**: `common/synonyms.py` enthält feste Koordinaten für PF-Kunden
- **Short-Circuit**: Geocoder wird für PF-Kunden **nicht** aufgerufen
- **Frontend**: Zeigt `resolved_address`, routet via `lat/lon`
- **Audit**: Zählt Synonyme als geokodiert

### Synonym-Koordinaten pflegen

```python
# In common/synonyms.py
_SYNONYMS: Dict[str, SynonymHit] = {
    "PF:JOCHEN": SynonymHit("PF:JOCHEN", "Pf-Depot Jochen, Dresden", 51.0500, 13.7373),
    "PF:SVEN":   SynonymHit("PF:SVEN",   "Pf-Depot Sven, Dresden",   51.0600, 13.7300),
}
```

### Akzeptanzkriterien

- ✅ „Jochen – PF" und „Sven – PF" erscheinen **mit Koordinaten** und **ohne** „nan, nan nan"
- ✅ Geocoder wird für diese Einträge **nicht** angerufen (Short-Circuit)
- ✅ API liefert DTO mit `resolved_address`, `geo_source='synonym'`, `valid=true`
- ✅ Audit: `missing_count == 0` bei CSV mit nur PF-Einträgen

### Kundennummern-Resolver (neu)

- In `common/synonyms.py` ist ein schlanker Resolver hinterlegt: `resolve_customer_number(name) -> Optional[int]`.
- Zweck: Für Synonyme die echte ERP-Kundennummer verfügbar machen, ohne bestehende CSV-Felder zu überschreiben.
- API/DTO-Nutzung: wird als separates Feld `customer_number_resolved` ausgegeben (nicht verpflichtend im UI).

### CSV/Import-Härtung (NaN/Excel-Apostroph)

- Parser und Bulk-Prozessor entfernen führende/abschließende Apostroph‑Marker aus Excel und wandeln `NaN` in leere Strings um.
- Adressen werden nur aus vorhandenen Teilen gebaut; es erscheint kein „nan, nan nan“ oder ", ," mehr.
- Frontend rendert priorisiert `resolved_address`, danach `address`, sonst aus Teilen `street, postal_code, city` (bereinigt).

## 🛡️ Schutzmaßnahmen

### Pre-commit-Hooks

Das System verwendet Pre-commit-Hooks zum Schutz der Original-CSVs:

- **Blockiert Schreibzugriffe** auf `./Tourplaene/`
- **Scannt verdächtige Muster** in Code-Änderungen
- **Verhindert versehentliche Modifikationen** der Original-Dateien

### Docker Read-Only-Mounts

Bei Docker-Deployment werden Original-Verzeichnisse read-only gemountet:

```yaml
volumes:
  - ./Tourplaene:/app/Tourplaene:ro    # Originale nur lesen
  - ./data:/app/data:rw                # Daten beschreibbar
```

### CI/CD-Pipeline

GitHub Actions führt automatisch aus:

- **Integritätsprüfungen** der Original-Dateien
- **Unit-Tests** aller Komponenten
- **Docker-Build-Tests**
- **Pre-commit-Hook-Validierung**

## 🔧 Konfiguration

### Umgebungsvariablen

Erstelle eine `.env`-Datei:

```env
# Verzeichnisse
ORIG_DIR=./Tourplaene
STAGING_DIR=./data/staging
OUTPUT_DIR=./data/output
BACKUP_DIR=./routen

# Datenbank
DATABASE_URL=sqlite:///data/traffic.db

# Geocoding
GEOCODER_BASE=https://nominatim.openstreetmap.org/search
GEOCODER_CONTACT=your-email@example.com
GEOCODER_RPS=1
GEOCODER_TIMEOUT_S=20
```

## 🧪 Tests

```bash
# Alle Tests ausführen
pytest

# Tests mit Coverage
pytest --cov=backend --cov=repositories --cov=services

# Spezifische Tests
pytest tests/test_geocode_robust_simple.py -v
```

## 📊 API-Endpoints

- `GET /api/tourplaene/list` - Liste verfügbarer CSVs
- `GET /api/tourplan/match` - Adressen gegen Cache matchen
- `GET /api/tourplan/geocode-missing` - Fehlende Adressen geokodieren
- `GET /api/tourplan/status` - Status-Zähler für CSV
- `GET /health/db` - Datenbank-Health-Check
- `GET /audit/orig-integrity` - Original-Integritätsprüfung

## 🔒 Sicherheitsfeatures

- **PathPolicy**: Verhindert Schreibzugriffe auf Original-Verzeichnisse
- **Fail-Cache**: Verhindert wiederholte Anfragen problematischer Adressen
- **Retry/Backoff**: Robuste Behandlung von Rate-Limiting und Timeouts
- **Integritätsprüfung**: SHA256-Hashes für Original-CSVs
- **Pre-commit-Hooks**: Lokaler Schutz vor versehentlichen Änderungen

## 📝 Entwicklung

### Pre-commit-Hooks aktivieren

```bash
pip install pre-commit
pre-commit install
```

### Tests ausführen

```bash
pytest -v
```

### Docker-Tests

```bash
docker build -t trafficapp-test .
docker-compose config
```

## 🚨 Wichtige Hinweise

- **`./Tourplaene/` ist schreibgeschützt** - Verwende `./data/staging/` oder `./data/output/` für Ausgaben
- **Original-CSVs dürfen nie modifiziert werden** - Pre-commit-Hooks verhindern dies
- **Docker mountet Originale read-only** - Nur Daten-Verzeichnisse sind beschreibbar
- **CI/CD prüft Integrität** - Automatische Validierung bei jedem Push/PR

## 📞 Support

Bei Problemen oder Fragen:

1. Prüfe die Logs in `./logs/`
2. Führe `pytest` aus, um Tests zu validieren
3. Prüfe die CI/CD-Pipeline auf GitHub Actions
4. Kontaktiere das Entwicklungsteam

## Routing Health Checks & Testing

Um die Stabilität und Verfügbarkeit des Routings zu überprüfen, können Sie die folgenden Endpunkte und Skripte verwenden:

* **`GET /health/osrm`**: Überprüft den Status des OSRM-Dienstes, einschließlich Circuit Breaker und Fallback-Status.
* **`GET /_debug/routes`**: Listet alle registrierten API-Routen auf, nützlich zur Verifizierung der Router-Registrierung.
* **Smoke-Test Skript (`scripts/test_smoke_routing.py`)**:
  Dieses Skript sendet Testanfragen an den `/api/tour/route-details`-Endpunkt, um die grundlegende Funktionalität und Fehlerbehandlung zu verifizieren. Führen Sie es mit `python scripts/test_smoke_routing.py` aus.

```bash
python scripts/test_smoke_routing.py
```
