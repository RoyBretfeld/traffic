# FAMO TrafficApp

On-Prem Routenplanung mit KI für die FAMO GmbH. Dieses System ermöglicht die Verarbeitung von Tourplan-CSVs mit automatischer Geocodierung und Adresserkennung.

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
