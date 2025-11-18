# Script zum Entfernen des API-Keys aus der Git-Historie
# WICHTIG: Dies überschreibt die Git-Historie - nur verwenden wenn sicher!

param(
    [string]$OldApiKey = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Red
Write-Host "API-Key aus Git-Historie entfernen" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNUNG: Dies überschreibt die Git-Historie!" -ForegroundColor Yellow
Write-Host "Alle Commits, die den API-Key enthalten, werden bereinigt." -ForegroundColor Yellow
Write-Host ""

if (-not $OldApiKey) {
    Write-Host "FEHLER: Bitte geben Sie den alten API-Key an:" -ForegroundColor Red
    Write-Host "  .\scripts\remove_api_key_from_history.ps1 -OldApiKey 'sk-proj-...'" -ForegroundColor Yellow
    exit 1
}

# Prüfe ob wir auf main/master sind
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne "main" -and $currentBranch -ne "master") {
    Write-Host "WARNUNG: Sie sind nicht auf 'main' oder 'master'!" -ForegroundColor Yellow
    Write-Host "Aktueller Branch: $currentBranch" -ForegroundColor Yellow
    $confirm = Read-Host "Fortfahren? (j/n)"
    if ($confirm -ne "j" -and $confirm -ne "J") {
        exit 0
    }
}

# Prüfe ob es uncommitted Änderungen gibt
$status = git status --porcelain
if ($status) {
    Write-Host "FEHLER: Es gibt uncommitted Änderungen!" -ForegroundColor Red
    Write-Host "Bitte committen oder stashen Sie alle Änderungen zuerst." -ForegroundColor Yellow
    exit 1
}

Write-Host "Entferne API-Key aus Git-Historie..." -ForegroundColor Cyan
Write-Host "Alter Key (erste 20 Zeichen): $($OldApiKey.Substring(0, [Math]::Min(20, $OldApiKey.Length)))..." -ForegroundColor Gray
Write-Host ""

# Verwende git filter-branch oder git filter-repo
# Prüfe ob git-filter-repo verfügbar ist
$hasFilterRepo = Get-Command git-filter-repo -ErrorAction SilentlyContinue

if ($hasFilterRepo) {
    Write-Host "Verwende git-filter-repo (schneller und sicherer)..." -ForegroundColor Cyan
    
    # Erstelle temporäre Datei mit dem zu entfernenden Key
    $tempFile = [System.IO.Path]::GetTempFileName()
    $OldApiKey | Out-File -FilePath $tempFile -Encoding UTF8
    
    # Entferne Key aus config.env in der Historie
    git filter-repo --path config.env --invert-paths --force
    # Dann füge config.env wieder hinzu, aber ohne den Key
    # (Dies ist komplexer - wir verwenden stattdessen git filter-branch)
    
    Remove-Item $tempFile
} else {
    Write-Host "Verwende git filter-branch (langsamer, aber verfügbar)..." -ForegroundColor Cyan
    
    # Entferne den Key aus config.env in allen Commits
    $env:GIT_EDITOR = "powershell -Command `"`$content = Get-Content `$args[0]; `$content = `$content -replace '$OldApiKey', 'sk-proj-REMOVED'; Set-Content `$args[0] `$content`""
    
    # Alternative: Verwende sed-ähnliche Ersetzung
    git filter-branch --force --index-filter "git rm --cached --ignore-unmatch config.env" --prune-empty --tag-name-filter cat -- --all
    
    # Jetzt müssen wir config.env wieder hinzufügen, aber ohne den Key
    # Das ist komplex - besser: config.env komplett aus Historie entfernen
    Write-Host "Entferne config.env komplett aus Git-Historie..." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Bereinige Referenzen..." -ForegroundColor Cyan
git for-each-ref --format="%(refname)" refs/original/ | ForEach-Object { git update-ref -d $_ }
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Bereinigung abgeschlossen!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "NÄCHSTE SCHRITTE:" -ForegroundColor Yellow
Write-Host "1. Prüfe die Historie: git log --all -- config.env" -ForegroundColor Cyan
Write-Host "2. Wenn alles OK ist: git push --force --all" -ForegroundColor Cyan
Write-Host "3. Warnung: Force-Push überschreibt Remote-Historie!" -ForegroundColor Red
Write-Host ""

