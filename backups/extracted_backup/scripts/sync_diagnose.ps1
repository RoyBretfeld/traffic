# Cloud-Synchronisation Diagnose
# 
# Analysiert Unterschiede zwischen lokalem Projekt und Cloud-Ordner
#
# Nutzung:
#   .\scripts\sync_diagnose.ps1

$ErrorActionPreference = "Stop"

# Pfade
$ProjectRoot = $PSScriptRoot + "\.."
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

Write-Host "=== Cloud-Synchronisation Diagnose ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lokaler Pfad: $ProjectRoot" -ForegroundColor Gray
Write-Host "Cloud-Pfad:   $CloudRoot" -ForegroundColor Gray
Write-Host ""

# Prüfe ob beide Pfade existieren
$LocalExists = Test-Path $ProjectRoot
$CloudExists = Test-Path $CloudRoot

if (-not $LocalExists) {
    Write-Host "❌ FEHLER: Lokaler Pfad existiert nicht!" -ForegroundColor Red
    Write-Host "   $ProjectRoot" -ForegroundColor Yellow
    exit 1
}

if (-not $CloudExists) {
    Write-Host "❌ FEHLER: Cloud-Pfad existiert nicht!" -ForegroundColor Red
    Write-Host "   $CloudRoot" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte prüfen:" -ForegroundColor Yellow
    Write-Host "  1. Ist OneDrive synchronisiert?" -ForegroundColor Yellow
    Write-Host "  2. Ist der Pfad korrekt?" -ForegroundColor Yellow
    exit 1
}

# Liste aller wichtigen Dateien
$FilesToCheck = @(
    "___START_HIER_MORGEN_2025-01-10.md",
    "config\tour_ignore_list.json",
    "routes\workflow_api.py",
    "routes\engine_api.py",
    "services\sector_planner.py",
    "services\pirna_clusterer.py",
    "frontend\index.html",
    "docs\STATUS_HEUTE_2025.md",
    "docs\START_HIER_MORGEN.md",
    "docs\CLOUD_SYNC_LISTE.md",
    "docs\98_MINUTEN_ROUTE_PROBLEM.md",
    "docs\PERFORMANCE_OPTIMIERUNG.md",
    "docs\API_ONLY_VERIFIZIERUNG.md",
    "docs\TOUR_IGNORE_LIST.md"
)

Write-Host "Prüfe Dateien..." -ForegroundColor Cyan
Write-Host ""

$MissingInLocal = @()
$MissingInCloud = @()
$DifferentFiles = @()
$SameFiles = @()
$ErrorFiles = @()

foreach ($File in $FilesToCheck) {
    $LocalPath = Join-Path $ProjectRoot $File
    $CloudPath = Join-Path $CloudRoot $File
    
    $LocalExists = Test-Path $LocalPath
    $CloudExists = Test-Path $CloudPath
    
    if (-not $LocalExists -and -not $CloudExists) {
        # Beide fehlen - überspringen
        continue
    }
    
    if (-not $LocalExists) {
        $MissingInLocal += $File
        Write-Host "  ⚠️  Fehlt lokal:     $File" -ForegroundColor Yellow
        continue
    }
    
    if (-not $CloudExists) {
        $MissingInCloud += $File
        Write-Host "  ⚠️  Fehlt in Cloud:  $File" -ForegroundColor Yellow
        continue
    }
    
    # Beide existieren - vergleiche
    try {
        $LocalHash = (Get-FileHash -Path $LocalPath -Algorithm MD5).Hash
        $CloudHash = (Get-FileHash -Path $CloudPath -Algorithm MD5).Hash
        
        if ($LocalHash -eq $CloudHash) {
            $SameFiles += $File
            Write-Host "  ✅ Identisch:       $File" -ForegroundColor Green
        } else {
            $DifferentFiles += $File
            
            # Prüfe Datum
            $LocalDate = (Get-Item $LocalPath).LastWriteTime
            $CloudDate = (Get-Item $CloudPath).LastWriteTime
            
            $Newer = if ($LocalDate -gt $CloudDate) { "lokal" } else { "Cloud" }
            Write-Host "  ⚠️  Unterschiedlich: $File (neuere Version: $Newer)" -ForegroundColor Yellow
            Write-Host "     Lokal:  $LocalDate" -ForegroundColor Gray
            Write-Host "     Cloud:  $CloudDate" -ForegroundColor Gray
        }
    } catch {
        $ErrorFiles += $File
        Write-Host "  ❌ Fehler beim Prüfen: $File" -ForegroundColor Red
        Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host "  ✅ Identisch:        $($SameFiles.Count) Dateien" -ForegroundColor Green
Write-Host "  ⚠️  Unterschiedlich:  $($DifferentFiles.Count) Dateien" -ForegroundColor Yellow
Write-Host "  ⚠️  Fehlt lokal:      $($MissingInLocal.Count) Dateien" -ForegroundColor Yellow
Write-Host "  ⚠️  Fehlt in Cloud:   $($MissingInCloud.Count) Dateien" -ForegroundColor Yellow
if ($ErrorFiles.Count -gt 0) {
    Write-Host "  ❌ Fehler:           $($ErrorFiles.Count) Dateien" -ForegroundColor Red
}

Write-Host ""

# Details für unterschiedliche Dateien
if ($DifferentFiles.Count -gt 0) {
    Write-Host "Unterschiedliche Dateien:" -ForegroundColor Cyan
    foreach ($File in $DifferentFiles) {
        $LocalPath = Join-Path $ProjectRoot $File
        $CloudPath = Join-Path $CloudRoot $File
        $LocalDate = (Get-Item $LocalPath).LastWriteTime
        $CloudDate = (Get-Item $CloudPath).LastWriteTime
        $Newer = if ($LocalDate -gt $CloudDate) { "lokal" } else { "Cloud" }
        $LocalSize = (Get-Item $LocalPath).Length
        $CloudSize = (Get-Item $CloudPath).Length
        Write-Host "  - $File" -ForegroundColor Yellow
        Write-Host "    Neuere Version: $Newer" -ForegroundColor Gray
        Write-Host "    Lokale Größe:   $LocalSize bytes" -ForegroundColor Gray
        Write-Host "    Cloud-Größe:    $CloudSize bytes" -ForegroundColor Gray
    }
    Write-Host ""
}

# Fehlende Dateien
if ($MissingInCloud.Count -gt 0) {
    Write-Host "Fehlt in Cloud (müssen hochgeladen werden):" -ForegroundColor Cyan
    foreach ($File in $MissingInCloud) {
        Write-Host "  - $File" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($MissingInLocal.Count -gt 0) {
    Write-Host "Fehlt lokal (müssen heruntergeladen werden):" -ForegroundColor Cyan
    foreach ($File in $MissingInLocal) {
        Write-Host "  - $File" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Empfehlung
Write-Host "=== Empfehlung ===" -ForegroundColor Cyan
if ($DifferentFiles.Count -gt 0 -or $MissingInCloud.Count -gt 0 -or $MissingInLocal.Count -gt 0) {
    Write-Host "⚠️  Synchronisation erforderlich!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Führe aus:" -ForegroundColor Cyan
    Write-Host "  .\scripts\sync_repair.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Oder manuell:" -ForegroundColor Cyan
    Write-Host "  .\scripts\sync_to_cloud.ps1    (Projekt → Cloud)" -ForegroundColor White
    Write-Host "  .\scripts\sync_from_cloud.ps1  (Cloud → Projekt)" -ForegroundColor White
} else {
    Write-Host "✅ Alle Dateien sind synchronisiert!" -ForegroundColor Green
}

Write-Host ""

