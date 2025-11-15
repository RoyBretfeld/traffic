@echo off
REM Batch-Script zum Erstellen eines Windows Task Scheduler Jobs
REM für tägliches Datenbank-Backup um 16:00 Uhr

set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%db_backup.py
set TASK_NAME=FAMO_TrafficApp_DB_Backup
set TASK_DESC=Tägliches Backup der traffic.db Datenbank um 16:00 Uhr

echo Erstelle Windows Task Scheduler Job...
echo.

REM Prüfe ob Task bereits existiert und lösche ihn
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Task existiert bereits. Lösche...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
)

REM Erstelle neuen Task (täglich um 16:00 Uhr)
schtasks /create /tn "%TASK_NAME%" /tr "python \"%SCRIPT_PATH%\"" /sc daily /st 16:00 /ru SYSTEM /f

if %ERRORLEVEL% == 0 (
    echo.
    echo Task erfolgreich erstellt: %TASK_NAME%
    echo Backup wird täglich um 16:00 Uhr ausgeführt.
    echo.
    echo Task anzeigen: schtasks /query /tn "%TASK_NAME%"
    echo Task löschen: schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo FEHLER: Task konnte nicht erstellt werden.
    echo Bitte führen Sie das Script als Administrator aus.
)

pause

