@echo off
REM Git Sync Script für FAMO TrafficApp 3.0 (Batch-Version)
REM Verwendung: scripts\git_sync.bat "Commit-Nachricht"

setlocal enabledelayedexpansion

set "COMMIT_MSG=%~1"
if "%COMMIT_MSG%"=="" set "COMMIT_MSG=Automatischer Commit: Updates und Verbesserungen"

echo ========================================
echo FAMO TrafficApp 3.0 - Git Synchronisation
echo ========================================
echo.

cd /d "%~dp0.."

REM Prüfe ob Git-Repository initialisiert ist
if not exist ".git" (
    echo Git-Repository nicht gefunden. Initialisiere...
    git init
    git branch -M main
    echo Git-Repository initialisiert.
)

REM Status prüfen
echo Git Status prüfen...
git status --short
if errorlevel 1 (
    echo Keine Änderungen zum Commit gefunden.
    exit /b 0
)

REM Alle Änderungen hinzufügen
echo.
echo Änderungen zum Staging hinzufügen...
git add .

REM Commit erstellen
echo Commit erstellen...
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%:%datetime:~12,2%

git commit -m "%COMMIT_MSG%

Automatischer Commit: %timestamp%"
if errorlevel 1 (
    echo FEHLER beim Commit.
    exit /b 1
)
echo Commit erfolgreich erstellt.

REM Prüfe ob Remote-Repository konfiguriert ist
git remote -v >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNUNG: Kein Remote-Repository konfiguriert.
    echo Füge Remote-Repository hinzu mit:
    echo   git remote add origin ^<URL^>
    echo.
    exit /b 0
)

REM Push zu Remote
echo.
echo Änderungen zu Remote-Repository pushen...
git push
if errorlevel 1 (
    echo FEHLER beim Push.
    echo Möglicherweise ist 'git push -u origin main' erforderlich.
    exit /b 1
)

echo.
echo ========================================
echo Git Synchronisation erfolgreich!
echo ========================================
echo.

