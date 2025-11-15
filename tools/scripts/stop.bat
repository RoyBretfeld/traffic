@echo off
REM ========================================
REM FAMO TrafficApp - Server stoppen
REM ========================================

echo.
echo ========================================
echo   FAMO TrafficApp Server wird gestoppt...
echo ========================================
echo.

REM Finde Python-Prozesse mit start_server.py
echo Suche nach laufenden Server-Prozessen...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /NH ^| findstr "python.exe"') do (
    echo Stoppe Prozess mit PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ========================================
echo   Server wurde gestoppt.
echo ========================================
echo.
pause

