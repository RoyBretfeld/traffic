# Vollstaendiges Backup der aktuellen Situation
# Erstellt: Git-Commit + ZIP-Backup

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupDir = "backups"
$zipName = "backup_vollstaendig_$timestamp.zip"
$zipPath = Join-Path $backupDir $zipName

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VOLLSTAENDIGES BACKUP ERSTELLEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Git-Status pruefen
Write-Host "[1/4] Git-Status pruefen..." -ForegroundColor Yellow
$gitStatus = git status --short
if ($gitStatus) {
    Write-Host "  WARNUNG: Uncommitted Aenderungen gefunden:" -ForegroundColor Yellow
    Write-Host $gitStatus -ForegroundColor Gray
    
    # Git-Commit erstellen
    Write-Host ""
    Write-Host "[2/4] Git-Commit erstellen..." -ForegroundColor Yellow
    $commitMessage = "Backup: Stand $timestamp - Alle Fehler behoben, Allow-Liste geleert, Sub-Routen-Generator angepasst"
    git add .
    git commit -m $commitMessage
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK: Git-Commit erfolgreich" -ForegroundColor Green
    } else {
        Write-Host "  WARNUNG: Git-Commit fehlgeschlagen (moeglicherweise keine Aenderungen)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  OK: Keine uncommitted Aenderungen" -ForegroundColor Green
}

Write-Host ""

# 2. Backup-Verzeichnis erstellen
Write-Host "[3/4] Backup-Verzeichnis vorbereiten..." -ForegroundColor Yellow
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    Write-Host "  OK: Backup-Verzeichnis erstellt: $backupDir" -ForegroundColor Green
} else {
    Write-Host "  OK: Backup-Verzeichnis vorhanden: $backupDir" -ForegroundColor Green
}

Write-Host ""

# 3. ZIP-Backup erstellen
Write-Host "[4/4] ZIP-Backup erstellen..." -ForegroundColor Yellow
Write-Host "  Erstelle: $zipName" -ForegroundColor Gray

# Wichtige Verzeichnisse und Dateien
$itemsToBackup = @(
    "backend",
    "frontend",
    "config",
    "Regeln",
    "Global",
    "docs",
    "scripts",
    "db",
    "common",
    "repositories",
    "services",
    "routes",
    "tests",
    "ingest",
    "tools",
    "*.md",
    "*.py",
    "*.ps1",
    "*.json",
    "*.txt",
    "*.toml",
    "*.yml",
    "*.yaml",
    ".cursorrules",
    "requirements.txt",
    "start_server.py",
    "PROJECT_PROFILE.md",
    "DOKUMENTATION.md",
    "MODULE_MAP.md",
    "README_AUDIT_COMPLETE.md"
)

# ZIP erstellen
$zipItems = @()
foreach ($item in $itemsToBackup) {
    $path = Join-Path "." $item
    if (Test-Path $path) {
        $zipItems += $path
    }
}

try {
    Compress-Archive -Path $zipItems -DestinationPath $zipPath -CompressionLevel Optimal -Force
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Host "  OK: ZIP-Backup erstellt: $zipName ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
} catch {
    Write-Host "  FEHLER: Fehler beim Erstellen des ZIP-Backups: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OK: BACKUP ERFOLGREICH ABGESCHLOSSEN" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup-Datei: $zipPath" -ForegroundColor Cyan
Write-Host "Zeitstempel: $timestamp" -ForegroundColor Cyan
Write-Host ""
