# 🔄 Interaktive Synchronisation
# 
# Fragt nach Quell- und Zielpfad und synchronisiert Dateien
#
# Nutzung:
#   .\scripts\___sync_interaktiv.ps1
#
# Oder aus Projekt-Root:
#   powershell -ExecutionPolicy Bypass -File scripts\___sync_interaktiv.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Interaktive Synchronisation ===" -ForegroundColor Cyan
Write-Host ""

# Aktueller Pfad als Vorschlag
$CurrentPath = (Get-Location).Path

# Quellpfad abfragen
Write-Host "📂 Quellpfad (von wo synchronisieren?):" -ForegroundColor Yellow
Write-Host "   Vorschlag: $CurrentPath" -ForegroundColor Gray
$SourceRoot = Read-Host "   Eingabe (Enter für Vorschlag)"

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    $SourceRoot = $CurrentPath
}

# Normalisiere Pfad
$SourceRoot = $SourceRoot.Trim('"').Trim()
if (-not $SourceRoot.EndsWith('\')) {
    $SourceRoot = $SourceRoot + '\'
}

# Prüfe ob Quellpfad existiert
if (-not (Test-Path $SourceRoot)) {
    Write-Host ""
    Write-Host "❌ FEHLER: Quellpfad existiert nicht!" -ForegroundColor Red
    Write-Host "   $SourceRoot" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ Quellpfad: $SourceRoot" -ForegroundColor Green
Write-Host ""

# Zielpfad abfragen
Write-Host "📂 Zielpfad (wohin synchronisieren?):" -ForegroundColor Yellow
Write-Host "   Beispiele:" -ForegroundColor Gray
Write-Host "   - G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0" -ForegroundColor Gray
Write-Host "   - H:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0" -ForegroundColor Gray
$TargetRoot = Read-Host "   Eingabe"

if ([string]::IsNullOrWhiteSpace($TargetRoot)) {
    Write-Host ""
    Write-Host "❌ FEHLER: Zielpfad ist leer!" -ForegroundColor Red
    exit 1
}

# Normalisiere Pfad
$TargetRoot = $TargetRoot.Trim('"').Trim()
if (-not $TargetRoot.EndsWith('\')) {
    $TargetRoot = $TargetRoot + '\'
}

# Prüfe ob Zielpfad existiert
if (-not (Test-Path $TargetRoot)) {
    Write-Host ""
    Write-Host "⚠️  Zielpfad existiert nicht. Soll er erstellt werden? (J/N)" -ForegroundColor Yellow
    $CreateDir = Read-Host "   Eingabe"
    if ($CreateDir -eq "J" -or $CreateDir -eq "j" -or $CreateDir -eq "y" -or $CreateDir -eq "Y") {
        try {
            New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null
            Write-Host "✅ Zielpfad erstellt: $TargetRoot" -ForegroundColor Green
        } catch {
            Write-Host ""
            Write-Host "❌ FEHLER: Konnte Zielpfad nicht erstellen!" -ForegroundColor Red
            Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "❌ Abgebrochen: Zielpfad muss existieren!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Zielpfad: $TargetRoot" -ForegroundColor Green
Write-Host ""

# Synchronisations-Richtung abfragen
Write-Host "🔄 Synchronisations-Richtung:" -ForegroundColor Yellow
Write-Host "   1 = Quelle → Ziel (normale Synchronisation)" -ForegroundColor White
Write-Host "   2 = Ziel → Quelle (rückwärts)" -ForegroundColor White
Write-Host "   3 = Bidirektional (neuere Version gewinnt)" -ForegroundColor White
$Direction = Read-Host "   Eingabe (1/2/3, Standard: 1)"

if ([string]::IsNullOrWhiteSpace($Direction)) {
    $Direction = "1"
}

Write-Host ""

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
    "docs\TOUR_CALCULATION_AUDIT.md",
    "docs\LLM_ROUTE_RULES.md",
    "docs\MULTI_MONITOR_SUPPORT.md",
    "docs\TOUR_MANAGEMENT.md",
    "docs\98_MINUTEN_ROUTE_PROBLEM.md",
    "docs\PERFORMANCE_OPTIMIERUNG.md",
    "docs\API_ONLY_VERIFIZIERUNG.md",
    "docs\TOUR_IGNORE_LIST.md",
    "docs\W_ROUTE_ISSUES.md",
    "docs\BUGS_TO_FIX.md",
    "docs\CURSOR_KI_BETRIEBSORDNUNG.md",
    "docs\Architecture.md",
    "docs\ENDPOINT_FLOW.md",
    
    # Skripte
    "scripts\sync_to_cloud.ps1",
    "scripts\sync_from_cloud.ps1",
    "scripts\sync_diagnose.ps1",
    "scripts\sync_repair.ps1",
    "scripts\___sync_interaktiv.ps1"
)

Write-Host "=== Synchronisation startet ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle: $SourceRoot" -ForegroundColor Gray
Write-Host "Ziel:   $TargetRoot" -ForegroundColor Gray
Write-Host "Richtung: " -NoNewline -ForegroundColor Gray
switch ($Direction) {
    "1" { Write-Host "Quelle → Ziel" -ForegroundColor White }
    "2" { Write-Host "Ziel → Quelle" -ForegroundColor White }
    "3" { Write-Host "Bidirektional (neuere Version)" -ForegroundColor White }
}
Write-Host ""

$SyncedCount = 0
$SkippedCount = 0
$ErrorCount = 0

foreach ($File in $FilesToSync) {
    $SourcePath = Join-Path $SourceRoot $File
    $TargetPath = Join-Path $TargetRoot $File
    
    # Bestimme welche Datei Quelle und welche Ziel ist
    $FromPath = $SourcePath
    $ToPath = $TargetPath
    
    if ($Direction -eq "2") {
        # Rückwärts: Ziel → Quelle
        $FromPath = $TargetPath
        $ToPath = $SourcePath
    }
    
    # Bidirektional: Neuere Version gewinnt
    if ($Direction -eq "3") {
        $SourceExists = Test-Path $SourcePath
        $TargetExists = Test-Path $TargetPath
        
        if ($SourceExists -and $TargetExists) {
            # Beide existieren - vergleiche Datum
            $SourceDate = (Get-Item $SourcePath).LastWriteTime
            $TargetDate = (Get-Item $TargetPath).LastWriteTime
            
            if ($SourceDate -gt $TargetDate) {
                # Quelle ist neuer → Quelle → Ziel
                $FromPath = $SourcePath
                $ToPath = $TargetPath
            } elseif ($TargetDate -gt $SourceDate) {
                # Ziel ist neuer → Ziel → Quelle
                $FromPath = $TargetPath
                $ToPath = $SourcePath
            } else {
                # Gleiche Zeit → beide sind identisch, überspringen
                $SkippedCount++
                Write-Host "  ⏭️  Übersprungen (identisch): $File" -ForegroundColor Gray
                continue
            }
        } elseif ($SourceExists) {
            # Nur Quelle existiert → Quelle → Ziel
            $FromPath = $SourcePath
            $ToPath = $TargetPath
        } elseif ($TargetExists) {
            # Nur Ziel existiert → Ziel → Quelle
            $FromPath = $TargetPath
            $ToPath = $SourcePath
        } else {
            # Beide fehlen → überspringen
            $SkippedCount++
            Write-Host "  ⏭️  Übersprungen (nicht gefunden): $File" -ForegroundColor Yellow
            continue
        }
    }
    
    # Prüfe ob Quelldatei existiert
    if (-not (Test-Path $FromPath)) {
        $SkippedCount++
        Write-Host "  ⏭️  Übersprungen (nicht gefunden): $File" -ForegroundColor Yellow
        continue
    }
    
    # Erstelle Ziel-Verzeichnis falls nicht vorhanden
    $TargetDir = Split-Path $ToPath -Parent
    if (-not (Test-Path $TargetDir)) {
        try {
            New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
        } catch {
            Write-Host "  ❌ Fehler beim Erstellen des Verzeichnisses: $TargetDir" -ForegroundColor Red
            Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
            $ErrorCount++
            continue
        }
    }
    
    # Kopiere Datei
    try {
        Copy-Item -Path $FromPath -Destination $ToPath -Force
        
        $SyncedCount++
        $DirectionArrow = switch ($Direction) {
            "1" { "→" }
            "2" { "←" }
            "3" { "↔" }
            default { "→" }
        }
        Write-Host "  ✅ Synchronisiert $DirectionArrow : $File" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Fehler: $File" -ForegroundColor Red
        Write-Host "     $($_.Exception.Message)" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""
Write-Host "=== Zusammenfassung ===" -ForegroundColor Cyan
Write-Host "  ✅ Erfolgreich: $SyncedCount Dateien" -ForegroundColor Green
Write-Host "  ⏭️  Übersprungen: $SkippedCount Dateien" -ForegroundColor Gray
if ($ErrorCount -gt 0) {
    Write-Host "  ❌ Fehler: $ErrorCount Dateien" -ForegroundColor Red
}
Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "✅ Synchronisation erfolgreich abgeschlossen!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Synchronisation abgeschlossen (mit Fehlern)" -ForegroundColor Yellow
}

Write-Host ""

