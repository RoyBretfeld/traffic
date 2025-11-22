# ========================================
# FAMO TrafficApp - Robuster Server-Start (PowerShell)
# Behebt automatisch Probleme und startet zuverlässig
# ========================================

$ErrorActionPreference = "Continue"

# Farben für saubere Ausgabe
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FAMO TrafficApp - Robuster Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Wechsel ins Projektverzeichnis
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Resolve-Path (Join-Path $scriptPath "..\..")
Set-Location $projectDir

# 1. Prüfe ob Server bereits läuft
Write-Host "[1/6] Prüfe Server-Status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8111/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "   Server läuft bereits auf Port 8111" -ForegroundColor Green
        Write-Host "   Öffne Browser: http://127.0.0.1:8111" -ForegroundColor Green
        Start-Process "http://127.0.0.1:8111"
        Start-Sleep -Seconds 2
        exit 0
    }
} catch {
    Write-Host "   Server läuft nicht - Starte neu..." -ForegroundColor Yellow
}

# 2. Prüfe und repariere Datenbank
Write-Host "[2/6] Prüfe Datenbank-Integrität..." -ForegroundColor Yellow
$dbPath = Join-Path $projectDir "data\traffic.db"
if (Test-Path $dbPath) {
    try {
        Add-Type -Path (Join-Path $projectDir "venv\Lib\site-packages\System.Data.SQLite.dll") -ErrorAction SilentlyContinue
        $conn = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$dbPath")
        $conn.Open()
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = "PRAGMA integrity_check"
        $result = $cmd.ExecuteScalar()
        $conn.Close()
        
        if ($result -ne "ok") {
            Write-Host "   Datenbank scheint beschädigt - Starte Reparatur..." -ForegroundColor Yellow
            & "$projectDir\venv\Scripts\python.exe" "$projectDir\scripts\repair_db.py"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "   Reparatur fehlgeschlagen - Erstelle neue Datenbank..." -ForegroundColor Yellow
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $corruptedPath = "$dbPath.corrupted_$timestamp"
                Move-Item $dbPath $corruptedPath -ErrorAction SilentlyContinue
            }
        } else {
            Write-Host "   Datenbank OK" -ForegroundColor Green
        }
    } catch {
        # Fallback: Python-Check
        $checkResult = & "$projectDir\venv\Scripts\python.exe" -c "import sqlite3; conn = sqlite3.connect('data/traffic.db'); result = conn.execute('PRAGMA integrity_check').fetchone()[0]; conn.close(); exit(0 if result == 'ok' else 1)" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   Datenbank scheint beschädigt - Starte Reparatur..." -ForegroundColor Yellow
            & "$projectDir\venv\Scripts\python.exe" "$projectDir\scripts\repair_db.py"
        } else {
            Write-Host "   Datenbank OK" -ForegroundColor Green
        }
    }
} else {
    Write-Host "   Datenbank existiert nicht - wird beim Start erstellt" -ForegroundColor Yellow
}

# 3. Prüfe virtuelle Umgebung
Write-Host "[3/6] Prüfe virtuelle Umgebung..." -ForegroundColor Yellow
$venvPython = Join-Path $projectDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "   Venv nicht gefunden - Erstelle neue..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   FEHLER: Venv konnte nicht erstellt werden" -ForegroundColor Red
        Read-Host "Drücken Sie Enter zum Beenden"
        exit 1
    }
}

# 4. Aktiviere virtuelle Umgebung
Write-Host "[4/6] Aktiviere virtuelle Umgebung..." -ForegroundColor Yellow
& "$venvPython" --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   FEHLER: Venv konnte nicht aktiviert werden" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

# 5. Prüfe kritische Packages
Write-Host "[5/6] Prüfe kritische Packages..." -ForegroundColor Yellow
$checkPackages = & "$venvPython" -c "import fastapi, uvicorn, sqlalchemy" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Kritische Packages fehlen - Installiere..." -ForegroundColor Yellow
    & "$venvPython" -m pip install -q fastapi uvicorn sqlalchemy
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   FEHLER: Packages konnten nicht installiert werden" -ForegroundColor Red
        Read-Host "Drücken Sie Enter zum Beenden"
        exit 1
    }
}

# 6. Starte Server
Write-Host "[6/6] Starte Server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server wird gestartet..." -ForegroundColor Cyan
Write-Host "  URL: http://127.0.0.1:8111" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Drücken Sie Ctrl+C zum Beenden" -ForegroundColor Yellow
Write-Host ""

# Warte 3 Sekunden und öffne dann den Browser
Start-Job -ScriptBlock { Start-Sleep -Seconds 3; Start-Process "http://127.0.0.1:8111" } | Out-Null

# Server starten (blockiert das Terminal)
& "$venvPython" "$projectDir\start_server.py"

# Falls der Server beendet wird
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server wurde beendet." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Drücken Sie Enter zum Beenden"

