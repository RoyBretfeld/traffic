# Cloud-Synchronisation Reparatur
# 
# Repariert Synchronisationsprobleme zwischen lokalem Projekt und Cloud
# - Erstellt Backup
# - Synchronisiert fehlende Dateien
# - Behebt Konflikte (neuere Version behält)
#
# Nutzung:
#   .\scripts\sync_repair.ps1

$ErrorActionPreference = "Stop"

# Pfade
$ProjectRoot = $PSScriptRoot + "\.."
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$BackupRoot = Join-Path $ProjectRoot "backup\sync_repair_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"

Write-Host "=== Cloud-Synchronisation Reparatur ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lokaler Pfad: $ProjectRoot" -ForegroundColor Gray
Write-Host "Cloud-Pfad:   $CloudRoot" -ForegroundColor Gray
Write-Host "Backup-Pfad:  $BackupRoot" -ForegroundColor Gray
Write-Host ""

# Prüfe ob beide Pfade existieren
$LocalExists = Test-Path $ProjectRoot
$CloudExists = Test-Path $CloudRoot

if (-not $LocalExists) {
    Write-Host "❌ FEHLER: Lokaler Pfad existiert nicht!" -ForegroundColor Red
    exit 1
}

if (-not $CloudExists) {
    Write-Host "❌ FEHLER: Cloud-Pfad existiert nicht!" -ForegroundColor Red
    Write-Host "   $CloudRoot" -ForegroundColor Yellow
    exit 1
}

# Bestätigung
Write-Host "⚠️  ACHTUNG: Diese Aktion kann Dateien überschreiben!" -ForegroundColor Yellow
Write-Host ""
$Confirm = Read-Host "Möchten Sie fortfahren? (j/n)"
if ($Confirm -ne "j" -and $Confirm -ne "J") {
    Write-Host "Abgebrochen." -ForegroundColor Yellow
    exit 0
}

# Erstelle Backup-Verzeichnis
Write-Host ""
Write-Host "Erstelle Backup..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
Write-Host "  ✅ Backup-Verzeichnis erstellt: $BackupRoot" -ForegroundColor Green

# Liste aller wichtigen Dateien
$FilesToSync = @(
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

Write-Host ""
Write-Host "Analysiere Dateien..." -ForegroundColor Cyan
Write-Host ""

$SyncedToCloud = 0
$SyncedFromCloud = 0
$BackedUp = 0
$Errors = 0
$Skipped = 0

foreach ($File in $FilesToSync) {
    $LocalPath = Join-Path $ProjectRoot $File
    $CloudPath = Join-Path $CloudRoot $File
    $BackupPath = Join-Path $BackupRoot $File
    
    $LocalExists = Test-Path $LocalPath
    $CloudExists = Test-Path $CloudPath
    
    # Fall 1: Beide existieren - vergleiche
    if ($LocalExists -and $CloudExists) {
        try {
            $LocalHash = (Get-FileHash -Path $LocalPath -Algorithm MD5).Hash
            $CloudHash = (Get-FileHash -Path $CloudPath -Algorithm MD5).Hash
            
            if ($LocalHash -eq $CloudHash) {
                # Identisch - nichts zu tun
                Write-Host "  ✓ Identisch:       $File" -ForegroundColor Gray
                $Skipped++
                continue
            }
            
            # Unterschiedlich - entscheide nach Datum
            $LocalDate = (Get-Item $LocalPath).LastWriteTime
            $CloudDate = (Get-Item $CloudPath).LastWriteTime
            
            if ($LocalDate -gt $CloudDate) {
                # Lokale Version ist neuer → Upload zu Cloud
                # Backup der Cloud-Version
                $BackupDir = Split-Path $BackupPath -Parent
                if (-not (Test-Path $BackupDir)) {
                    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
                }
                Copy-Item -Path $CloudPath -Destination $BackupPath -Force | Out-Null
                $BackedUp++
                
                # Kopiere lokal → Cloud
                $CloudDir = Split-Path $CloudPath -Parent
                if (-not (Test-Path $CloudDir)) {
                    New-Item -ItemType Directory -Path $CloudDir -Force | Out-Null
                }
                Copy-Item -Path $LocalPath -Destination $CloudPath -Force
                $SyncedToCloud++
                Write-Host "  ⬆️  Lokal → Cloud:   $File (lokal ist neuer)" -ForegroundColor Green
            } else {
                # Cloud-Version ist neuer → Download von Cloud
                # Backup der lokalen Version
                $BackupDir = Split-Path $BackupPath -Parent
                if (-not (Test-Path $BackupDir)) {
                    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
                }
                Copy-Item -Path $LocalPath -Destination $BackupPath -Force | Out-Null
                $BackedUp++
                
                # Kopiere Cloud → lokal
                $LocalDir = Split-Path $LocalPath -Parent
                if (-not (Test-Path $LocalDir)) {
                    New-Item -ItemType Directory -Path $LocalDir -Force | Out-Null
                }
                Copy-Item -Path $CloudPath -Destination $LocalPath -Force
                $SyncedFromCloud++
                Write-Host "  ⬇️  Cloud → Lokal:   $File (Cloud ist neuer)" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ❌ Fehler:         $File" -ForegroundColor Red
            Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
            $Errors++
        }
    }
    # Fall 2: Nur lokal existiert → Upload zu Cloud
    elseif ($LocalExists -and -not $CloudExists) {
        try {
            $CloudDir = Split-Path $CloudPath -Parent
            if (-not (Test-Path $CloudDir)) {
                New-Item -ItemType Directory -Path $CloudDir -Force | Out-Null
            }
            Copy-Item -Path $LocalPath -Destination $CloudPath -Force
            $SyncedToCloud++
            Write-Host "  ⬆️  Upload:          $File (fehlte in Cloud)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Fehler:         $File" -ForegroundColor Red
            Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
            $Errors++
        }
    }
    # Fall 3: Nur Cloud existiert → Download von Cloud
    elseif (-not $LocalExists -and $CloudExists) {
        try {
            $LocalDir = Split-Path $LocalPath -Parent
            if (-not (Test-Path $LocalDir)) {
                New-Item -ItemType Directory -Path $LocalDir -Force | Out-Null
            }
            Copy-Item -Path $CloudPath -Destination $LocalPath -Force
            $SyncedFromCloud++
            Write-Host "  ⬇️  Download:        $File (fehlte lokal)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Fehler:         $File" -ForegroundColor Red
            Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
            $Errors++
        }
    }
    # Fall 4: Beide fehlen - überspringen
    else {
        Write-Host "  ⊘ Übersprungen:   $File (fehlt überall)" -ForegroundColor Gray
        $Skipped++
    }
}

Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host "  ⬆️  Hochgeladen:     $SyncedToCloud Dateien" -ForegroundColor Green
Write-Host "  ⬇️  Heruntergeladen: $SyncedFromCloud Dateien" -ForegroundColor Green
Write-Host "  💾 Backup erstellt: $BackedUp Dateien" -ForegroundColor Cyan
Write-Host "  ⊘ Übersprungen:    $Skipped Dateien" -ForegroundColor Gray
if ($Errors -gt 0) {
    Write-Host "  ❌ Fehler:          $Errors Dateien" -ForegroundColor Red
}

Write-Host ""
Write-Host "Backup-Verzeichnis: $BackupRoot" -ForegroundColor Gray
Write-Host ""

if ($Errors -eq 0) {
    Write-Host "✅ Reparatur erfolgreich abgeschlossen!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Reparatur abgeschlossen (mit Fehlern)" -ForegroundColor Yellow
}

Write-Host ""
