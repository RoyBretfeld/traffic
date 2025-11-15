@echo off
echo ========================================
echo   FAMO TrafficApp - Schnellstart
echo ========================================

REM Alle Python-Prozesse beenden
taskkill /f /im python.exe >nul 2>&1

REM Warten
timeout /t 2 /nobreak >nul

REM Server starten
echo Starte Server...
python start_server.py

pause