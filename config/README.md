# Konfigurationsverwaltung - FAMO TrafficApp 3.0

## Struktur

```
config/
├── static/           # Statische Konfigurationen (keine Zeitstempel)
│   ├── app_config.json      # Hauptkonfiguration
│   ├── geocoding_config.json # Geocoding-Einstellungen
│   ├── routing_config.json   # Routing-Parameter
│   └── ai_config.json       # AI/LLM-Einstellungen
└── dynamic/          # Zeitlich variable Daten
    ├── address_mappings.json
    ├── bar_customers_mappings.json
    ├── private_customers_ignore.json
    └── recognition_rate_analysis.json
```

## Verwendung

### Statische Konfigurationen
- Werden nicht automatisch überschrieben
- Enthalten keine Zeitstempel im Dateinamen
- Werden über Umgebungsvariablen überschrieben

### Dynamische Konfigurationen
- Werden automatisch generiert
- Enthalten Zeitstempel im Dateinamen
- Werden regelmäßig aktualisiert

## Migration von alten Konfigurationsdateien

Alle JSON-Dateien mit Zeitstempel wurden nach `config/dynamic/` verschoben:
- `address_analysis_*.json`
- `mapping_suggestions_*.json`
- `bar_suggestions_*.json`

## Umgebungsvariablen

Die Konfiguration kann über Umgebungsvariablen überschrieben werden:

```bash
# Beispiel: .env Datei
DATABASE_URL=sqlite:///data/traffic.db
GEOCODER_BASE=https://nominatim.openstreetmap.org/search
GEOCODER_RPS=1
GEOCODER_TIMEOUT_S=20
LOG_LEVEL=INFO
```
