# Cloud-Synchronisation: Projekt → OneDrive
# 
# Synchronisiert wichtige Dateien zum Cloud-Ordner:
# G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0
#
# Nutzung:
#   .\scripts\sync_to_cloud.ps1
#
# Oder aus Projekt-Root:
#   powershell -ExecutionPolicy Bypass -File scripts\sync_to_cloud.ps1

$ErrorActionPreference = "Stop"

# Pfade
$ProjectRoot = $PSScriptRoot + "\.."
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

Write-Host "=== Cloud-Synchronisation ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Projekt-Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Cloud-Root:    $CloudRoot" -ForegroundColor Gray
Write-Host ""

# Prüfe ob Cloud-Ordner existiert
if (-not (Test-Path $CloudRoot)) {
    Write-Host "FEHLER: Cloud-Ordner existiert nicht!" -ForegroundColor Red
    Write-Host "Pfad: $CloudRoot" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte prüfen:" -ForegroundColor Yellow
    Write-Host "  1. Ist OneDrive synchronisiert?" -ForegroundColor Yellow
    Write-Host "  2. Ist der Pfad korrekt?" -ForegroundColor Yellow
    exit 1
}

# Dateien die synchronisiert werden sollen
$FilesToSync = @(
    # === WICHTIGSTE DATEI FÜR MORGEN ===
    "___START_HIER_MORGEN_2025-01-10.md",
    
    # Backend
    "routes\workflow_api.py",
    "routes\engine_api.py",
    "services\sector_planner.py",
    "services\pirna_clusterer.py",
    
    # Frontend
    "frontend\index.html",
    
    # Konfiguration
    "config\tour_ignore_list.json",
    
    # Dokumentation
    "docs\STATUS_HEUTE_2025.md",
    "docs\START_HIER_MORGEN.md",
    "docs\CLOUD_SYNC_LISTE.md",
    
    # Weitere wichtige Dateien
    "docs\98_MINUTEN_ROUTE_PROBLEM.md",
    "docs\PERFORMANCE_OPTIMIERUNG.md",
    "docs\API_ONLY_VERIFIZIERUNG.md",
    "docs\TOUR_IGNORE_LIST.md",
    "docs\CURSOR_KI_BETRIEBSORDNUNG.md",
    "docs\Architecture.md",
    "docs\ENDPOINT_FLOW.md"
)

Write-Host "Synchronisiere Dateien..." -ForegroundColor Cyan
Write-Host ""

$SyncedCount = 0
$ErrorCount = 0

foreach ($File in $FilesToSync) {
    $SourcePath = Join-Path $ProjectRoot $File
    $TargetPath = Join-Path $CloudRoot $File
    
    if (-not (Test-Path $SourcePath)) {
        Write-Host "  ⚠️  Übersprungen (nicht gefunden): $File" -ForegroundColor Yellow
        $ErrorCount++
        continue
    }
    
    # Erstelle Ziel-Verzeichnis falls nicht vorhanden
    $TargetDir = Split-Path $TargetPath -Parent
    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }
    
    try {
        # Kopiere Datei
        Copy-Item -Path $SourcePath -Destination $TargetPath -Force
        
        $SyncedCount++
        Write-Host "  ✅ Synchronisiert: $File" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Fehler: $File" -ForegroundColor Red
        Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host "  ✅ Erfolgreich: $SyncedCount Dateien" -ForegroundColor Green
if ($ErrorCount -gt 0) {
    Write-Host "  ❌ Fehler: $ErrorCount Dateien" -ForegroundColor Red
}
Write-Host ""
Write-Host "Cloud-Ordner: $CloudRoot" -ForegroundColor Gray
Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "✅ Synchronisation erfolgreich abgeschlossen!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Synchronisation abgeschlossen (mit Fehlern)" -ForegroundColor Yellow
}

