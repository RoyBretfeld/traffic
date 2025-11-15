#!/usr/bin/env pwsh
# Synchronisiert Projekt zu BEIDEN Zielpfaden (H: und G: Cloud)
# Inkl. Datenbank-Dateien und System-Daten

param(
    [ValidateSet("to", "from")]
    [string]$Direction = "to"
)

$SourcePath = "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$TargetPathH = "H:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$TargetPathG = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

if (-not (Test-Path $SourcePath)) {
    Write-Host "FEHLER: Quellpfad nicht gefunden: $SourcePath" -ForegroundColor Red
    exit 1
}

# Code-Dateien
$FilesToSync = @(
    "routes\workflow_api.py",
    "routes\engine_api.py",
    "routes\tourplan_match.py",
    "routes\upload_csv.py",
    "routes\health_check.py",
    "services\sector_planner.py",
    "services\pirna_clusterer.py",
    "services\osrm_client.py",
    "frontend\index.html",
    "db\schema.py",
    "start_server.py",
    "app_startup.py",
    "config\tour_ignore_list.json",
    "config.env",
    "docs\database_schema.sql",
    "docs\CUSTOMER_SYNONYMS.md",
    "docs\DATABASE_SCHEMA.md",
    "docs\Architecture.md",
    "docs\PROJECT_STATUS.md",
    "docs\STATUS_AKTUELL.md",
    "docs\SPEICHERORTE_UND_STRUKTUR.md",
    "docs\PLAN_MULTI_MONITOR_ROUTEN_EXPORT.md",
    "docs\CHANGELOG_2025-11-06.md",
    "docs\PROBLEM_OSRM_POLYGONE.md",
    "docs\FIX_ROUTE_DETAILS_404.md",
    "docs\FIX_APPLIED_OSRM_TIMEOUT.md",
    "docs\STATISTIK_NAV_ADMIN_PLAN.md",
    "docs\licensing-plan.md",
    "docs\PLAENE_UEBERSICHT.md",
    "docs\ARCHITEKTUR_KOMPLETT.md",
    "docs\UMBAU_REACT_PLAN.md",
    "docs\DEPLOYMENT_AI_OPS_PLAN.md",
    "docs\EXPORT_LIVE_DATA_PLAN.md"
)

# Datenbank-Dateien (ohne .shm und .wal - diese können gesperrt sein)
$DatabaseFiles = @(
    "data\traffic.db",
    "data\customers.db",
    "data\llm_monitoring.db",
    "data\address_corrections.sqlite3"
)

# Verzeichnisse die komplett synchronisiert werden sollen
$DirectoriesToSync = @(
    "data\backups",
    "data\archive",
    "data\temp",
    "docs\archive",
    "scripts\legacy",
    "config",
    "ZIP"
)

# Dateien/Patterns die IGNORIERT werden sollen
$IgnorePatterns = @(
    "*.shm",           # SQLite Shared Memory (gesperrt wenn DB offen)
    "*.wal",           # SQLite Write-Ahead Log (gesperrt wenn DB offen)
    "desktop.ini",     # Windows-Systemdatei
    "*.tmp",           # Temporäre Dateien
    "*.log"            # Log-Dateien (optional, falls zu groß)
)

function Copy-FileSafe {
    param(
        [string]$SourceFile,
        [string]$TargetFile,
        [string]$RelativePath
    )
    
    try {
        # Prüfe ob Datei gerade verwendet wird (gesperrt)
        $fileInfo = Get-Item $SourceFile -ErrorAction Stop
        $fileStream = $null
        
        try {
            # Versuche Datei zum Lesen zu öffnen
            $fileStream = [System.IO.File]::Open($SourceFile, 'Open', 'Read', 'None')
            $fileStream.Close()
            $fileStream = $null
            
            # Erstelle Ziel-Verzeichnis falls nötig
            $targetDir = Split-Path $TargetFile -Parent
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            
            # Kopiere Datei (inkl. versteckte/System-Dateien)
            Copy-Item -Path $SourceFile -Destination $TargetFile -Force -ErrorAction Stop
            Write-Host "  OK: $RelativePath" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "  GESPERRT: $RelativePath (wird übersprungen)" -ForegroundColor Yellow
            return $false
        }
        finally {
            if ($fileStream) {
                $fileStream.Close()
                $fileStream = $null
            }
        }
    }
    catch {
        Write-Host "  FEHLER: $RelativePath - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Sync-Directory {
    param(
        [string]$SourceDir,
        [string]$TargetDir,
        [string]$RelativePath
    )
    
    if (-not (Test-Path $SourceDir)) {
        return 0
    }
    
    $copied = 0
    
    # Erstelle Ziel-Verzeichnis
    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }
    
    # Kopiere alle Dateien im Verzeichnis (rekursiv, inkl. versteckte Dateien)
    $items = Get-ChildItem -Path $SourceDir -Recurse -File -Force
    
    foreach ($item in $items) {
        # Relativer Pfad vom Source-Verzeichnis aus
        $relativeFromSourceDir = $item.FullName.Substring($SourceDir.Length + 1)
        
        # Prüfe Ignore-Patterns
        $shouldIgnore = $false
        foreach ($pattern in $IgnorePatterns) {
            if ($item.Name -like $pattern) {
                $shouldIgnore = $true
                break
            }
        }
        
        if ($shouldIgnore) {
            continue
        }
        
        # Ziel-Datei im Ziel-Verzeichnis erstellen
        $targetFile = Join-Path $TargetDir $relativeFromSourceDir
        
        # Relativer Pfad für Anzeige (vom Projekt-Root)
        $displayPath = $item.FullName.Substring($SourcePath.Length + 1)
        
        if (Copy-FileSafe -SourceFile $item.FullName -TargetFile $targetFile -RelativePath $displayPath) {
            $copied++
        }
    }
    
    return $copied
}

