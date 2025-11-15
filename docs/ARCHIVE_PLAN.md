# Dokumentations-Archivierungsplan

**Erstellt:** 2025-11-13  
**Ziel:** Reduzierung der Dokumentationsdateien von ~193 auf ~30-40 aktive Dateien

---

## ✅ Konsolidierte Dokumentation (BEHALTEN)

### Hauptdokumentation
- **STANDARDS.md** ⭐ - Zentrale Standards (wiederverwendbar)
- **API.md** ⭐ - Konsolidierte API-Dokumentation
- **DEVELOPMENT.md** ⭐ - Konsolidiertes Entwicklerhandbuch
- **Architecture.md** ⭐ - Konsolidierte Architektur-Dokumentation
- **INDEX.md** - Vollständiger Dokumentations-Index
- **README.md** - Haupt-README

### Standards
- **STANDARDS/CODE_AUDIT_PLAYBOOK.md** - Code-Audit Playbook
- **STANDARDS/INDEX.md** - Standards-Index

### Spezifische Dokumentation (aktuell & wichtig)
- **DATABASE_SCHEMA.md** - Datenbankschema
- **RUNBOOK_ROUTING.md** - Routing-Runbook
- **LOGGING_GUIDE.md** - Logging-Guide
- **PERFORMANCE_OPTIMIERUNG.md** - Performance-Optimierung
- **ERROR_CATALOG.md** - Fehler-Katalog
- **CUSTOMER_SYNONYMS.md** - Kunden-Synonyme
- **MULTI_TOUR_GENERATOR_API.md** - Multi-Tour-Generator API
- **TOUR_MANAGEMENT.md** - Tour-Management
- **TOUR_IGNORE_LIST.md** - Tour-Ignore-Liste
- **TOUR_NAMING_SCHEMA.md** - Tour-Naming
- **SUB_ROUTES_GENERATOR_LOGIC.md** - Sub-Routen-Logik
- **OSRM_INTEGRATION_ROAD_ROUTES.md** - OSRM-Integration
- **DATABASE_BACKUP.md** - Datenbank-Backup

### Feature-Dokumentation (aktuell)
- **ADAPTIVE_PATTERN_ENGINE.md** - Adaptive Pattern Engine
- **LLM_ROUTE_RULES.md** - LLM-Route-Regeln
- **LLM_INTEGRATION_PLAN.md** - LLM-Integration-Plan
- **CURSOR_KI_BETRIEBSORDNUNG.md** - Cursor-KI Betriebsordnung
- **Cursor-Arbeitsrichtlinie.md** - Cursor-Arbeitsrichtlinie

---

## 📦 ZU ARCHIVIEREN (In `docs/archive/` verschieben)

### Veraltete Architektur-Dokumentation
- `ARCHITEKTUR_KOMPLETT.md` → Inhalt in Architecture.md integriert
- `TECHNICAL_IMPLEMENTATION.md` → Inhalt in Architecture.md integriert
- `TECHNISCHE_DOKUMENTATION.md` → Inhalt in Architecture.md integriert
- `Architecture_OLD.md` → Backup der alten Version

### Veraltete API-Dokumentation
- `Api_Docs.md` → Inhalt in API.md integriert
- `api_tourplan_match.md` → Inhalt in API.md integriert
- `api_tourplan_geocode_missing.md` → Inhalt in API.md integriert
- `api_manual_geo.md` → Inhalt in API.md integriert

### Veraltete Setup/Installation-Dokumentation
- `DEVELOPER_GUIDE.md` → Inhalt in DEVELOPMENT.md integriert
- `INSTALLATION_GUIDE.md` → Inhalt in DEVELOPMENT.md integriert
- `SETUP_ANLEITUNG.md` → Inhalt in DEVELOPMENT.md integriert

