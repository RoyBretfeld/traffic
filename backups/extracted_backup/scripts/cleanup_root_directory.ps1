#!/usr/bin/env pwsh
# Aufräumen des Root-Verzeichnisses
# Verschiebt Dateien in passende Unterverzeichnisse

$ErrorActionPreference = "Continue"

# Projekt-Root bestimmen (aus scripts/ Verzeichnis heraus)
if ($PSScriptRoot) {
    $ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
} else {
    # Fallback: Aktuelles Verzeichnis wenn direkt aufgerufen
    $ProjectRoot = Get-Location
}
Set-Location $ProjectRoot
$ProjectRoot = (Get-Location).Path

Write-Host "=== Root-Verzeichnis Aufräumen ===" -ForegroundColor Cyan
Write-Host "Projekt-Root: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Verzeichnisse erstellen falls nicht vorhanden
$Directories = @{
    "scripts/legacy" = "Alte Skripte die nicht mehr aktiv verwendet werden"
    "docs/archive" = "Archivierte Dokumentation"
    "data/temp" = "Temporäre Dateien"
    "data/archive" = "Archivierte Daten"
    "tools/legacy" = "Legacy-Tools"
}

foreach ($dir in $Directories.Keys) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "Erstellt: $dir" -ForegroundColor Yellow
    }
}

# Dateien die im Root bleiben SOLLEN
$KeepInRoot = @(
    "README.md",
    "README_BACKUP.md",
    "CHANGELOG.md",
    "CURSOR_RULES.md",
    "requirements.txt",
    "pyproject.toml",
    "docker-compose.yml",
    "Dockerfile",
    "config.env",
    "env.example",
    "start_server.py",
    "app_startup.py",
    "settings.py",
    "logging_setup.py",
    "comprehensive_test_suite.py",
    "___START_HIER_ARBEITSRECHNER.md",
    "___START_HIER_MORGEN_2025-01-10.md",
    "Traffic.code-workspace",
    ".gitignore",
    ".git",
    "venv",
    "__pycache__"
)

# Kategorisierung der Dateien
$FileMoves = @()

# Python-Skripte → scripts/legacy (außer wichtige die im Root bleiben)
$PythonScripts = Get-ChildItem -Path $ProjectRoot -Filter "*.py" -File | Where-Object {
    $_.Name -notin @("start_server.py", "app_startup.py", "settings.py", "logging_setup.py", "comprehensive_test_suite.py")
}

foreach ($file in $PythonScripts) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "scripts\legacy\$($file.Name)"
        Category = "Python-Skript"
    }
}

# Test-Datenbanken → data/temp
$TestDBs = Get-ChildItem -Path $ProjectRoot -Filter "*.db" -File | Where-Object {
    $_.Name -match "^(test|tmp|temp)" -or $_.Name -eq "tmp_manual.db"
}

foreach ($file in $TestDBs) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "data\temp\$($file.Name)"
        Category = "Test-Datenbank"
    }
}

# Test-CSV-Dateien → data/temp
$TestCSVs = Get-ChildItem -Path $ProjectRoot -Filter "test*.csv" -File

foreach ($file in $TestCSVs) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "data\temp\$($file.Name)"
        Category = "Test-CSV"
    }
}

# Test-HTML → data/temp
$TestHTMLs = Get-ChildItem -Path $ProjectRoot -Filter "test*.html" -File

foreach ($file in $TestHTMLs) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "data\temp\$($file.Name)"
        Category = "Test-HTML"
    }
}

# Markdown-Dokumentation (außer README, CHANGELOG, CURSOR_RULES) → docs/archive
$MarkdownFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.md" -File | Where-Object {
    $_.Name -notin @("README.md", "README_BACKUP.md", "CHANGELOG.md", "CURSOR_RULES.md", "___START_HIER_ARBEITSRECHNER.md", "___START_HIER_MORGEN_2025-01-10.md")
}

