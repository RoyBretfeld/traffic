@echo off
REM ========================================
REM FAMO TrafficApp - Stiller Start
REM (ohne Konsolenfenster)
REM ========================================

cd /d "%~dp0"

REM Prüfe, ob Server schon läuft
curl -s http://127.0.0.1:8111/health >nul 2>&1
if %errorlevel% equ 0 (
    start http://127.0.0.1:8111
    exit /b 0
)

REM Server im Hintergrund starten
start /B cmd /c "venv\Scripts\activate.bat && python start_server.py"

REM Warte 5 Sekunden und öffne Browser
timeout /t 5 /nobreak >nul
start http://127.0.0.1:8111

exit /b 0

