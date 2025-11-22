# Aktuelles Backup von heute erstellen
# Erstellt: ZIP-Archiv mit allen wichtigen Dateien
# Kopiert: In Cloud-Ordner für automatische Synchronisation
#
# Nutzung:
#   .\scripts\backup_today.ps1

$ErrorActionPreference = "Stop"

# Pfade
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$BackupDir = Join-Path $ProjectRoot "backups"
$CloudBackupDir = Join-Path $CloudRoot "backups"

# Zeitstempel
$date = Get-Date -Format "yyyy-MM-dd"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$zipName = "backup_$date.zip"
$zipPath = Join-Path $BackupDir $zipName
$cloudZipPath = Join-Path $CloudBackupDir $zipName

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BACKUP VON HEUTE ERSTELLEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Projekt:      $ProjectRoot" -ForegroundColor Gray
Write-Host "Cloud:        $CloudRoot" -ForegroundColor Gray
Write-Host "Backup-Datei: $zipName" -ForegroundColor Gray
Write-Host ""

# 1. Prüfe Cloud-Ordner
Write-Host "[1/5] Prüfe Cloud-Ordner..." -ForegroundColor Yellow
if (-not (Test-Path $CloudRoot)) {
    Write-Host "  FEHLER: Cloud-Ordner existiert nicht!" -ForegroundColor Red
    Write-Host "  Pfad: $CloudRoot" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Cloud-Ordner gefunden" -ForegroundColor Green

# 2. Erstelle Backup-Verzeichnisse
Write-Host ""
Write-Host "[2/5] Erstelle Backup-Verzeichnisse..." -ForegroundColor Yellow
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

# 3. Git-Status prüfen
Write-Host ""
Write-Host "[3/5] Prüfe Git-Status..." -ForegroundColor Yellow
try {
    $gitStatus = git status --short 2>$null
    if ($gitStatus) {
        Write-Host "  INFO: Uncommitted Änderungen vorhanden" -ForegroundColor Yellow
    } else {
        Write-Host "  OK: Keine uncommitted Änderungen" -ForegroundColor Green
    }
} catch {
    Write-Host "  INFO: Git nicht verfügbar" -ForegroundColor Gray
}

# 4. Erstelle Liste der zu sichernden Dateien/Ordner
Write-Host ""
Write-Host "[4/5] Erstelle Datei-Liste..." -ForegroundColor Yellow

# Wichtige Verzeichnisse
$ImportantDirs = @(
    "backend",
    "frontend",
    "config",
    "Regeln",
    "Global",
    "docs",
    "scripts",
    "db",
    "common",
    "repositories",
    "services",
    "routes",
    "tests",
    "ingest",
    "tools",
    "data"
)

# Wichtige Root-Dateien
$ImportantFiles = @(
    "*.md",
    "*.py",
    "*.ps1",
    "*.bat",
    "*.sh",
    "*.json",
    "*.txt",
    "*.toml",
    "*.yml",
    "*.yaml",
    ".cursorrules",
    ".gitignore",
    "requirements.txt",
    "start_server.py"
)

# Sammle alle Dateien
$itemsToBackup = @()

foreach ($dir in $ImportantDirs) {
    $dirPath = Join-Path $ProjectRoot $dir
    if (Test-Path $dirPath) {
        $itemsToBackup += $dirPath
    }
}

foreach ($pattern in $ImportantFiles) {
    $files = Get-ChildItem -Path $ProjectRoot -Filter $pattern -File -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        $itemsToBackup += $file.FullName
    }
}

Write-Host "  OK: $($itemsToBackup.Count) Dateien/Ordner gefunden" -ForegroundColor Green

# 5. Erstelle ZIP-Archiv
Write-Host ""
Write-Host "[5/5] Erstelle ZIP-Archiv..." -ForegroundColor Yellow
Write-Host "  Datei: $zipName" -ForegroundColor Gray
Write-Host "  Dies kann einige Minuten dauern..." -ForegroundColor Gray

