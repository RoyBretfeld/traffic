# Vollständige Synchronisation ALLER Dateien in die Cloud
# Von: E:\_____1111____Projekte-Programmierung
# Nach: G:\Meine Ablage\_____1111____Projekte-Programmierung
#
# Nutzung:
#   .\scripts\sync_complete_to_cloud.ps1
#
# Oder aus Projekt-Root:
#   powershell -ExecutionPolicy Bypass -File scripts\sync_complete_to_cloud.ps1

$ErrorActionPreference = "Stop"

# Pfade
$SourceRoot = "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

# Zeitstempel
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VOLLSTAENDIGE CLOUD-SYNCHRONISATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle: $SourceRoot" -ForegroundColor Gray
Write-Host "Ziel:   $CloudRoot" -ForegroundColor Gray
Write-Host "Zeit:   $timestamp" -ForegroundColor Gray
Write-Host ""

# 1. Prüfe ob Quell-Ordner existiert
Write-Host "[1/5] Prüfe Quell-Ordner..." -ForegroundColor Yellow
if (-not (Test-Path $SourceRoot)) {
    Write-Host "  FEHLER: Quell-Ordner existiert nicht!" -ForegroundColor Red
    Write-Host "  Pfad: $SourceRoot" -ForegroundColor Yellow
    exit 1
}
Write-Host "  OK: Quell-Ordner gefunden" -ForegroundColor Green

# 2. Prüfe ob Cloud-Ordner existiert
Write-Host ""
Write-Host "[2/5] Prüfe Cloud-Ordner..." -ForegroundColor Yellow
if (-not (Test-Path $CloudRoot)) {
    Write-Host "  Erstelle Cloud-Ordner..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $CloudRoot -Force | Out-Null
    Write-Host "  OK: Cloud-Ordner erstellt" -ForegroundColor Green
} else {
    Write-Host "  OK: Cloud-Ordner vorhanden" -ForegroundColor Green
}

# 3. Erstelle Ausschluss-Liste
Write-Host ""
Write-Host "[3/5] Erstelle Ausschluss-Liste..." -ForegroundColor Yellow

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
    "backups",
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

# Erstelle robocopy Ausschluss-String
$excludeString = "/XD"
foreach ($dir in $ExcludeDirs) {
    $excludeString += " `"$dir`""
}

$excludeString += " /XF"
foreach ($file in $ExcludeFiles) {
    $excludeString += " `"$file`""
}

Write-Host "  OK: Ausschluss-Liste erstellt" -ForegroundColor Green

# 4. Synchronisiere mit robocopy
Write-Host ""
Write-Host "[4/5] Starte Synchronisation..." -ForegroundColor Yellow
Write-Host "  Dies kann sehr lange dauern (82626+ Dateien)..." -ForegroundColor Gray
Write-Host "  Bitte warten..." -ForegroundColor Gray
Write-Host ""

# robocopy Parameter:
# /E = Kopiere alle Unterverzeichnisse (inkl. leerer)
# /COPYALL = Kopiere alle Dateiattribute
# /R:3 = 3 Wiederholungsversuche bei Fehlern
# /W:5 = 5 Sekunden Wartezeit zwischen Versuchen
# /MT:8 = 8 Threads für bessere Performance
# /NP = Keine Fortschrittsanzeige (für bessere Performance)
# /NFL = Keine Dateiliste
# /NDL = Keine Verzeichnisliste
# /NJH = Keine Job-Header
# /NJS = Keine Job-Zusammenfassung

$robocopyArgs = @(
    "`"$SourceRoot`"",
    "`"$CloudRoot`"",
    "/E",
    "/COPY:DAT",  # Kopiere Data, Attributes, Timestamps (ohne ACLs - keine Admin-Rechte nötig)
    "/R:3",
    "/W:5",
    "/MT:8",
    "/NP",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS"
)

# Füge Ausschlüsse hinzu
foreach ($dir in $ExcludeDirs) {
    $robocopyArgs += "/XD"
    $robocopyArgs += "`"$dir`""
}

foreach ($file in $ExcludeFiles) {
    $robocopyArgs += "/XF"
    $robocopyArgs += "`"$file`""
}

try {
    $robocopyOutput = & robocopy $robocopyArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    # robocopy Exit-Codes:
    # 0-7 = Erfolg (0 = keine Dateien kopiert, 1-7 = Dateien kopiert)
    # 8+ = Fehler
    
    if ($exitCode -le 7) {
        Write-Host "  OK: Synchronisation erfolgreich" -ForegroundColor Green
        
        # Parse robocopy Output für Statistiken
        $outputText = $robocopyOutput -join "`n"
        if ($outputText -match "Dirs\s+:\s+(\d+)\s+(\d+)\s+(\d+)") {
            $dirsTotal = $matches[1]
            $dirsCopied = $matches[2]
            $dirsSkipped = $matches[3]
            Write-Host "      Verzeichnisse: $dirsTotal (kopiert: $dirsCopied, übersprungen: $dirsSkipped)" -ForegroundColor Gray
        }
        if ($outputText -match "Files\s+:\s+(\d+)\s+(\d+)\s+(\d+)") {
            $filesTotal = $matches[1]
            $filesCopied = $matches[2]
            $filesSkipped = $matches[3]
            Write-Host "      Dateien: $filesTotal (kopiert: $filesCopied, übersprungen: $filesSkipped)" -ForegroundColor Gray
        }
        if ($outputText -match "Bytes\s+:\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)") {
            $bytesTotal = $matches[1]
            $bytesCopied = $matches[2]
            $bytesSkipped = $matches[3]
            Write-Host "      Daten: $bytesTotal Bytes (kopiert: $bytesCopied, übersprungen: $bytesSkipped)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  FEHLER: Synchronisation fehlgeschlagen (Exit-Code: $exitCode)" -ForegroundColor Red
        Write-Host "  Output:" -ForegroundColor Yellow
        Write-Host $robocopyOutput -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "  FEHLER: Fehler bei robocopy: $_" -ForegroundColor Red
    exit 1
}

# 5. Zusammenfassung
Write-Host ""
Write-Host "[5/5] Erstelle Zusammenfassung..." -ForegroundColor Yellow

# Zähle Dateien im Ziel
$cloudFileCount = (Get-ChildItem -Path $CloudRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
$cloudDirCount = (Get-ChildItem -Path $CloudRoot -Recurse -Directory -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Host "  OK: Zusammenfassung erstellt" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SYNCHRONISATION ERFOLGREICH" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle:        $SourceRoot" -ForegroundColor Cyan
Write-Host "Ziel:          $CloudRoot" -ForegroundColor Cyan
Write-Host "Zeitstempel:   $timestamp" -ForegroundColor Cyan
Write-Host "Dateien:       $cloudFileCount" -ForegroundColor Cyan
Write-Host "Verzeichnisse: $cloudDirCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "HINWEIS: Google Drive synchronisiert automatisch die Dateien in die Cloud." -ForegroundColor Yellow
Write-Host "         Bitte warten Sie, bis die Synchronisation abgeschlossen ist." -ForegroundColor Yellow
Write-Host ""

