#!/usr/bin/env pwsh
# Verifiziert ob die Synchronisation korrekt war
# Vergleicht Dateien zwischen E:, H: und G:

$SourcePath = "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$TargetPathH = "H:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$TargetPathG = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

Write-Host "=== Synchronisations-Verifizierung ===" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob alle Pfade existieren
$pathsOk = $true
if (-not (Test-Path $SourcePath)) {
    Write-Host "FEHLER: Quellpfad nicht gefunden: $SourcePath" -ForegroundColor Red
    $pathsOk = $false
}
if (-not (Test-Path $TargetPathH)) {
    Write-Host "FEHLER: H: Pfad nicht gefunden: $TargetPathH" -ForegroundColor Red
    $pathsOk = $false
}
if (-not (Test-Path $TargetPathG)) {
    Write-Host "FEHLER: G: Pfad nicht gefunden: $TargetPathG" -ForegroundColor Red
    $pathsOk = $false
}

if (-not $pathsOk) {
    exit 1
}

function Get-FileHash {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        return $null
    }
    
    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm SHA256 -ErrorAction Stop
        return $hash.Hash
    }
    catch {
        return "ERROR"
    }
}

function Compare-Files {
    param(
        [string]$SourceFile,
        [string]$TargetFileH,
        [string]$TargetFileG,
        [string]$RelativePath
    )
    
    $result = @{
        RelativePath = $RelativePath
        SourceExists = $false
        HExists = $false
        GExists = $false
        SourceHash = $null
        HHash = $null
        GHash = $null
        HMatch = $false
        GMatch = $false
    }
    
    # Prüfe Existenz
    $result.SourceExists = Test-Path $SourceFile
    $result.HExists = Test-Path $TargetFileH
    $result.GExists = Test-Path $TargetFileG
    
    if (-not $result.SourceExists) {
        return $result
    }
    
    # Berechne Hashes
    $result.SourceHash = Get-FileHash -FilePath $SourceFile
    
    if ($result.HExists) {
        $result.HHash = Get-FileHash -FilePath $TargetFileH
        $result.HMatch = ($result.SourceHash -eq $result.HHash)
    }
    
    if ($result.GExists) {
        $result.GHash = Get-FileHash -FilePath $TargetFileG
        $result.GMatch = ($result.SourceHash -eq $result.GHash)
    }
    
    return $result
}

# Dateien die verglichen werden sollen (aus Sync-Skript)
$FilesToCheck = @(
    "routes\workflow_api.py",
    "routes\engine_api.py",
    "services\sector_planner.py",
    "services\pirna_clusterer.py",
    "frontend\index.html",
    "db\schema.py",
    "start_server.py",
    "app_startup.py",
    "config\tour_ignore_list.json",
    "config.env",
    "docs\database_schema.sql",
    "docs\CUSTOMER_SYNONYMS.md"
)

$DatabaseFiles = @(
    "data\traffic.db",
    "data\customers.db",
    "data\llm_monitoring.db",
    "data\address_corrections.sqlite3"
)

$DirectoriesToCheck = @(
    "data\backups",
    "data\archive",
    "data\temp",
    "docs\archive",
    "scripts\legacy",
    "config"
)

Write-Host "Vergleiche Dateien..." -ForegroundColor Yellow
Write-Host ""

$allResults = @()
$totalFiles = 0
$identicalH = 0
$identicalG = 0
$missingH = 0
$missingG = 0
$differentH = 0
$differentG = 0

# 1. Code-Dateien
Write-Host "1. Code-Dateien..." -ForegroundColor Cyan
foreach ($file in $FilesToCheck) {
    $sourceFile = Join-Path $SourcePath $file
    $targetFileH = Join-Path $TargetPathH $file
    $targetFileG = Join-Path $TargetPathG $file
    
    $result = Compare-Files -SourceFile $sourceFile -TargetFileH $targetFileH -TargetFileG $targetFileG -RelativePath $file
    $allResults += $result
    $totalFiles++
    
    if ($result.SourceExists) {
        if (-not $result.HExists) {
            Write-Host "  FEHLT H: $file" -ForegroundColor Red
            $missingH++
        } elseif (-not $result.HMatch) {
            Write-Host "  UNTERSCHIEDLICH H: $file" -ForegroundColor Yellow
            $differentH++
        } else {
            $identicalH++
        }
        
        if (-not $result.GExists) {
            Write-Host "  FEHLT G: $file" -ForegroundColor Red
            $missingG++
        } elseif (-not $result.GMatch) {
            Write-Host "  UNTERSCHIEDLICH G: $file" -ForegroundColor Yellow
            $differentG++
        } else {
            $identicalG++
        }
    }
}