### Veraltete Status/Changelog-Dateien (älter als 3 Monate)
- `STATUS_AKTUELL_2025-01-10.md`
- `STATUS_MASTER_PLAN_2025-01-10.md`
- `SESSION_ABSCHLUSS_2025-01-10.md`
- `CHANGELOG_2025-01-10.md`
- `SYNC_CHECKLIST_2025-01-10.md`
- `SYNC_CHECKLIST_2025-01-10_FINAL.md`
- `SYNC_ZUSAMMENFASSUNG_2025-01-10.md`
- `SYNC_ZUSAMMENFASSUNG_2025-01-09.md`
- `CLEANUP_ERGEBNIS_2025-01-10.md`
- `DOCS_CLEANUP_PLAN.md`

### Veraltete Audit-Dateien
- `AUDIT_ALLE_FEHLER_2025-01-10.md`
- `AUDIT_UPLOAD_FEHLER_2025-01-10.md`
- `AUDIT_ERGEBNISSE_2025-01-10.md`
- `AUDIT_PHASE1_2025-01-10.md`
- `AUDIT_500_ERROR_OPTIMIZE.md`
- `AUDIT_SUB_ROUTEN_GENERATOR.md`
- `FEHLER_AUDIT_2025-01-10.md`
- `GESAMT_AUDIT_2025-01-10.md`
- `PRODUKT_AUDIT_2025-01-10.md`

### Veraltete Fix-Dokumentation
- `FIX_402_500_ROUTING_IMPLEMENTIERT.md`
- `FIX_404_402_500_ROUTING.md`
- `FIX_CRITICAL_PYDANTIC_MUTABILITY.md`
- `FIX_ROUTE_DETAILS_404.md`
- `FIX_STATUS_INDIKATOREN_2025-01-10.md`
- `FIX_APPLIED_OSRM_TIMEOUT.md`
- `FIXPLAN_500_ERROR_IMPLEMENTIERT.md`
- `FEHLER_ZUSAMMENFASSUNG_500_ERROR.md`
- `FEHLER_URSACHE_ANALYSE.md`
- `FEHLER_URSACHE_ERKLAERUNG.md`
- `KRITISCHE_FEHLER_FIX_2025-01-10.md`
- `ROUTE_DETAILS_FIX.md`
- `PANEL_SYNCHRONISATION.md`
- `SERVER_STARTUP_VERBESSERUNGEN_2025-11-10.md`

### Veraltete Phase-Dokumentation
- `PHASE1_RUNBOOK_IMPLEMENTIERUNG.md`
- `PHASE1_RUNBOOK_STATUS.md`
- `PHASE1_RUNBOOK_ZUSAMMENFASSUNG.md`
- `PHASE1_VERIFICATION.md`
- `PHASE2_IMPLEMENTIERUNG_STATUS.md`
- `PHASE2_MIGRATION_ANLEITUNG.md`
- `PHASE2_VERIFICATION.md`
- `PHASE2_SCHEMA_ERWEITERUNG.md`
- `UI_VERBESSERUNGEN_PHASE2.md`

### Veraltete KI-Dokumentation (dupliziert)
- `KI_INTEGRATION_STATUS_2025-01-10.md`
- `KI_INTEGRATION_ABGESCHLOSSEN.md`
- `KI_BENACHRICHTIGUNGSKONZEPT_2025-01-10.md`
- `KI_BENACHRICHTIGUNG_IMPLEMENTIERUNG.md`
- `KI_CODECHECKER_KONZEPT_2025-01-10.md`
- `KI_CODECHECKER_VERBESSERUNGEN.md`
- `KI_CONTINUOUS_IMPROVEMENT_KONZEPT.md`
- `KI_COST_PERFORMANCE_MONITORING.md`
- `KI_CHECKER_STATUS.md`
- `KI_CHECKER_API_KEY_SETUP.md`
- `KI_MODell_KONFIGURATION.md`

### Veraltete Test-Dokumentation
- `TEST_STRATEGIE_2025-01-10.md`
- `TESTS_KRITISCHE_FIXES_2025-01-10.md`
- `TESTS_UEBERSICHT_2025-01-10.md`
- `ZUSAMMENFASSUNG_TESTS_KI_CHECKS.md`

