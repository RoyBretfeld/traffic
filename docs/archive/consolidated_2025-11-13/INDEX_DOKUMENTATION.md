# Dokumentations-Index

## Übersicht aller Dokumentationen

### 🆕 Adaptive Pattern Engine (NEU)

**Hauptdokumentation für FA:**
- `FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md` ⭐ **START HIER**

**Technische Dokumentation:**
- `ADAPTIVE_PATTERN_ENGINE.md` - Vollständige technische Details
- `SYSTEM_ARCHITEKTUR_ANPASSUNG.md` - Architektur-Übersicht
- `ZUSAMMENFASSUNG_ADAPTIVE_ENGINE.md` - Kurze Zusammenfassung
- `EINFUEHRUNG_ADAPTIVE_PATTERN_ENGINE.md` - Entwickler-Einführung
- `AI_COSTS_VS_FLEXIBILITY_ANALYSIS.md` - Kosten-Analyse
- `AI_VS_PURE_PYTHON_ANALYSIS.md` - Vergleich AI vs. Python

### Original-Tourenpläne Schutz

- `ORIGINAL_TOURPLAENE_PROTECTION.md` - Schutz-System für Original-CSVs

### Geocoding & Adress-Erkennung

- `GEOCODING_DETERMINISM.md` - Deterministisches Geocoding
- `DETERMINISTIC_CSV_PARSING.md` - Deterministisches CSV-Parsing
- `GEO_FAIL_CACHE_POLICY.md` - Fail-Cache Strategie

### Entwicklung & Setup

- `DEVELOPER_GUIDE.md` - Entwickler-Anleitung
- `INSTALLATION_GUIDE.md` - Installations-Anleitung
- `TECHNICAL_IMPLEMENTATION.md` - Technische Implementierung
- `ARCHITECTURE.md` - System-Architektur

### API-Dokumentation

- `Api_Docs.md` - API-Übersicht
- `api_manual_geo.md` - Manual Geocoding API
- `MULTI_TOUR_GENERATOR_API.md` - Multi-Tour Generator

### Datenbank

- `DATABASE_SCHEMA.md` - Datenbank-Schema
- `Data_Schema.md` - Daten-Schema

### Weitere Dokumentationen

- `ENDPOINT_FLOW.md` - Endpoint-Flow-Diagramm
- `Clustering-KI.md` - Clustering mit KI
- `Cursor-Arbeitsrichtlinie.md` - Cursor-Arbeitsrichtlinien

## Schnelleinstieg für FA

**Für Fachabteilung (FA):**
1. Start: `FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md`
2. Übersicht: `ZUSAMMENFASSUNG_ADAPTIVE_ENGINE.md`
3. Technisch: `ADAPTIVE_PATTERN_ENGINE.md`

**Für Entwickler:**
1. Start: `EINFUEHRUNG_ADAPTIVE_PATTERN_ENGINE.md`
2. Technisch: `ADAPTIVE_PATTERN_ENGINE.md`
3. Architektur: `SYSTEM_ARCHITEKTUR_ANPASSUNG.md`

## Wichtige Speicherorte

### Code
- **Adaptive Pattern Engine:** `backend/services/adaptive_pattern_engine.py`
- **Integration:** `routes/ai_test_api.py`
- **Original-Schutz:** `scripts/protect_tourplaene_originals.py`

### Datenbanken
- **Pattern-DB:** `data/learned_patterns.db`
- **Traffic-DB:** `data/traffic.db`
- **Address Corrections:** `data/address_corrections.sqlite3`

### Konfiguration
- **Environment:** `env.example` / `.env`
- **Docker:** `docker-compose.yml`

### Dokumentation
- **Hauptverzeichnis:** `docs/`
- **FA-Doku:** `docs/FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md`