foreach ($file in $MarkdownFiles) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "docs\archive\$($file.Name)"
        Category = "Dokumentation"
    }
}

# ZIP-Dateien → data/archive
$ZipFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.zip" -File

foreach ($file in $ZipFiles) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "data\archive\$($file.Name)"
        Category = "ZIP-Archiv"
    }
}

# JSON-Dateien im Root (außer cursorTasks.json falls wichtig) → config/dynamic
$JsonFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.json" -File | Where-Object {
    $_.Name -ne "cursorTasks.json"  # Kann im Root bleiben falls benötigt
}

foreach ($file in $JsonFiles) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "config\dynamic\$($file.Name)"
        Category = "JSON-Konfiguration"
    }
}

# TXT-Dateien → docs/archive
$TxtFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.txt" -File | Where-Object {
    $_.Name -ne "requirements.txt"  # requirements.txt bleibt im Root
}

foreach ($file in $TxtFiles) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "docs\archive\$($file.Name)"
        Category = "Text-Datei"
    }
}

# PNG-Dateien → docs/archive
$PngFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.png" -File

foreach ($file in $PngFiles) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "docs\archive\$($file.Name)"
        Category = "Bild-Datei"
    }
}

# Patch-Dateien → docs/archive
$PatchFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.patch" -File

foreach ($file in $PatchFiles) {
    $FileMoves += @{
        Source = $file.FullName
        Target = Join-Path $ProjectRoot "docs\archive\$($file.Name)"
        Category = "Patch-Datei"
    }
}

