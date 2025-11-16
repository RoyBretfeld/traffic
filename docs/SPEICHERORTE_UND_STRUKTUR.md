# Speicherorte & Projektstruktur

## 📂 Alle Dateien & Speicherorte

### 🎯 FA-Dokumentation (Für Fachabteilung)

**Hauptdokumentation:**
- `docs/FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md` ⭐ **START HIER**
  - Vollständige Erklärung des Systems
  - Kosten-Vergleich
  - Technische Details
  - Alle Speicherorte

**Weitere FA-Dokumentation:**
- `docs/ZUSAMMENFASSUNG_ADAPTIVE_ENGINE.md` - Kurze Übersicht
- `docs/INDEX_DOKUMENTATION.md` - Index aller Dokumentationen
- `docs/README_DOKUMENTATION.md` - Dokumentations-Verzeichnis

### 💻 Code-Dateien

**Adaptive Pattern Engine (Haupt-Modul):**
- `backend/services/adaptive_pattern_engine.py`
  - Größe: ~7.5 KB
  - Funktion: Pattern-Engine mit automatischem Lernen
  - Datenbank: `data/learned_patterns.db`

**Integration:**
- `routes/ai_test_api.py`
  - Verwendet: `normalize_city_with_adaptive_engine()`
  - Endpoint: `/api/ai-test/analyze`

**Original-Tourenpläne Schutz:**
- `scripts/protect_tourplaene_originals.py` - Aktiviert Read-Only
- `scripts/verify_originals_readonly.py` - Prüft Schutz-Status
- `fs/protected_fs.py` - Code-Integration (Schreib-Schutz)

**Weitere relevante Dateien:**
- `backend/app.py` - Haupt-App (enthält `/ui/ai-test` Route)
- `frontend/ai-test.html` - AI-Test UI
- `frontend/index.html` - Haupt-UI (Navigation)

### 🗄️ Datenbanken

**Pattern-Datenbank:**
- **Pfad:** `data/learned_patterns.db`
- **Status:** Wird bei erster Nutzung automatisch erstellt
- **Inhalt:**
  - Gelernte Pattern (Input → Output)
  - Pattern-Typen (OT, Slash, Dash, etc.)
  - Nutzungshäufigkeit
  - Zeitstempel

**Weitere Datenbanken:**
- `data/traffic.db` - Haupt-Datenbank
- `data/address_corrections.sqlite3` - Adress-Korrekturen

### 📚 Dokumentation

**Adaptive Pattern Engine:**
- `docs/FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md` ⭐ **FA-Doku**
- `docs/ADAPTIVE_PATTERN_ENGINE.md` - Technische Details
- `docs/SYSTEM_ARCHITEKTUR_ANPASSUNG.md` - Architektur
- `docs/EINFUEHRUNG_ADAPTIVE_PATTERN_ENGINE.md` - Entwickler-Guide
- `docs/AI_COSTS_VS_FLEXIBILITY_ANALYSIS.md` - Kosten-Analyse
- `docs/AI_VS_PURE_PYTHON_ANALYSIS.md` - Vergleich

**Weitere Dokumentation:**
- `docs/ORIGINAL_TOURPLAENE_PROTECTION.md` - Original-Schutz
- `docs/GEOCODING_DETERMINISM.md` - Geocoding
- `docs/DETERMINISTIC_CSV_PARSING.md` - CSV-Parsing

### 🛠️ Scripts & Tools

**Analyse-Scripts:**
- `scripts/analyze_ai_integration.py` - AI-Integration Analyse
- `scripts/analyze_ai_usage.py` - AI-Nutzung Analyse
- `scripts/check_ai_test_setup.py` - AI-Test Setup-Check

**Schutz-Scripts:**
- `scripts/protect_tourplaene_originals.py` - Aktiviert Read-Only
- `scripts/verify_originals_readonly.py` - Prüft Schutz

**Audit-Package:**
- `CSV_PARSING_AUDIT_PACKAGE.zip` - CSV-Parsing Dateien für Audit

### 📁 Verzeichnisstruktur