### Veraltete Planungs-Dokumentation
- `PLAN_OFFENE_TODOS.md`
- `PLAN_MULTI_MONITOR_ROUTEN_EXPORT.md`
- `MASTER_PLAN_UMBAU.md`
- `MVP_PATCHPLAN_IMPLEMENTIERT.md`
- `AKTUELLER_STAND_2025-01-10.md`
- `AKTUELLER_STATUS.md`
- `STATUS_HEUTE_2025.md`
- `PROJECT_STATUS.md`
- `STATUS_AKTUELL.md`
- `OFFENE_PUNKTE_2025-01-10.md`
- `CHECKLIST_PROBLEME_VERIFIZIERUNG_2025-01-10.md`
- `CHECKLIST_POST_FIX.md`

### Veraltete Implementierungs-Dokumentation
- `BACKGROUND_JOB_IMPLEMENTIERUNG.md`
- `MONITORING_IMPLEMENTIERT.md`
- `IMPLEMENTIERUNGS_UEBERSICHT.md`
- `CURRENT_IMPLEMENTATION_ANALYSIS.md`

### Veraltete Zusammenfassungen
- `FINAL_SUMMARY.md`
- `KONTEXT_ZUSAMMENFASSUNG.md`
- `ZUSAMMENFASSUNG_ADAPTIVE_ENGINE.md`
- `AI_AUDIT_SUMMARY.md`

### Veraltete Prompt-Dokumentation
- `prompt11_frontend_integration.md`
- `prompt12_status_polling.md`
- `prompt13_geocoding_robustness.md`
- `prompt14_protection_guards.md`
- `prompt15_final_cleanup.md`
- `prompt16_fuzzy_suggestions.md`
- `prompt17_alias_accept.md`
- `Prompt19_Audit_Log_Report.md`
- `Prompt20_FailCache_Inspector_Report.md`
- `Prompt21_FailCache_Clear_Report.md`

### Veraltete Analyse-Dokumentation
- `AI_COSTS_VS_FLEXIBILITY_ANALYSIS.md`
- `AI_VS_PURE_PYTHON_ANALYSIS.md`
- `ERKENNUNGSRATE_ANALYSE.md`
- `LIVE_DATEN_API_RECHERCHE.md`
- `LIVE_TRAFFIC_DATA.md`
- `98_MINUTEN_ROUTE_PROBLEM.md`
- `PROBLEM_OSRM_POLYGONE.md`
- `W_ROUTE_ISSUES.md`
- `W_ROUTE_OPTIMIERUNG.md`
- `ROUTING_OPTIMIZATION_NEU.md`
- `TOUR_CALculation_AUDIT.md`
- `PARSING_FIX_BAR_GROUPS.md`

### Veraltete Feature-Pläne
- `abdock_panels_plan.md`
- `traffic_app_performance_fix_fur_cursor.md`
- `traffic_app_statistikseite_abdockbare_panels_vanilla_js_plan.md`
- `traffic_app_option_b_statistik_auf_hauptseite_admin_bereich_plan_security_vanilla_js.md`
- `traffic_app_navigations_admin_plan_vanilla_js.md`
- `statistik_box_detachbare_panels_cursor_ready_backend_frontend_tests.md`
- `ai_test_orchestrator_konzept_implementierungsplan_vanilla_js_fast_api.md`