# Altes backup-Verzeichnis → data/backups/legacy
if (Test-Path (Join-Path $ProjectRoot "backup")) {
    $backupDir = Join-Path $ProjectRoot "backup"
    $legacyBackupDir = Join-Path $ProjectRoot "data\backups\legacy"
    
    if (-not (Test-Path $legacyBackupDir)) {
        New-Item -ItemType Directory -Path $legacyBackupDir -Force | Out-Null
    }
    
    Write-Host "Verschiebe altes backup-Verzeichnis..." -ForegroundColor Yellow
    
    # Verschiebe nur existierende Dateien
    $backupItems = Get-ChildItem -Path $backupDir -Recurse -File -ErrorAction SilentlyContinue
    
    if ($backupItems) {
        foreach ($item in $backupItems) {
            $relativePath = $item.FullName.Substring($backupDir.Length + 1)
            $targetPath = Join-Path $legacyBackupDir $relativePath
            
            $targetParent = Split-Path $targetPath -Parent
            if (-not (Test-Path $targetParent)) {
                New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
            }
            
            try {
                if (Test-Path $item.FullName) {
                    Move-Item -Path $item.FullName -Destination $targetPath -Force -ErrorAction Stop
                    Write-Host "  OK: backup\$relativePath" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "  FEHLER: backup\$relativePath - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    # Verschiebe Verzeichnisse
    $backupDirs = Get-ChildItem -Path $backupDir -Directory -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
    
    foreach ($dir in $backupDirs) {
        $relativePath = $dir.FullName.Substring($backupDir.Length + 1)
        $targetPath = Join-Path $legacyBackupDir $relativePath
        
        try {
            if (Test-Path $dir.FullName) {
                $items = Get-ChildItem -Path $dir.FullName -Recurse -ErrorAction SilentlyContinue
                if ($items.Count -eq 0) {
                    # Leeres Verzeichnis
                    if (-not (Test-Path $targetPath)) {
                        New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
                    }
                    Remove-Item -Path $dir.FullName -Force -ErrorAction SilentlyContinue
                }
            }
        }
        catch {
            # Ignoriere Fehler bei Verzeichnissen
        }
    }
    
    # Lösche leeres backup-Verzeichnis
    try {
        $remainingItems = Get-ChildItem -Path $backupDir -Recurse -ErrorAction SilentlyContinue
        if ($null -eq $remainingItems -or $remainingItems.Count -eq 0) {
            Remove-Item -Path $backupDir -Force -ErrorAction Stop
            Write-Host "Altes backup-Verzeichnis entfernt" -ForegroundColor Green
        } else {
            Write-Host "Backup-Verzeichnis enthält noch $($remainingItems.Count) Elemente" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Konnte backup-Verzeichnis nicht entfernen: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Zeige Zusammenfassung
Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host "Gefundene Dateien zum Verschieben: $($FileMoves.Count)" -ForegroundColor White
Write-Host ""

if ($FileMoves.Count -gt 0) {
    $byCategory = $FileMoves | Group-Object -Property Category
    foreach ($group in $byCategory) {
        Write-Host "  $($group.Name): $($group.Count) Dateien" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "Beispiele:" -ForegroundColor Cyan
    $examples = $FileMoves | Select-Object -First 5
    foreach ($ex in $examples) {
        $sourceName = [System.IO.Path]::GetFileName($ex.Source)
        $targetName = $ex.Target.Substring($ProjectRoot.Length + 1)
        Write-Host "  $sourceName → $targetName" -ForegroundColor Gray
    }
    if ($FileMoves.Count -gt 5) {
        Write-Host "  ... und $($FileMoves.Count - 5) weitere" -ForegroundColor Gray
    }
}

if ($FileMoves.Count -eq 0) {
    Write-Host ""
    Write-Host "Keine Dateien zum Verschieben gefunden!" -ForegroundColor Green
    exit 0
}

# Bestätigung (automatisch wenn Parameter gesetzt)
$autoConfirm = $false
if ($args -contains "-AutoConfirm" -or $args -contains "-y") {
    $autoConfirm = $true
    Write-Host ""
    Write-Host "Automatische Bestätigung aktiviert - verschiebe Dateien..." -ForegroundColor Yellow
} else {
    Write-Host ""
    $confirm = Read-Host "Möchten Sie diese Dateien verschieben? (j/n, oder -AutoConfirm für automatisch)"
    if ($confirm -ne "j" -and $confirm -ne "J" -and $confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Abgebrochen." -ForegroundColor Yellow
        Write-Host "Tipp: Verwenden Sie -AutoConfirm Parameter für automatische Ausführung" -ForegroundColor Gray
        exit 0
    }
}

# Verschiebe Dateien
Write-Host ""
Write-Host "Verschiebe Dateien..." -ForegroundColor Cyan

$moved = 0
$errors = 0
$skipped = 0

foreach ($move in $FileMoves) {
    $source = $move.Source
    $target = $move.Target
    $category = $move.Category
    
    if (-not (Test-Path $source)) {
        $skipped++
        continue
    }
    
    # Prüfe ob Ziel bereits existiert
    if (Test-Path $target) {
        Write-Host "  ÜBERSPRUNGEN (existiert bereits): $([System.IO.Path]::GetFileName($source))" -ForegroundColor Yellow
        $skipped++
        continue
    }
    
    try {
        # Erstelle Ziel-Verzeichnis falls nötig
        $targetDir = Split-Path $target -Parent
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        
        Move-Item -Path $source -Destination $target -Force -ErrorAction Stop
        Write-Host "  OK [$category]: $([System.IO.Path]::GetFileName($source))" -ForegroundColor Green
        $moved++
    }
    catch {
        Write-Host "  FEHLER [$category]: $([System.IO.Path]::GetFileName($source)) - $($_.Exception.Message)" -ForegroundColor Red
        $errors++
    }
}

Write-Host ""
Write-Host "=== Ergebnis ===" -ForegroundColor Cyan
Write-Host "Verschoben: $moved" -ForegroundColor Green
Write-Host "Übersprungen: $skipped" -ForegroundColor Yellow
Write-Host "Fehler: $errors" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "Aufräumen abgeschlossen!" -ForegroundColor Green