# 2. Datenbank-Dateien
Write-Host ""
Write-Host "2. Datenbank-Dateien..." -ForegroundColor Cyan
foreach ($file in $DatabaseFiles) {
    $sourceFile = Join-Path $SourcePath $file
    $targetFileH = Join-Path $TargetPathH $file
    $targetFileG = Join-Path $TargetPathG $file
    
    $result = Compare-Files -SourceFile $sourceFile -TargetFileH $targetFileH -TargetFileG $targetFileG -RelativePath $file
    $allResults += $result
    $totalFiles++
    
    if ($result.SourceExists) {
        if (-not $result.HExists) {
            Write-Host "  FEHLT H: $file" -ForegroundColor Red
            $missingH++
        } elseif (-not $result.HMatch) {
            Write-Host "  UNTERSCHIEDLICH H: $file" -ForegroundColor Yellow
            $differentH++
        } else {
            $identicalH++
        }
        
        if (-not $result.GExists) {
            Write-Host "  FEHLT G: $file" -ForegroundColor Red
            $missingG++
        } elseif (-not $result.GMatch) {
            Write-Host "  UNTERSCHIEDLICH G: $file" -ForegroundColor Yellow
            $differentG++
        } else {
            $identicalG++
        }
    }
}

# 3. Verzeichnisse (Stichprobe - nicht alle Dateien)
Write-Host ""
Write-Host "3. Verzeichnisse (Stichprobe)..." -ForegroundColor Cyan
foreach ($dir in $DirectoriesToCheck) {
    $sourceDir = Join-Path $SourcePath $dir
    $targetDirH = Join-Path $TargetPathH $dir
    $targetDirG = Join-Path $TargetPathG $dir
    
    if (-not (Test-Path $sourceDir)) {
        continue
    }
    
    # Prüfe nur erste 5 Dateien pro Verzeichnis (für Performance)
    $sourceFiles = Get-ChildItem -Path $sourceDir -Recurse -File -Force | Select-Object -First 5
    
    foreach ($sourceFile in $sourceFiles) {
        $relativePath = $sourceFile.FullName.Substring($SourcePath.Length + 1)
        $targetFileH = Join-Path $TargetPathH $relativePath
        $targetFileG = Join-Path $TargetPathG $relativePath
        
        $result = Compare-Files -SourceFile $sourceFile.FullName -TargetFileH $targetFileH -TargetFileG $targetFileG -RelativePath $relativePath
        $allResults += $result
        $totalFiles++
        
        if ($result.SourceExists) {
            if (-not $result.HExists) {
                Write-Host "  FEHLT H: $relativePath" -ForegroundColor Red
                $missingH++
            } elseif (-not $result.HMatch) {
                Write-Host "  UNTERSCHIEDLICH H: $relativePath" -ForegroundColor Yellow
                $differentH++
            } else {
                $identicalH++
            }
            
            if (-not $result.GExists) {
                Write-Host "  FEHLT G: $relativePath" -ForegroundColor Red
                $missingG++
            } elseif (-not $result.GMatch) {
                Write-Host "  UNTERSCHIEDLICH G: $relativePath" -ForegroundColor Yellow
                $differentG++
            } else {
                $identicalG++
            }
        }
    }
}

# Zusammenfassung
Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host "Geprüfte Dateien: $totalFiles" -ForegroundColor White
Write-Host ""
Write-Host "H: Laufwerk:" -ForegroundColor Cyan
Write-Host "  ✅ Identisch: $identicalH" -ForegroundColor Green
Write-Host "  ⚠️  Unterschiedlich: $differentH" -ForegroundColor $(if ($differentH -gt 0) { "Yellow" } else { "Green" })
Write-Host "  ❌ Fehlend: $missingH" -ForegroundColor $(if ($missingH -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "G: Cloud:" -ForegroundColor Cyan
Write-Host "  ✅ Identisch: $identicalG" -ForegroundColor Green
Write-Host "  ⚠️  Unterschiedlich: $differentG" -ForegroundColor $(if ($differentG -gt 0) { "Yellow" } else { "Green" })
Write-Host "  ❌ Fehlend: $missingG" -ForegroundColor $(if ($missingG -gt 0) { "Red" } else { "Green" })

if ($differentH -eq 0 -and $differentG -eq 0 -and $missingH -eq 0 -and $missingG -eq 0) {
    Write-Host ""
    Write-Host "✅ ALLE DATEIEN SIND IDENTISCH!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "⚠️  Es wurden Unterschiede gefunden!" -ForegroundColor Yellow
    exit 1
}

