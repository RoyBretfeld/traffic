# Diagnose-Script: Warum startet der Server nicht?
# Systematische Analyse aller möglichen Probleme

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║     🔍 SERVER-START DIAGNOSE 🔍                               ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

$ErrorActionPreference = "Continue"

# 1. Python-Prozesse
Write-Host "1. PYTHON-PROZESSE:" -ForegroundColor Cyan
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "   [WARNUNG] Gefunden: $($pythonProcs.Count) Python-Prozess(e)" -ForegroundColor Yellow
    $pythonProcs | ForEach-Object {
        $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        Write-Host "   PID: $($_.Id) - Start: $($_.StartTime) - Memory: $([math]::Round($_.WorkingSet64/1MB, 2)) MB"
        if ($cmdLine) {
            Write-Host "      CmdLine: $($cmdLine.Substring(0, [Math]::Min(100, $cmdLine.Length)))..."
        }
    }
} else {
    Write-Host "   [OK] Keine Python-Prozesse" -ForegroundColor Green
}
Write-Host ""

# 2. Port 8111
Write-Host "2. PORT 8111:" -ForegroundColor Cyan
$port8111 = netstat -ano | findstr ":8111 "
if ($port8111) {
    Write-Host "   [WARNUNG] Port 8111 ist belegt!" -ForegroundColor Yellow
    $port8111 | ForEach-Object {
        Write-Host "   $_"
        $pid = ($_ -split '\s+')[-1]
        if ($pid) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "      -> Prozess: $($proc.ProcessName) (PID: $pid, Start: $($proc.StartTime))"
            }
        }
    }
} else {
    Write-Host "   [OK] Port 8111 ist frei" -ForegroundColor Green
}
Write-Host ""

# 3. Venv-Status
Write-Host "3. VENV-STATUS:" -ForegroundColor Cyan
if (Test-Path "venv\Scripts\python.exe") {
    $venvPython = (Resolve-Path "venv\Scripts\python.exe").Path
    Write-Host "   [OK] Venv gefunden: $venvPython" -ForegroundColor Green
    
    # Teste Python
    $pythonTest = & $venvPython -c "import sys; print(sys.executable)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Python funktioniert: $pythonTest" -ForegroundColor Green
    } else {
        Write-Host "   [FEHLER] Python-Test fehlgeschlagen: $pythonTest" -ForegroundColor Red
    }
} else {
    Write-Host "   [FEHLER] Venv nicht gefunden!" -ForegroundColor Red
}
Write-Host ""

# 4. Kritische Packages
Write-Host "4. KRITISCHE PACKAGES:" -ForegroundColor Cyan
if (Test-Path "venv\Scripts\python.exe") {
    $venvPython = (Resolve-Path "venv\Scripts\python.exe").Path
    $packages = @("sqlalchemy", "fastapi", "uvicorn", "pandas")
    foreach ($pkg in $packages) {
        $test = & $venvPython -c "import $pkg; print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] $pkg" -ForegroundColor Green
        } else {
            Write-Host "   [FEHLER] ${pkg}: $test" -ForegroundColor Red
        }
    }
}
Write-Host ""

# 5. Datenbank-Status
Write-Host "5. DATENBANK-STATUS:" -ForegroundColor Cyan
if (Test-Path "data\traffic.db") {
    $dbSize = (Get-Item "data\traffic.db").Length / 1MB
    Write-Host "   [OK] traffic.db gefunden: $([math]::Round($dbSize, 2)) MB" -ForegroundColor Green
    
    # Prüfe ob DB gesperrt ist
    try {
        $dbTest = & $venvPython -c "import sqlite3; conn = sqlite3.connect('data/traffic.db'); conn.execute('SELECT 1'); conn.close(); print('OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] Datenbank ist nicht gesperrt" -ForegroundColor Green
        } else {
            Write-Host "   [WARNUNG] Datenbank könnte gesperrt sein: $dbTest" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   [WARNUNG] Datenbank-Test fehlgeschlagen: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [INFO] traffic.db nicht gefunden (wird beim Start erstellt)" -ForegroundColor Gray
}
Write-Host ""

# 6. Log-Dateien
Write-Host "6. LOG-DATEIEN:" -ForegroundColor Cyan
if (Test-Path "logs\debug.log") {
    $logSize = (Get-Item "logs\debug.log").Length / 1KB
    Write-Host "   [OK] debug.log gefunden: $([math]::Round($logSize, 2)) KB" -ForegroundColor Green
    Write-Host "   Letzte 5 Zeilen:"
    Get-Content "logs\debug.log" -Tail 5 | ForEach-Object { Write-Host "      $_" }
} else {
    Write-Host "   [INFO] debug.log nicht gefunden" -ForegroundColor Gray
}
Write-Host ""

# 7. Schema-Fehler prüfen
Write-Host "7. SCHEMA-FEHLER PRUEFEN:" -ForegroundColor Cyan
if (Test-Path "venv\Scripts\python.exe" -and Test-Path "data\traffic.db") {
    $venvPython = (Resolve-Path "venv\Scripts\python.exe").Path
    $schemaTest = & $venvPython -c "import sqlite3; conn = sqlite3.connect('data/traffic.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(geo_fail)'); cols = [row[1] for row in cursor.fetchall()]; print('Spalten:', ', '.join(cols)); conn.close()" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Schema-Test erfolgreich" -ForegroundColor Green
        Write-Host "   $schemaTest"
    } else {
        Write-Host "   [FEHLER] Schema-Test fehlgeschlagen: $schemaTest" -ForegroundColor Red
    }
}
Write-Host ""

# 8. Zusammenfassung
Write-Host "8. ZUSAMMENFASSUNG:" -ForegroundColor Cyan
$issues = @()
if ($pythonProcs -and $pythonProcs.Count -gt 0) {
    $issues += "Python-Prozesse laufen noch ($($pythonProcs.Count))"
}
if ($port8111) {
    $issues += "Port 8111 ist belegt"
}
if ($issues.Count -eq 0) {
    Write-Host "   [OK] Keine offensichtlichen Probleme gefunden" -ForegroundColor Green
    Write-Host "   → Server sollte starten können"
} else {
    Write-Host "   [WARNUNG] Probleme gefunden:" -ForegroundColor Yellow
    $issues | ForEach-Object { Write-Host "      - $_" }
    Write-Host ""
    Write-Host "   EMPFEHLUNG:" -ForegroundColor Yellow
    Write-Host "   1. Alle Python-Prozesse beenden: Get-Process python | Stop-Process -Force"
    Write-Host "   2. Port 8111 prüfen: netstat -ano | findstr ':8111'"
    Write-Host "   3. Server neu starten"
}
Write-Host ""

