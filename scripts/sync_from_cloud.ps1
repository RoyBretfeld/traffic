# Cloud-Synchronisation: Google Drive → Projekt
# 
# Synchronisiert wichtige Dateien vom Google Drive Ordner zurück zum Projekt:
# G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0
#
# HINWEIS: G:\Meine Ablage\... ist der Google Drive Ordner (nicht OneDrive!)
#
# Nutzung:
#   .\scripts\sync_from_cloud.ps1
#
# ACHTUNG: Überschreibt lokale Dateien!

$ErrorActionPreference = "Stop"

# Pfade
$ProjectRoot = $PSScriptRoot + "\.."
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

Write-Host "=== Cloud → Projekt Synchronisation ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Cloud-Root:    $CloudRoot" -ForegroundColor Gray
Write-Host "Projekt-Root: $ProjectRoot" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  ACHTUNG: Überschreibt lokale Dateien!" -ForegroundColor Yellow
Write-Host ""

# Prüfe ob Cloud-Ordner existiert
if (-not (Test-Path $CloudRoot)) {
    Write-Host "FEHLER: Cloud-Ordner existiert nicht!" -ForegroundColor Red
    Write-Host "Pfad: $CloudRoot" -ForegroundColor Yellow
    exit 1
}

# Bestätigung
$Confirm = Read-Host "Möchten Sie fortfahren? (j/n)"
if ($Confirm -ne "j" -and $Confirm -ne "J") {
    Write-Host "Abgebrochen." -ForegroundColor Yellow
    exit 0
}

# Dateien die synchronisiert werden sollen
$FilesToSync = @(
    # Backend
    "routes\workflow_api.py",
    "routes\engine_api.py",
    "services\sector_planner.py",
    "services\pirna_clusterer.py",
    
    # Frontend
    "frontend\index.html",
    
    # Dokumentation
    "docs\STATUS_HEUTE_2025.md",
    "docs\START_HIER_MORGEN.md"
)

Write-Host ""
Write-Host "Synchronisiere Dateien..." -ForegroundColor Cyan
Write-Host ""

$SyncedCount = 0
$ErrorCount = 0

foreach ($File in $FilesToSync) {
    $SourcePath = Join-Path $CloudRoot $File
    $TargetPath = Join-Path $ProjectRoot $File
    
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

if ($ErrorCount -eq 0) {
    Write-Host "✅ Synchronisation erfolgreich abgeschlossen!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Synchronisation abgeschlossen (mit Fehlern)" -ForegroundColor Yellow
}