```
TrafficApp/
├── docs/                                    # Dokumentation
│   ├── FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md  ⭐ FA-Doku
│   ├── ADAPTIVE_PATTERN_ENGINE.md           # Technisch
│   ├── SYSTEM_ARCHITEKTUR_ANPASSUNG.md     # Architektur
│   ├── INDEX_DOKUMENTATION.md              # Index
│   ├── README_DOKUMENTATION.md             # Übersicht
│   ├── DATABASE_SCHEMA.md                   # Datenbank-Schema (Dokumentation)
│   ├── database_schema.sql                  # Datenbank-Schema (SQL)
│   ├── Architecture.md                     # System-Architektur
│   ├── PROJECT_STATUS.md                    # Projekt-Status
│   ├── STATUS_AKTUELL.md                    # Aktueller Stand
│   ├── archive/                              # Archivierte Dokumentation
│   └── status/                               # Status-Dokumentation
│
├── backend/
│   └── services/
│       └── adaptive_pattern_engine.py       # Haupt-Modul (7.5 KB)
│
├── routes/
│   └── ai_test_api.py                      # Integration
│
├── frontend/
│   ├── ai-test.html                        # AI-Test UI
│   └── index.html                          # Haupt-UI
│
├── data/
│   ├── learned_patterns.db                 # Pattern-DB (wird erstellt)
│   ├── traffic.db                          # Haupt-DB
│   ├── customers.db                        # Kunden-Datenbank
│   ├── llm_monitoring.db                   # LLM-Monitoring-Datenbank
│   ├── address_corrections.sqlite3         # Adress-Korrekturen
│   ├── staging/                            # Staging-Verzeichnis (temporäre CSV-Dateien)
│   ├── output/                              # Ausgabe-Verzeichnis
│   ├── uploads/                             # Hochgeladene Dateien
│   ├── backups/                             # Automatische DB-Backups
│   │   └── legacy/                          # Legacy-Backups (aus altem backup-Verzeichnis)
│   ├── archive/                              # Archivierte Dateien (ZIP-Archive)
│   └── temp/                                 # Temporäre Dateien (Test-DBs, Test-CSVs)
│
├── scripts/
│   ├── protect_tourplaene_originals.py    # Original-Schutz
│   ├── verify_originals_readonly.py       # Schutz-Prüfung
│   ├── analyze_ai_integration.py          # AI-Analyse
│   ├── analyze_ai_usage.py                # Nutzungs-Analyse
│   ├── ___sync_alle_ziele.ps1             # Synchronisation zu H: und G:
│   ├── cleanup_root_directory.ps1          # Root-Verzeichnis aufräumen
│   ├── verify_sync.ps1                     # Synchronisations-Verifizierung
│   └── legacy/                              # Legacy-Skripte (aus Root verschoben)
│
├── fs/
│   └── protected_fs.py                     # Dateisystem-Schutz
│
├── tourplaene/                             # Original-CSVs (READ-ONLY)
│   └── *.csv                               # 66 geschützte Dateien
│
└── README.md                               # Projekt-README (aktualisiert)
```

## 🔍 Schnellzugriff

### Für FA (Fachabteilung)
1. **Start:** `docs/FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md`
2. **Übersicht:** `docs/ZUSAMMENFASSUNG_ADAPTIVE_ENGINE.md`
3. **Index:** `docs/INDEX_DOKUMENTATION.md`

### Für Entwickler
1. **Einführung:** `docs/EINFUEHRUNG_ADAPTIVE_PATTERN_ENGINE.md`
2. **Technisch:** `docs/ADAPTIVE_PATTERN_ENGINE.md`
3. **Architektur:** `docs/SYSTEM_ARCHITEKTUR_ANPASSUNG.md`

### Code-Verwendung
```python
# Pattern-Engine verwenden
from backend.services.adaptive_pattern_engine import get_pattern_engine

engine = get_pattern_engine()
normalized, pattern_type = engine.normalize_with_learning("Bannewitz, OT Posen")
```

### UI-Zugriff
- **Hauptseite:** `http://127.0.0.1:8111`
- **AI-Test:** `http://127.0.0.1:8111/ui/ai-test`
- **Test-Dashboard:** `http://127.0.0.1:8111/ui/test-dashboard`

## 📊 Wichtige Informationen

### Dateigrößen
- `adaptive_pattern_engine.py`: 7.5 KB
- Pattern-DB: Wird bei Nutzung erstellt (~10-100 KB je nach Pattern-Anzahl)
- Dokumentation: ~50-100 KB gesamt

### Status
- ✅ **Adaptive Pattern Engine:** Implementiert und aktiv
- ✅ **Original-Schutz:** 66 CSV-Dateien geschützt
- ✅ **Dokumentation:** Vollständig für FA vorbereitet

---

**Letzte Aktualisierung:** 2025-10-31  
**Version:** 1.0  
**Status:** ✅ Produktiv & Dokumentiert