function Sync-ToTarget {
    param([string]$Target, [string]$Name)
    
    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    
    if (-not (Test-Path $Target)) {
        New-Item -ItemType Directory -Path $Target -Force | Out-Null
        Write-Host "Zielpfad erstellt: $Target" -ForegroundColor Yellow
    }
    
    $totalCopied = 0
    
    # 1. Code-Dateien synchronisieren
    Write-Host "  Code-Dateien..." -ForegroundColor White
    foreach ($file in $FilesToSync) {
        $sourceFile = Join-Path $SourcePath $file
        $targetFile = Join-Path $Target $file
        
        if (Test-Path $sourceFile) {
            if (Copy-FileSafe -SourceFile $sourceFile -TargetFile $targetFile -RelativePath $file) {
                $totalCopied++
            }
        }
    }
    
    # 2. Datenbank-Dateien synchronisieren
    Write-Host "  Datenbank-Dateien..." -ForegroundColor White
    foreach ($dbFile in $DatabaseFiles) {
        $sourceFile = Join-Path $SourcePath $dbFile
        $targetFile = Join-Path $Target $dbFile
        
        if (Test-Path $sourceFile) {
            if (Copy-FileSafe -SourceFile $sourceFile -TargetFile $targetFile -RelativePath $dbFile) {
                $totalCopied++
            }
        }
    }
    
    # 3. Verzeichnisse synchronisieren
    Write-Host "  Verzeichnisse..." -ForegroundColor White
    foreach ($dir in $DirectoriesToSync) {
        $sourceDir = Join-Path $SourcePath $dir
        $targetDir = Join-Path $Target $dir
        
        $dirCopied = Sync-Directory -SourceDir $sourceDir -TargetDir $targetDir -RelativePath $dir
        $totalCopied += $dirCopied
        if ($dirCopied -gt 0) {
            Write-Host "    $dir`: $dirCopied Dateien" -ForegroundColor Gray
        }
    }
    
    Write-Host "Ergebnis: $totalCopied Dateien kopiert" -ForegroundColor Green
    return $totalCopied
}

function Sync-FromSource {
    param([string]$Source, [string]$Name)
    
    Write-Host ""
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    
    if (-not (Test-Path $Source)) {
        Write-Host "  Quelle nicht gefunden: $Source (wird übersprungen)" -ForegroundColor Yellow
        return 0
    }
    
    $totalCopied = 0
    
    # 1. Code-Dateien synchronisieren
    Write-Host "  Code-Dateien..." -ForegroundColor White
    foreach ($file in $FilesToSync) {
        $sourceFile = Join-Path $Source $file
        $targetFile = Join-Path $SourcePath $file
        
        if (Test-Path $sourceFile) {
            if (Copy-FileSafe -SourceFile $sourceFile -TargetFile $targetFile -RelativePath $file) {
                $totalCopied++
            }
        }
    }
    
    # 2. Datenbank-Dateien synchronisieren
    Write-Host "  Datenbank-Dateien..." -ForegroundColor White
    foreach ($dbFile in $DatabaseFiles) {
        $sourceFile = Join-Path $Source $dbFile
        $targetFile = Join-Path $SourcePath $dbFile
        
        if (Test-Path $sourceFile) {
            if (Copy-FileSafe -SourceFile $sourceFile -TargetFile $targetFile -RelativePath $dbFile) {
                $totalCopied++
            }
        }
    }
    
    # 3. Verzeichnisse synchronisieren
    Write-Host "  Verzeichnisse..." -ForegroundColor White
    foreach ($dir in $DirectoriesToSync) {
        $sourceDir = Join-Path $Source $dir
        $targetDir = Join-Path $SourcePath $dir
        
        $dirCopied = Sync-Directory -SourceDir $sourceDir -TargetDir $targetDir -RelativePath $dir
        $totalCopied += $dirCopied
        if ($dirCopied -gt 0) {
            Write-Host "    $dir`: $dirCopied Dateien" -ForegroundColor Gray
        }
    }
    
    Write-Host "Ergebnis: $totalCopied Dateien kopiert" -ForegroundColor Green
    return $totalCopied
}

Write-Host "=== FAMO TrafficApp - Synchronisation ===" -ForegroundColor Cyan
Write-Host "Quelle: $SourcePath" -ForegroundColor White
Write-Host "Richtung: $Direction" -ForegroundColor White
Write-Host ""

if ($Direction -eq "to") {
    Write-Host "Synchronisiere zu BEIDEN Zielen:" -ForegroundColor Yellow
    $resultH = Sync-ToTarget -Target $TargetPathH -Name "H: Laufwerk"
    $resultG = Sync-ToTarget -Target $TargetPathG -Name "G: Cloud"
    Write-Host ""
    Write-Host "Zusammenfassung:" -ForegroundColor Cyan
    Write-Host "  H: $resultH Dateien" -ForegroundColor White
    Write-Host "  G: $resultG Dateien" -ForegroundColor White
} else {
    Write-Host "Synchronisiere von BEIDEN Quellen zurück:" -ForegroundColor Yellow
    Write-Host "  (Neueste Dateien werden bevorzugt)" -ForegroundColor Gray
    $resultG = Sync-FromSource -Source $TargetPathG -Name "G: Cloud"
    $resultH = Sync-FromSource -Source $TargetPathH -Name "H: Laufwerk"
    Write-Host ""
    Write-Host "Zusammenfassung:" -ForegroundColor Cyan
    Write-Host "  G: $resultG Dateien" -ForegroundColor White
    Write-Host "  H: $resultH Dateien" -ForegroundColor White
}

Write-Host ""
Write-Host "Synchronisation abgeschlossen!" -ForegroundColor Green
