@echo off
REM ========================================
REM FAMO TrafficApp - Debug-Start
REM (zeigt alle Fehlermeldungen)
REM ========================================

cd /d "%~dp0"

echo.
echo ========================================
echo   Debug-Start - Zeigt alle Fehler
echo ========================================
echo.

REM Prüfe virtuelle Umgebung
if not exist "venv\Scripts\python.exe" (
    echo [FEHLER] Virtuelle Umgebung nicht gefunden!
    echo Bitte zuerst ausfuehren: python -m venv venv
    pause
    exit /b 1
)

REM Stoppe alte Prozesse
echo [1/3] Stoppe alte Python-Prozesse...
taskkill /F /IM python.exe >nul 2>&1

REM Kurz warten
timeout /t 2 /nobreak >nul

REM Server starten (OHNE Hintergrund, mit Debug-Ausgabe)
echo [2/3] Starte Server...
echo.

venv\Scripts\python.exe start_server.py

echo.
echo ========================================
echo   Server wurde beendet
echo ========================================
echo.
pause