### Veraltete Sonstige Dokumentation
- `TROUBLESHOOTING_FEHLER_2025-01-10.md`
- `SPEICHERORTE_UND_STRUKTUR.md`
- `SPLITTING_INFO_FLOW.md`
- `ENDPOINT_FLOW.md`
- `DRESDEN_QUADRANTEN_ZEITBOX.md`
- `MULTI_MONITOR_SUPPORT.md`
- `CLOUD_SYNC_LISTE.md`
- `SYNC_STATUS.md`
- `STANDORTBESTIMMUNG_2025.md`
- `VERKEHRSZEITEN_ROUTENPLANUNG.md`
- `ROUTE_VISUALISIERUNG.md`
- `BUGS_TO_FIX.md`
- `TODO_MORGEN.md`
- `ZEITSCHAETZUNG_MORGEN.md`
- `START_HIER_MORGEN.md`
- `TIE_Minimal_README.md`
- `Doku.md`
- `DOKUMENTATIONS_INDEX.md`
- `INDEX_DOKUMENTATION.md`
- `README_DOKUMENTATION.md`
- `PROJEKT_DOKUMENTATION_FINAL.md`
- `FAMO_TrafficApp_MasterDoku.md`
- `lizenz_vertriebsplan_fur_famo_traffic_app_v_0.md`
- `SYSTEM_ARCHITEKTUR_ANPASSUNG.md`
- `ORIGINAL_TOURPLAENE_PROTECTION.md`
- `GEOCODING_DETERMINISM.md`
- `DETERMINISTIC_CSV_PARSING.md`
- `GEO_FAIL_CACHE_POLICY.md`
- `API_ONLY_VERIFIZIERUNG.md`
- `Manual_Geo_Implementation.md`
- `DATABASE_README.md`
- `Clustering-KI.md`
- `EINFUEHRUNG_ADAPTIVE_PATTERN_ENGINE.md`
- `FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md`
- `AI_ROUTE_OPTIMIZATION.md`

---

## 📋 Archivierungs-Befehle

### PowerShell (Windows)
```powershell
# Archiv-Verzeichnis erstellen
New-Item -ItemType Directory -Path "docs\archive\consolidated_2025-11-13" -Force

# Dateien verschieben (Beispiel)
Move-Item "docs\ARCHITEKTUR_KOMPLETT.md" "docs\archive\consolidated_2025-11-13\"
Move-Item "docs\TECHNICAL_IMPLEMENTATION.md" "docs\archive\consolidated_2025-11-13\"
Move-Item "docs\TECHNISCHE_DOKUMENTATION.md" "docs\archive\consolidated_2025-11-13\"
Move-Item "docs\Api_Docs.md" "docs\archive\consolidated_2025-11-13\"
Move-Item "docs\DEVELOPER_GUIDE.md" "docs\archive\consolidated_2025-11-13\"
Move-Item "docs\INSTALLATION_GUIDE.md" "docs\archive\consolidated_2025-11-13\"
Move-Item "docs\SETUP_ANLEITUNG.md" "docs\archive\consolidated_2025-11-13\"
```

### Bash (Linux/macOS)
```bash
# Archiv-Verzeichnis erstellen
mkdir -p docs/archive/consolidated_2025-11-13

# Dateien verschieben (Beispiel)
mv docs/ARCHITEKTUR_KOMPLETT.md docs/archive/consolidated_2025-11-13/
mv docs/TECHNICAL_IMPLEMENTATION.md docs/archive/consolidated_2025-11-13/
mv docs/TECHNISCHE_DOKUMENTATION.md docs/archive/consolidated_2025-11-13/
mv docs/Api_Docs.md docs/archive/consolidated_2025-11-13/
mv docs/DEVELOPER_GUIDE.md docs/archive/consolidated_2025-11-13/
mv docs/INSTALLATION_GUIDE.md docs/archive/consolidated_2025-11-13/
mv docs/SETUP_ANLEITUNG.md docs/archive/consolidated_2025-11-13/
```

---

## 📊 Ergebnis

### Vorher
- **~193 Dokumentationsdateien**
- Viele Duplikate und veraltete Inhalte
- Unübersichtliche Struktur

### Nachher
- **~30-40 aktive Dokumentationsdateien**
- Konsolidierte Hauptdokumentation (STANDARDS.md, API.md, DEVELOPMENT.md, Architecture.md)
- Klare Struktur mit Archiv für veraltete Dokumente

---

## ✅ Nächste Schritte

1. **Archiv-Verzeichnis erstellen**
2. **Dateien verschieben** (siehe Archivierungs-Befehle)
3. **Index-Dateien aktualisieren** (bereits erledigt)
4. **README aktualisieren** (bereits erledigt)
5. **Git-Commit** mit Beschreibung der Konsolidierung

---

**Dieser Plan reduziert die Dokumentationsdateien von ~193 auf ~30-40 aktive Dateien.**