try {
    # Lösche alte ZIP-Datei falls vorhanden
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    # Erstelle ZIP mit Compress-Archive
    $fileCount = 0
    $errorCount = 0
    
    # Erstelle temporäres Verzeichnis
    $tempBackupDir = Join-Path $env:TEMP "backup_temp_$timestamp"
    if (Test-Path $tempBackupDir) {
        Remove-Item $tempBackupDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempBackupDir -Force | Out-Null
    
    Write-Host "  Kopiere Dateien..." -ForegroundColor Gray
    
    # Ausschlüsse
    $ExcludeDirs = @("venv", "__pycache__", ".git", "node_modules", ".pytest_cache", ".mypy_cache", "chroma_db", "dist", "build", ".idea", ".vscode", "backups", "ZIP", "temp", "tmp", "logs")
    $ExcludeFiles = @("*.pyc", "*.pyo", "*.pyd", ".DS_Store", "Thumbs.db", "desktop.ini", "*.swp", "*.swo", "*~", "*.log")
    
    foreach ($item in $itemsToBackup) {
        try {
            if (-not (Test-Path $item)) {
                continue
            }
            
            $relativePath = $item.Replace($ProjectRoot + "\", "").Replace($ProjectRoot + "/", "")
            
            # Prüfe Ausschlüsse
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
            
            foreach ($excludeFile in $ExcludeFiles) {
                if ($relativePath -like $excludeFile) {
                    $shouldExclude = $true
                    break
                }
            }
            if ($shouldExclude) {
                continue
            }
            
            $targetPath = Join-Path $tempBackupDir $relativePath
            $targetDir = Split-Path $targetPath -Parent
            
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            
            if ((Get-Item $item) -is [System.IO.DirectoryInfo]) {
                # Verzeichnis: Kopiere rekursiv
                $files = Get-ChildItem -Path $item -Recurse -File -ErrorAction SilentlyContinue
                foreach ($file in $files) {
                    $fileRelativePath = $file.FullName.Replace($ProjectRoot + "\", "").Replace($ProjectRoot + "/", "")
                    
                    # Prüfe Ausschlüsse
                    $shouldExclude = $false
                    foreach ($excludeDir in $ExcludeDirs) {
                        if ($fileRelativePath -like "*\$excludeDir\*" -or $fileRelativePath -like "*/$excludeDir/*") {
                            $shouldExclude = $true
                            break
                        }
                    }
                    if ($shouldExclude) {
                        continue
                    }
                    
                    foreach ($excludeFile in $ExcludeFiles) {
                        if ($fileRelativePath -like $excludeFile) {
                            $shouldExclude = $true
                            break
                        }
                    }
                    if ($shouldExclude) {
                        continue
                    }
                    
                    try {
                        $fileTargetPath = Join-Path $tempBackupDir $fileRelativePath
                        $fileTargetDir = Split-Path $fileTargetPath -Parent
                        if (-not (Test-Path $fileTargetDir)) {
                            New-Item -ItemType Directory -Path $fileTargetDir -Force | Out-Null
                        }
                        Copy-Item -Path $file.FullName -Destination $fileTargetPath -Force -ErrorAction Stop
                        $fileCount++
                    } catch {
                        $errorCount++
                    }
                }
            } else {
                # Einzelne Datei
                try {
                    Copy-Item -Path $item -Destination $targetPath -Force -ErrorAction Stop
                    $fileCount++
                } catch {
                    $errorCount++
                }
            }
        } catch {
            $errorCount++
        }
    }
    
    # Erstelle ZIP
    Write-Host "  Komprimiere..." -ForegroundColor Gray
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
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
Write-Host "BACKUP ERFOLGREICH ERSTELLT" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lokales Backup:  $zipPath" -ForegroundColor Cyan
Write-Host "Cloud-Backup:    $cloudZipPath" -ForegroundColor Cyan
Write-Host "Datum:           $date" -ForegroundColor Cyan
Write-Host "Zeitstempel:     $timestamp" -ForegroundColor Cyan
Write-Host "Dateien:        $fileCount" -ForegroundColor Cyan
Write-Host "Größe:          $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "HINWEIS: Google Drive synchronisiert automatisch die Datei in die Cloud." -ForegroundColor Yellow
Write-Host ""

