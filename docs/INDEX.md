# Dokumentations-Index

**FAMO TrafficApp 3.0 - Zentrale Dokumentationsübersicht**

---

## 🎯 Schnellzugriff

### Für Entwickler
- **[STANDARDS.md](STANDARDS.md)** ⭐ **START HIER** - Zentrale Standards & Richtlinien
- **[DEVELOPMENT.md](DEVELOPMENT.md)** ⭐ **Konsolidiert** - Entwicklerhandbuch (Installation, Setup, Entwicklung)
- **[Architecture.md](Architecture.md)** - System-Architektur

### Für Operations
- **[RUNBOOK_ROUTING.md](RUNBOOK_ROUTING.md)** - Routing-Runbook
- **[LOGGING_GUIDE.md](LOGGING_GUIDE.md)** - Logging-Guide
- **[PERFORMANCE_OPTIMIERUNG.md](PERFORMANCE_OPTIMIERUNG.md)** - Performance-Optimierung

### Für API-Entwicklung
- **[API.md](API.md)** ⭐ **Konsolidiert** - Vollständige API-Dokumentation (alle Endpunkte)
- **[MULTI_TOUR_GENERATOR_API.md](MULTI_TOUR_GENERATOR_API.md)** - Multi-Tour-Generator API (spezifisch)

---

## 📚 Standards (Wiederverwendbar für alle Projekte)

### [STANDARDS.md](STANDARDS.md) ⭐
**Zentrale Standards-Dokumentation** - Alle wichtigen Richtlinien:
- Cursor KI Arbeitsrichtlinien
- Coding Standards (Python, FastAPI, Pydantic)
- Architektur-Prinzipien
- API-Standards
- Testing-Standards
- Git & Versionierung
- Deployment & Operations
- Audit & Compliance

### [STANDARDS/INDEX.md](STANDARDS/INDEX.md)
Index der Standards-Dokumentation

---

## 🏗️ Architektur & Design

- **[Architecture.md](Architecture.md)** ⭐ **Konsolidiert** - Vollständige Architektur-Dokumentation (alle Architektur-Informationen in einem Dokument)

**Hinweis:** Die folgenden Dokumentationen sind in `Architecture.md` integriert:
- `ARCHITEKTUR_KOMPLETT.md` → Abschnitte "Projekt-Statistiken", "Module-Details"
- `TECHNICAL_IMPLEMENTATION.md` → Abschnitt "Technologie-Stack"
- `TECHNISCHE_DOKUMENTATION.md` → Abschnitte "Technologie-Stack", "Backend-Architektur"

---

## 🔌 API-Dokumentation

- **[API.md](API.md)** ⭐ **Konsolidiert** - Vollständige API-Dokumentation (alle Endpunkte in einem Dokument)
- **[MULTI_TOUR_GENERATOR_API.md](MULTI_TOUR_GENERATOR_API.md)** - Multi-Tour-Generator API (spezifisch)

**Hinweis:** Die folgenden spezifischen API-Dokumentationen sind in `API.md` integriert:
- `api_tourplan_match.md` → Abschnitt "Tourplan-Management"
- `api_tourplan_geocode_missing.md` → Abschnitt "Tourplan-Management"
- `api_manual_geo.md` → Abschnitt "Geocoding"

---

## 🧪 Testing & Qualität

- **[TEST_STRATEGIE_2025-01-10.md](TEST_STRATEGIE_2025-01-10.md)** - Test-Strategie
- **[ERROR_CATALOG.md](ERROR_CATALOG.md)** - Fehler-Katalog
- **[TROUBLESHOOTING_FEHLER_2025-01-10.md](TROUBLESHOOTING_FEHLER_2025-01-10.md)** - Troubleshooting

---

## 🚀 Deployment & Operations

- **[DEVELOPMENT.md](DEVELOPMENT.md)** ⭐ **Konsolidiert** - Entwicklerhandbuch (enthält Installation & Setup)
- **[RUNBOOK_ROUTING.md](RUNBOOK_ROUTING.md)** - Routing-Runbook
- **[LOGGING_GUIDE.md](LOGGING_GUIDE.md)** - Logging-Guide
- **[PERFORMANCE_OPTIMIERUNG.md](PERFORMANCE_OPTIMIERUNG.md)** - Performance-Optimierung

