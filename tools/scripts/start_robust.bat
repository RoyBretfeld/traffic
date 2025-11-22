@echo off
REM ========================================
REM FAMO TrafficApp - Robuster Server-Start
REM Behebt automatisch Probleme und startet zuverlässig
REM ========================================

setlocal enabledelayedexpansion

REM Farben für saubere Ausgabe
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

echo.
echo ========================================
echo   FAMO TrafficApp - Robuster Start
echo ========================================
echo.

REM Wechsel ins Projektverzeichnis
cd /d "%~dp0\..\.."
set "PROJECT_DIR=%CD%"

REM 1. Prüfe ob Server bereits läuft
echo [1/6] Pruefe Server-Status...
curl -s http://127.0.0.1:8111/health >nul 2>&1
if %errorlevel% equ 0 (
    echo    Server laeuft bereits auf Port 8111
    echo    Oeffne Browser: http://127.0.0.1:8111
    start http://127.0.0.1:8111
    timeout /t 2 >nul
    exit /b 0
)
echo    Server laeuft nicht - Starte neu...

REM 2. Beende alle Python-Prozesse (falls Server noch läuft)
echo [2/6] Beende alte Python-Prozesse...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul 2>&1

REM 3. Prüfe und repariere Datenbank
echo [3/6] Pruefe Datenbank-Integritaet...
if exist "data\traffic.db" (
    python -c "import sqlite3; conn = sqlite3.connect('data/traffic.db'); result = conn.execute('PRAGMA integrity_check').fetchone()[0]; conn.close(); exit(0 if result == 'ok' else 1)" 2>nul
    if !errorlevel! neq 0 (
        echo    Datenbank scheint beschaedigt - Starte Reparatur...
        python scripts\repair_db.py --auto
        if !errorlevel! neq 0 (
            echo    Reparatur fehlgeschlagen - Erstelle neue Datenbank...
            if exist "data\traffic.db" (
                move "data\traffic.db" "data\traffic.db.corrupted_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%" >nul 2>&1
            )
        )
    ) else (
        echo    Datenbank OK
    )
) else (
    echo    Datenbank existiert nicht - wird beim Start erstellt
)

REM 4. Prüfe virtuelle Umgebung
echo [4/6] Pruefe virtuelle Umgebung...
if not exist "venv\Scripts\python.exe" (
    echo    Venv nicht gefunden - Erstelle neue...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo    FEHLER: Venv konnte nicht erstellt werden
        pause
        exit /b 1
    )
)

REM 5. Aktiviere virtuelle Umgebung
echo [5/6] Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo    FEHLER: Venv konnte nicht aktiviert werden
    pause
    exit /b 1
)

REM 6. Prüfe kritische Packages
echo [6/6] Pruefe kritische Packages...
python -c "import fastapi, uvicorn, sqlalchemy" 2>nul
if !errorlevel! neq 0 (
    echo    Kritische Packages fehlen - Installiere...
    pip install -q fastapi uvicorn sqlalchemy
    if !errorlevel! neq 0 (
        echo    FEHLER: Packages konnten nicht installiert werden
        pause
        exit /b 1
    )
)

REM 7. Starte Server
echo [7/7] Starte Server...
echo.
echo ========================================
echo   Server wird gestartet...
echo   URL: http://127.0.0.1:8111
echo ========================================
echo.
echo   Druecken Sie Ctrl+C zum Beenden
echo.

REM Warte 3 Sekunden und öffne dann den Browser
start /B timeout /t 3 /nobreak >nul 2>&1 && start http://127.0.0.1:8111

REM Server starten (blockiert das Terminal)
python start_server.py

REM Falls der Server beendet wird
echo.
echo ========================================
echo   Server wurde beendet.
echo ========================================
echo.
pause

