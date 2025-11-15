# Dokumentations-Aufräum-Script
# Führt die Aufräumaktion für den docs/ Ordner durch

$archiveDir = "docs\archive\old_docs_2025-01-10"
if (-not (Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    Write-Host "Archiv-Ordner erstellt: $archiveDir"
}

# Dateien zum Archivieren
$filesToArchive = @(
    # Audit-Dateien
    "AUDIT_*.md",
    "FEHLER_AUDIT_2025-01-10.md",
    "GESAMT_AUDIT_2025-01-10.md",
    "PRODUKT_AUDIT_2025-01-10.md",
    "TOUR_CALCULATION_AUDIT.md",
    
    # Fix-Dateien (bereits implementiert)
    "FIX_*.md",
    "FIXPLAN_500_ERROR_IMPLEMENTIERT.md",
    "FIX_STATUS_INDIKATOREN_2025-01-10.md",
    "KRITISCHE_FEHLER_FIX_2025-01-10.md",
    "FEHLER_ZUSAMMENFASSUNG_500_ERROR.md",
    "TROUBLESHOOTING_FEHLER_2025-01-10.md",
    "CHECKLIST_POST_FIX.md",
    "CHECKLIST_PROBLEME_VERIFIZIERUNG_2025-01-10.md",
    
    # Prompt-Dateien
    "prompt*.md",
    "Prompt*.md",
    
    # Status-Dateien
    "STATUS_*.md",
    "AKTUELLER_*.md",
    "PROJECT_STATUS.md",
    "CURRENT_IMPLEMENTATION_ANALYSIS.md",
    
    # Phase-Dateien
    "PHASE*.md",
    
    # KI-Dateien (bereits implementiert)
    "KI_INTEGRATION_ABGESCHLOSSEN.md",
    "KI_INTEGRATION_STATUS_2025-01-10.md",
    "KI_BENACHRICHTIGUNG_IMPLEMENTIERUNG.md",
    "KI_BENACHRICHTIGUNGSKONZEPT_2025-01-10.md",
    "KI_CONTINUOUS_IMPROVEMENT_KONZEPT.md",
    "KI_CODECHECKER_KONZEPT_2025-01-10.md",
    "KI_CODECHECKER_VERBESSERUNGEN.md",
    "KI_COST_PERFORMANCE_MONITORING.md",
    "KI_CHECKER_STATUS.md",
    
    # Zusammenfassungen
    "FINAL_SUMMARY.md",
    "KONTEXT_ZUSAMMENFASSUNG.md",
    "ZUSAMMENFASSUNG_ADAPTIVE_ENGINE.md",
    "ZUSAMMENFASSUNG_TESTS_KI_CHECKS.md",
    "SYNC_ZUSAMMENFASSUNG_2025-01-09.md",
    "SYNC_STATUS.md",
    
    # Plan-Dateien
    "MASTER_PLAN_UMBAU.md",
    "MVP_PATCHPLAN_IMPLEMENTIERT.md",
    "PLAN_OFFENE_TODOS.md",
    "PLAN_MULTI_MONITOR_ROUTEN_EXPORT.md",
    "TODO_MORGEN.md",
    "START_HIER_MORGEN.md",
    "ZEITSCHAETZUNG_MORGEN.md",
    
    # Feature-Pläne (bereits implementiert)
    "abdock_panels_plan.md",
    "statistik_box_detachbare_panels_cursor_ready_backend_frontend_tests.md",
    "traffic_app_statistikseite_abdockbare_panels_vanilla_js_plan.md",
    "traffic_app_navigations_admin_plan_vanilla_js.md",
    "traffic_app_option_b_statistik_auf_hauptseite_admin_bereich_plan_security_vanilla_js.md",
    "traffic_app_performance_fix_fur_cursor.md",
    "ai_test_orchestrator_konzept_implementierungsplan_vanilla_js_fast_api.md",
    
    # Implementierungs-Dateien (bereits implementiert)
    "MONITORING_IMPLEMENTIERT.md",
    "BACKGROUND_JOB_IMPLEMENTIERUNG.md",
    "SERVER_STARTUP_VERBESSERUNGEN_2025-11-10.md",
    "TESTS_KRITISCHE_FIXES_2025-01-10.md",
    "TESTS_UEBERSICHT_2025-01-10.md",
    "TEST_STRATEGIE_2025-01-10.md",
    "UI_VERBESSERUNGEN_PHASE2.md",
    "PARSING_FIX_BAR_GROUPS.md"
)

# Dateien zum Löschen
$filesToDelete = @(
    # Duplikate
    "ARCHITEKTUR_KOMPLETT.md",
    "DOKUMENTATIONS_INDEX.md",
    "INDEX_DOKUMENTATION.md",
    "README_DOKUMENTATION.md",
    "Doku.md",
    "TIE_Minimal_README.md",
    
    # Veraltete Implementierungs-Dokumentationen
    "IMPLEMENTIERUNGS_UEBERSICHT.md",
    "PROJEKT_DOKUMENTATION_FINAL.md",
    "FAMO_TrafficApp_MasterDoku.md",
    
    # Veraltete API-Dokumentationen
    "API_ONLY_VERIFIZIERUNG.md",
    "ENDPOINT_FLOW.md",
    
    # Veraltete Feature-Dokumentationen
    "MULTI_MONITOR_SUPPORT.md",
    "ORIGINAL_TOURPLAENE_PROTECTION.md",
    "DATABASE_BACKUP.md",
    "DATABASE_README.md",
    
    # Veraltete Analyse-Dateien
    "ERKENNUNGSRATE_ANALYSE.md",
    "AI_AUDIT_SUMMARY.md",
    "AI_VS_PURE_PYTHON_ANALYSIS.md",
    "AI_COSTS_VS_FLEXIBILITY_ANALYSIS.md",
    
    # Veraltete Konzepte
    "AI_ROUTE_OPTIMIZATION.md",
    "Clustering-KI.md",
    "KI_CLUSTERING_ENGINE.md",
    "ADAPTIVE_PATTERN_ENGINE.md",
    "EINFUEHRUNG_ADAPTIVE_PATTERN_ENGINE.md",
    "FA_DOKUMENTATION_ADAPTIVE_PATTERN_ENGINE.md",
    
    # Veraltete Sync-Dokumentationen
    "CLOUD_SYNC_LISTE.md",
    "OFFENE_PUNKTE_2025-01-10.md",
    
    # Veraltete Problem-Dokumentationen
    "98_MINUTEN_ROUTE_PROBLEM.md",
    "W_ROUTE_ISSUES.md",
    "W_ROUTE_OPTIMIERUNG.md",
    "PROBLEM_OSRM_POLYGONE.md",
    "BUGS_TO_FIX.md",
    "FEHLER_URSACHE_ANALYSE.md",
    "FEHLER_URSACHE_ERKLAERUNG.md",
    
    # Sonstige Veraltete Dateien
    "STANDORTBESTIMMUNG_2025.md",
    "SPLITTING_INFO_FLOW.md",
    "SPEICHERORTE_UND_STRUKTUR.md",
    "ROUTING_OPTIMIZATION_NEU.md",
    "ROUTE_VISUALISIERUNG.md",
    "LLM_INTEGRATION_PLAN.md",
    "LLM_ROUTE_RULES.md",
    "LIVE_DATEN_API_RECHERCHE.md",
    "LIVE_TRAFFIC_DATA.md",
    "GEOCODING_DETERMINISM.md",
    "GEO_FAIL_CACHE_POLICY.md",
    "DETERMINISTIC_CSV_PARSING.md",
    "DRESDEN_QUADRANTEN_ZEITBOX.md",
    "CUSTOMER_SYNONYMS.md",
    "CURSOR_KI_BETRIEBSORDNUNG.md",
    "Cursor-Arbeitsrichtlinie.md",
    "VERKEHRSZEITEN_ROUTENPLANUNG.md",
    "SYSTEM_ARCHITEKTUR_ANPASSUNG.md",
    "lizenz_vertriebsplan_fur_famo_traffic_app_v_0.md"
)

Write-Host "Starte Aufräumaktion..."
Write-Host ""

# Archivieren
$archivedCount = 0
foreach ($pattern in $filesToArchive) {
    if ($pattern -like "*.*") {
        # Einzelne Datei
        $file = "docs\$pattern"
        if (Test-Path $file) {
            Move-Item $file $archiveDir -Force -ErrorAction SilentlyContinue
            $archivedCount++
            Write-Host "Archiviert: $pattern"
        }
    } else {
        # Pattern
        $files = Get-ChildItem -Path "docs" -Filter $pattern -File -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Move-Item $file.FullName $archiveDir -Force -ErrorAction SilentlyContinue
            $archivedCount++
            Write-Host "Archiviert: $($file.Name)"
        }
    }
}

# Löschen
$deletedCount = 0
foreach ($file in $filesToDelete) {
    $filePath = "docs\$file"
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force -ErrorAction SilentlyContinue
        $deletedCount++
        Write-Host "Gelöscht: $file"
    }
}

Write-Host ""
Write-Host "Aufräumaktion abgeschlossen!"
Write-Host "Archiviert: $archivedCount Dateien"
Write-Host "Gelöscht: $deletedCount Dateien"