**Hinweis:** Die folgenden Dokumentationen sind in `DEVELOPMENT.md` integriert:
- `INSTALLATION_GUIDE.md` → Abschnitt "Installation & Setup"
- `SETUP_ANLEITUNG.md` → Abschnitt "Installation & Setup"
- `DEVELOPER_GUIDE.md` → Abschnitt "Entwicklung"

---

## 📊 Datenbank

- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Datenbank-Schema
- **[Data_Schema.md](Data_Schema.md)** - Daten-Schema
- **[DATABASE_BACKUP.md](DATABASE_BACKUP.md)** - Datenbank-Backup

---

## 🎯 Features

- **[TOUR_MANAGEMENT.md](TOUR_MANAGEMENT.md)** - Tour-Management
- **[TOUR_IGNORE_LIST.md](TOUR_IGNORE_LIST.md)** - Tour-Ignore-Liste
- **[TOUR_NAMING_SCHEMA.md](TOUR_NAMING_SCHEMA.md)** - Tour-Naming
- **[SUB_ROUTES_GENERATOR_LOGIC.md](SUB_ROUTES_GENERATOR_LOGIC.md)** - Sub-Routen-Logik
- **[CUSTOMER_SYNONYMS.md](CUSTOMER_SYNONYMS.md)** - Kunden-Synonyme

---

## 🤖 KI & LLM

- **[KI_MODell_KONFIGURATION.md](KI_MODell_KONFIGURATION.md)** - KI-Modell-Konfiguration
- **[KI_CHECKER_API_KEY_SETUP.md](KI_CHECKER_API_KEY_SETUP.md)** - KI-Checker Setup
- **[LLM_INTEGRATION_PLAN.md](LLM_INTEGRATION_PLAN.md)** - LLM-Integration-Plan
- **[LLM_ROUTE_RULES.md](LLM_ROUTE_RULES.md)** - LLM-Route-Regeln

---

## 🔍 Routing & OSRM

- **[OSRM_INTEGRATION_ROAD_ROUTES.md](OSRM_INTEGRATION_ROAD_ROUTES.md)** - OSRM-Integration
- **[ROUTING_OPTIMIZATION_NEU.md](ROUTING_OPTIMIZATION_NEU.md)** - Routing-Optimierung
- **[ROUTE_VISUALISIERUNG.md](ROUTE_VISUALISIERUNG.md)** - Route-Visualisierung

---

## 📝 Changelogs & Status

- **[CHANGELOG_2025-01-10.md](CHANGELOG_2025-01-10.md)** - Changelog
- **[CHANGELOG_2025-11-06.md](CHANGELOG_2025-11-06.md)** - Changelog
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Projekt-Status
- **[STATUS_AKTUELL.md](STATUS_AKTUELL.md)** - Aktueller Status

---

## 🔐 Audit & Compliance

- **[STANDARDS/CODE_AUDIT_PLAYBOOK.md](STANDARDS/CODE_AUDIT_PLAYBOOK.md)** ⭐ **Code-Audit Playbook** - Einheitlicher Ablauf für Audits
- **[tools/make_audit_zip.py](../tools/make_audit_zip.py)** - Audit-ZIP-Pipeline
- **[scripts/make_audit_zip.sh](../scripts/make_audit_zip.sh)** - Bash-Wrapper
- **[scripts/Make-AuditZip.ps1](../scripts/Make-AuditZip.ps1)** - PowerShell-Wrapper

**Verwendung:**
```bash
# Linux/macOS
bash scripts/make_audit_zip.sh

# Windows
pwsh -File scripts/Make-AuditZip.ps1

# Direkt
python tools/make_audit_zip.py
```

---

## 📦 Archivierte Dokumentation

Veraltete oder historische Dokumentation befindet sich in:
- `docs/archive/` - Archivierte Dokumentation

---

## 🔄 Aktualisierung

Dieser Index wird regelmäßig aktualisiert. Bei neuen Dokumenten:

1. **Dokument erstellen** in `docs/`
2. **Eintrag hinzufügen** in diesem Index
3. **Kategorie zuordnen** (Architektur, API, Testing, etc.)

---

**Letzte Aktualisierung:** 2025-11-13

