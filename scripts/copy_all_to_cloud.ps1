# Einfaches Kopieren ALLER Dateien in die Cloud
# Von: E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0
# Nach: G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0
#
# Nutzung:
#   .\scripts\copy_all_to_cloud.ps1

$ErrorActionPreference = "Stop"

# Pfade
$SourceRoot = "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
$CloudRoot = "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DATEIEN IN CLOUD KOPIEREN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle: $SourceRoot" -ForegroundColor Gray
Write-Host "Ziel:   $CloudRoot" -ForegroundColor Gray
Write-Host ""

# 1. Prüfe Quell-Ordner
Write-Host "[1/3] Prüfe Quell-Ordner..." -ForegroundColor Yellow
if (-not (Test-Path $SourceRoot)) {
    Write-Host "  FEHLER: Quell-Ordner existiert nicht!" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Quell-Ordner gefunden" -ForegroundColor Green

# 2. Erstelle Ziel-Ordner
Write-Host ""
Write-Host "[2/3] Erstelle Ziel-Ordner..." -ForegroundColor Yellow
if (-not (Test-Path $CloudRoot)) {
    New-Item -ItemType Directory -Path $CloudRoot -Force | Out-Null
    Write-Host "  OK: Ziel-Ordner erstellt" -ForegroundColor Green
} else {
    Write-Host "  OK: Ziel-Ordner vorhanden" -ForegroundColor Green
}

# 3. Kopiere alle Dateien
Write-Host ""
Write-Host "[3/3] Kopiere Dateien..." -ForegroundColor Yellow
Write-Host "  Dies kann einige Minuten dauern..." -ForegroundColor Gray
Write-Host ""

# Verwende robocopy für zuverlässiges Kopieren
# /E = Alle Unterverzeichnisse
# /COPY:DAT = Daten, Attribute, Zeitstempel
# /R:3 = 3 Wiederholungen bei Fehlern
# /W:5 = 5 Sekunden Wartezeit
# /MT:8 = 8 Threads
# /NP = Keine Fortschrittsanzeige
# /NFL = Keine Dateiliste
# /NDL = Keine Verzeichnisliste
# /NJH = Keine Job-Header
# /NJS = Keine Job-Zusammenfassung

$robocopyArgs = @(
    "`"$SourceRoot`"",
    "`"$CloudRoot`"",
    "/E",
    "/COPY:DAT",
    "/R:3",
    "/W:5",
    "/MT:8",
    "/NP",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/XD",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "chroma_db",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "backups",
    "ZIP",
    "temp",
    "tmp",
    "logs",
    "/XF",
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

try {
    $robocopyOutput = & robocopy $robocopyArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    # robocopy Exit-Codes: 0-7 = Erfolg, 8+ = Fehler
    if ($exitCode -le 7) {
        Write-Host "  OK: Kopieren erfolgreich" -ForegroundColor Green
        
        # Parse Output für Statistiken
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
            $bytesTotal = [math]::Round([double]$matches[1] / 1MB, 2)
            $bytesCopied = [math]::Round([double]$matches[2] / 1MB, 2)
            Write-Host "      Daten: $bytesTotal MB (kopiert: $bytesCopied MB)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  FEHLER: Kopieren fehlgeschlagen (Exit-Code: $exitCode)" -ForegroundColor Red
        Write-Host $robocopyOutput -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "  FEHLER: Fehler beim Kopieren: $_" -ForegroundColor Red
    exit 1
}

# Zusammenfassung
$cloudFileCount = (Get-ChildItem -Path $CloudRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
$cloudDirCount = (Get-ChildItem -Path $CloudRoot -Recurse -Directory -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KOPIEREN ERFOLGREICH" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle:        $SourceRoot" -ForegroundColor Cyan
Write-Host "Ziel:          $CloudRoot" -ForegroundColor Cyan
Write-Host "Dateien:       $cloudFileCount" -ForegroundColor Cyan
Write-Host "Verzeichnisse: $cloudDirCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "HINWEIS: Google Drive synchronisiert automatisch die Dateien in die Cloud." -ForegroundColor Yellow
Write-Host ""

