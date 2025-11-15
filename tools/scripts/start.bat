@echo off
REM ========================================
REM FAMO TrafficApp - Automatischer Start
REM ========================================

echo.
echo ========================================
echo   FAMO TrafficApp wird gestartet...
echo ========================================
echo.

REM Wechsel ins Projektverzeichnis
cd /d "%~dp0"

REM Virtuelle Umgebung aktivieren
echo [1/3] Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat

REM Prüfe, ob Server schon läuft
echo [2/3] Pruefe Server-Status...
curl -s http://127.0.0.1:8111/health >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Server laeuft bereits!
    echo ========================================
    echo.
    echo Oeffne Browser: http://127.0.0.1:8111
    start http://127.0.0.1:8111
    echo.
    pause
    exit /b 0
)

REM Server starten
echo [3/3] Starte FastAPI-Server...
echo.
echo ========================================
echo   Server wird gestartet...
echo   URL: http://127.0.0.1:8111
echo ========================================
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

