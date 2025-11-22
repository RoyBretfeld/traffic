# Vollständiges Backup ALLER Dateien in die Cloud
# Erstellt: ZIP-Archiv mit allen Projekt-Dateien und kopiert es in Google Drive
#
# Cloud-Ordner: G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0
# Google Drive synchronisiert automatisch von diesem Ordner zu Google Drive
#
# Nutzung:
#   .\scripts\backup_complete_to_cloud.ps1
#
# Oder aus Projekt-Root:
#   powershell -ExecutionPolicy Bypass -File scripts\backup_complete_to_cloud.ps1

$ErrorActionPreference = "Stop"

# Pfade
$SourceRoot = "E:\_____1111____Projekte-Programmierung"
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung"
$ProjectRoot = $PSScriptRoot + "\.."
$BackupDir = Join-Path $ProjectRoot "backups"
$CloudBackupDir = Join-Path $CloudRoot "backups"

# Zeitstempel
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$zipName = "backup_complete_$timestamp.zip"
$zipPath = Join-Path $BackupDir $zipName
$cloudZipPath = Join-Path $CloudBackupDir $zipName

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VOLLSTAENDIGES CLOUD-BACKUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle:       $SourceRoot" -ForegroundColor Gray
Write-Host "Ziel:         $CloudRoot" -ForegroundColor Gray
Write-Host "Projekt:      $ProjectRoot" -ForegroundColor Gray
Write-Host "Backup-Datei: $zipName" -ForegroundColor Gray
Write-Host ""

# 1. Prüfe ob Cloud-Ordner existiert
Write-Host "[1/6] Prüfe Cloud-Ordner..." -ForegroundColor Yellow
if (-not (Test-Path $CloudRoot)) {
    Write-Host "  FEHLER: Google Drive Ordner existiert nicht!" -ForegroundColor Red
    Write-Host "  Pfad: $CloudRoot" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte prüfen:" -ForegroundColor Yellow
    Write-Host "  1. Ist Google Drive synchronisiert?" -ForegroundColor Yellow
    Write-Host "  2. Ist der Pfad korrekt?" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Cloud-Ordner gefunden" -ForegroundColor Green

# 2. Backup-Verzeichnis erstellen
Write-Host ""
Write-Host "[2/6] Erstelle Backup-Verzeichnisse..." -ForegroundColor Yellow
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "  OK: Lokales Backup-Verzeichnis erstellt" -ForegroundColor Green
} else {
    Write-Host "  OK: Lokales Backup-Verzeichnis vorhanden" -ForegroundColor Green
}

if (-not (Test-Path $CloudBackupDir)) {
    New-Item -ItemType Directory -Path $CloudBackupDir -Force | Out-Null
    Write-Host "  OK: Cloud-Backup-Verzeichnis erstellt" -ForegroundColor Green
} else {
    Write-Host "  OK: Cloud-Backup-Verzeichnis vorhanden" -ForegroundColor Green
}

# 3. Git-Status prüfen (optional)
Write-Host ""
Write-Host "[3/6] Prüfe Git-Status..." -ForegroundColor Yellow
try {
    $gitStatus = git status --short 2>$null
    if ($gitStatus) {
        Write-Host "  WARNUNG: Uncommitted Änderungen gefunden" -ForegroundColor Yellow
        Write-Host "  Empfehlung: Git-Commit vor Backup erstellen" -ForegroundColor Yellow
    } else {
        Write-Host "  OK: Keine uncommitted Änderungen" -ForegroundColor Green
    }
} catch {
    Write-Host "  INFO: Git nicht verfügbar oder kein Repository" -ForegroundColor Gray
}

# 4. Erstelle Liste aller zu sichernden Dateien/Ordner
Write-Host ""
Write-Host "[4/6] Erstelle Datei-Liste..." -ForegroundColor Yellow

# Verzeichnisse die ausgeschlossen werden sollen
$ExcludeDirs = @(
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "chroma_db",
    "*.egg-info",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "backups",  # Backups selbst nicht sichern (verhindert Rekursion)
    "ZIP",
    "temp",
    "tmp",
    "logs"
)

# Dateien die ausgeschlossen werden sollen
$ExcludeFiles = @(
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "*.swp",
    "*.swo",
    "*~",
    "*.log"
)

# Sammle ALLE Dateien und Ordner aus dem gesamten Quell-Verzeichnis
$itemsToBackup = @()

Write-Host "  Scanne Verzeichnis: $SourceRoot" -ForegroundColor Gray

