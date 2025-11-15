# Git Sync Script für FAMO TrafficApp 3.0
# Führt automatische Git-Operationen aus: Add, Commit, Push
# Verwendung: .\scripts\git_sync.ps1 "Commit-Nachricht"

param(
    [string]$CommitMessage = "Automatischer Commit: Updates und Verbesserungen"
)

$ErrorActionPreference = "Stop"
$script:ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FAMO TrafficApp 3.0 - Git Synchronisation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob Git-Repository initialisiert ist
Set-Location $script:ProjectRoot
if (-not (Test-Path ".git")) {
    Write-Host "Git-Repository nicht gefunden. Initialisiere..." -ForegroundColor Yellow
    git init
    git branch -M main
    Write-Host "Git-Repository initialisiert." -ForegroundColor Green
}

# Status prüfen
Write-Host "Git Status prüfen..." -ForegroundColor Cyan
$status = git status --porcelain
if ($null -eq $status -or $status.Count -eq 0) {
    Write-Host "Keine Änderungen zum Commit gefunden." -ForegroundColor Yellow
    exit 0
}

Write-Host "Geänderte Dateien:" -ForegroundColor Cyan
git status --short

# Alle Änderungen hinzufügen
Write-Host ""
Write-Host "Änderungen zum Staging hinzufügen..." -ForegroundColor Cyan
git add .

# Commit erstellen
Write-Host "Commit erstellen..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$fullMessage = "$CommitMessage`n`nAutomatischer Commit: $timestamp"

try {
    git commit -m $fullMessage
    Write-Host "Commit erfolgreich erstellt." -ForegroundColor Green
} catch {
    Write-Host "FEHLER beim Commit: $_" -ForegroundColor Red
    exit 1
}

# Prüfe ob Remote-Repository konfiguriert ist
$remote = git remote -v
if ($null -eq $remote -or $remote.Count -eq 0) {
    Write-Host ""
    Write-Host "WARNUNG: Kein Remote-Repository konfiguriert." -ForegroundColor Yellow
    Write-Host "Füge Remote-Repository hinzu mit:" -ForegroundColor Yellow
    Write-Host "  git remote add origin <URL>" -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# Push zu Remote
Write-Host ""
Write-Host "Änderungen zu Remote-Repository pushen..." -ForegroundColor Cyan
try {
    git push
    Write-Host "Push erfolgreich." -ForegroundColor Green
} catch {
    Write-Host "FEHLER beim Push: $_" -ForegroundColor Red
    Write-Host "Möglicherweise ist 'git push -u origin main' erforderlich." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Git Synchronisation erfolgreich!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

