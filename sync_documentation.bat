@echo off
REM Dokumentations-Synchronisierungs-Skript (Batch-Version)
REM Synchronisiert alle wichtigen Dokumentationsdateien zwischen Workflow und Cloud

setlocal enabledelayedexpansion

set SOURCE=C:\Workflow\TrafficApp
set DESTINATION=C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0

echo.
echo ======================================================================
echo  Dokumentations-Synchronisierung
echo ======================================================================
echo  Quelle:  %SOURCE%
echo  Ziel:    %DESTINATION%
echo.

REM Dokumentationsdateien
set "FILES=README.md CHANGELOG.md CURSOR_RULES.md ADRESS_ERKENNUNG_DOKUMENTATION.md SYSTEMABSCHLUSS_DOKUMENTATION.md MIGRATION_TO_OPENAI.md README_CSV_PARSING.md FILE_INPUT_FIX_REPORT.md STATUS_REPORT.md"

set SYNC_COUNT=0
set ERROR_COUNT=0

echo [SYNCHRONISIERE DATEIEN]
echo.

for %%F in (%FILES%) do (
    if exist "!SOURCE!\%%F" (
        copy "!SOURCE!\%%F" "!DESTINATION!\%%F" /Y >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            echo   [OK] %%F
            set /a SYNC_COUNT+=1
        ) else (
            echo   [FEHLER] %%F
            set /a ERROR_COUNT+=1
        )
    ) else (
        echo   [SKIPPED] %%F - nicht gefunden
    )
)

echo.
echo ======================================================================
echo  Synchronisierung abgeschlossen!
echo  - %SYNC_COUNT% Dateien synchronisiert
if %ERROR_COUNT% gtr 0 (
    echo  - %ERROR_COUNT% Fehler
)
echo ======================================================================
echo.
pause