# Hole alle Unterverzeichnisse
$allDirs = Get-ChildItem -Path $SourceRoot -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object {
    $dirPath = $_.FullName
    $relativePath = $dirPath.Replace($SourceRoot + "\", "")
    
    # Prüfe Ausschlüsse
    $shouldExclude = $false
    foreach ($excludeDir in $ExcludeDirs) {
        if ($relativePath -like "*\$excludeDir\*" -or $relativePath -like "*/$excludeDir/*" -or $relativePath -like "$excludeDir\*" -or $relativePath -like "$excludeDir/*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

# Hole alle Dateien
$allFiles = Get-ChildItem -Path $SourceRoot -File -Recurse -ErrorAction SilentlyContinue | Where-Object {
    $filePath = $_.FullName
    $relativePath = $filePath.Replace($SourceRoot + "\", "")
    
    # Prüfe Ausschlüsse
    $shouldExclude = $false
    foreach ($excludeDir in $ExcludeDirs) {
        if ($relativePath -like "*\$excludeDir\*" -or $relativePath -like "*/$excludeDir/*") {
            $shouldExclude = $true
            break
        }
    }
    if ($shouldExclude) {
        return $false
    }
    
    foreach ($excludeFile in $ExcludeFiles) {
        if ($relativePath -like $excludeFile) {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

$itemsToBackup = $allFiles

Write-Host "  OK: $($itemsToBackup.Count) Dateien gefunden" -ForegroundColor Green

# 5. Erstelle ZIP-Archiv
Write-Host ""
Write-Host "[5/6] Erstelle ZIP-Archiv..." -ForegroundColor Yellow
Write-Host "  Datei: $zipName" -ForegroundColor Gray
Write-Host "  Dies kann einige Minuten dauern..." -ForegroundColor Gray

try {
    # Lösche alte ZIP-Datei falls vorhanden
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    # Erstelle temporäres Verzeichnis für Backup-Inhalt
    $tempBackupDir = Join-Path $env:TEMP "backup_temp_$timestamp"
    if (Test-Path $tempBackupDir) {
        Remove-Item $tempBackupDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempBackupDir -Force | Out-Null
    
    $fileCount = 0
    $errorCount = 0
    
    # Kopiere alle Dateien in temporäres Verzeichnis (mit Ausschlüssen)
    Write-Host "  Kopiere Dateien..." -ForegroundColor Gray
    
    foreach ($item in $itemsToBackup) {
        try {
            $itemPath = $item
            if (-not (Test-Path $itemPath)) {
                continue
            }
            
            $relativePath = $itemPath.Replace($SourceRoot + "\", "").Replace($SourceRoot + "/", "")
            
            # Prüfe ob ausgeschlossen
            $shouldExclude = $false
            foreach ($excludeDir in $ExcludeDirs) {
                if ($relativePath -like "*\$excludeDir\*" -or $relativePath -like "*/$excludeDir/*" -or $relativePath -like "$excludeDir\*" -or $relativePath -like "$excludeDir/*") {
                    $shouldExclude = $true
                    break
                }
            }
            if ($shouldExclude) {
                continue
            }
            
            # Prüfe ob Datei ausgeschlossen
            foreach ($excludeFile in $ExcludeFiles) {
                if ($relativePath -like $excludeFile) {
                    $shouldExclude = $true
                    break
                }
            }
            if ($shouldExclude) {
                continue
            }
            
            # Einzelne Datei (da wir bereits alle Dateien haben)
            $targetPath = Join-Path $tempBackupDir $relativePath
            $targetDir = Split-Path $targetPath -Parent
            
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            
            try {
                Copy-Item -Path $itemPath -Destination $targetPath -Force -ErrorAction Stop
                $fileCount++
            } catch {
                $errorCount++
            }
        } catch {
            $errorCount++
        }
    }
    
    # Erstelle ZIP aus temporärem Verzeichnis
    Write-Host "  Komprimiere..." -ForegroundColor Gray
    Compress-Archive -Path "$tempBackupDir\*" -DestinationPath $zipPath -CompressionLevel Optimal -Force
    
    # Lösche temporäres Verzeichnis
    Remove-Item $tempBackupDir -Recurse -Force
    
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Host "  OK: ZIP-Archiv erstellt" -ForegroundColor Green
    Write-Host "      Dateien: $fileCount" -ForegroundColor Gray
    if ($errorCount -gt 0) {
        Write-Host "      Fehler: $errorCount" -ForegroundColor Yellow
    }
    Write-Host "      Größe: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Gray
    
} catch {
    Write-Host "  FEHLER: Fehler beim Erstellen des ZIP-Archivs: $_" -ForegroundColor Red
    if (Test-Path $tempBackupDir) {
        Remove-Item $tempBackupDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

# 6. Kopiere ZIP in Cloud-Ordner
Write-Host ""
Write-Host "[6/6] Kopiere Backup in Cloud-Ordner..." -ForegroundColor Yellow

try {
    Copy-Item -Path $zipPath -Destination $cloudZipPath -Force
    $cloudZipSize = (Get-Item $cloudZipPath).Length / 1MB
    Write-Host "  OK: Backup in Cloud kopiert" -ForegroundColor Green
    Write-Host "      Cloud-Datei: $cloudZipPath" -ForegroundColor Gray
    Write-Host "      Größe: $([math]::Round($cloudZipSize, 2)) MB" -ForegroundColor Gray
} catch {
    Write-Host "  FEHLER: Fehler beim Kopieren in Cloud: $_" -ForegroundColor Red
    Write-Host "  Lokales Backup bleibt erhalten: $zipPath" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BACKUP ERFOLGREICH ABGESCHLOSSEN" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lokales Backup:  $zipPath" -ForegroundColor Cyan
Write-Host "Cloud-Backup:    $cloudZipPath" -ForegroundColor Cyan
Write-Host "Zeitstempel:     $timestamp" -ForegroundColor Cyan
Write-Host "Dateien:        $fileCount" -ForegroundColor Cyan
Write-Host "Größe:          $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "HINWEIS: Google Drive synchronisiert automatisch die Datei in die Cloud." -ForegroundColor Yellow
Write-Host "         Bitte warten Sie, bis die Synchronisation abgeschlossen ist." -ForegroundColor Yellow
Write-Host ""

