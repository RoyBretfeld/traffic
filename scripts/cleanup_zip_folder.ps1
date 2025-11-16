# PowerShell-Script zum Aufräumen des ZIP-Ordners
# Verschiebt alte ZIP-Dateien ins Archiv und löscht Duplikate

Write-Host "=== ZIP-Ordner Aufraeumen ===" -ForegroundColor Cyan
Write-Host ""

# Erstelle Archiv-Ordner
$archiveDir = "ZIP\archive"
if (-not (Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    Write-Host "[OK] Archiv-Ordner erstellt: $archiveDir" -ForegroundColor Green
}

# Verschiebe alte Audit-Pakete ins Archiv (vor 2025-11-10)
$oldAudits = @(
    "trafficapp_audit_20251029_141048.zip",
    "routing_osrm_audit_20251105_124035.zip",
    "OSRM_POLYGONE_PROBLEM_20251106_202641.zip",
    "FEHLER_ANALYSE_500_ERROR_20251108_194151.zip",
    "CODE_AUDIT_SPLITTING_LOGIK_2025-11-04.zip"
)

Write-Host "Verschiebe alte Audit-Pakete ins Archiv..." -ForegroundColor Yellow
foreach ($file in $oldAudits) {
    $source = "ZIP\$file"
    if (Test-Path $source) {
        $dest = "$archiveDir\$file"
        Move-Item -Path $source -Destination $dest -Force -ErrorAction SilentlyContinue
        if (Test-Path $dest) {
            Write-Host "  [OK] Archiviert: $file" -ForegroundColor Green
        }
    }
}

# Lösche Duplikate
$duplicates = @(
    "trafficapp_audit_20251029_141432.zip",
    "routing_osrm_audit_20251105_124528.zip",
    "routing_osrm_audit_20251105_124538.zip",
    "OSRM_POLYGONE_PROBLEM_20251106_204056.zip",
    "OSRM_POLYGONE_PROBLEM_20251106_205624.zip"
)

Write-Host ""
Write-Host "Loesche Duplikate..." -ForegroundColor Yellow
foreach ($file in $duplicates) {
    $path = "ZIP\$file"
    if (Test-Path $path) {
        Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Geloescht: $file" -ForegroundColor Green
    }
}

# Lösche temporäre Test-Dateien
Write-Host ""
Write-Host "Loesche temporaere Test-Dateien..." -ForegroundColor Yellow
$tempFiles = Get-ChildItem -Path "ZIP" -Filter "20251022_081032_*" -ErrorAction SilentlyContinue
foreach ($file in $tempFiles) {
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Geloescht: $($file.Name)" -ForegroundColor Green
}

# Zeige Ergebnis
Write-Host ""
Write-Host "=== Ergebnis ===" -ForegroundColor Cyan
$remainingZips = Get-ChildItem -Path "ZIP" -Filter "*.zip" -ErrorAction SilentlyContinue
$archivedZips = Get-ChildItem -Path $archiveDir -Filter "*.zip" -ErrorAction SilentlyContinue

Write-Host "Verbleibende ZIP-Dateien: $($remainingZips.Count)" -ForegroundColor Green
foreach ($zip in $remainingZips) {
    $sizeKB = [math]::Round($zip.Length / 1KB, 2)
    Write-Host "  - $($zip.Name) ($sizeKB KB)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Archivierte ZIP-Dateien: $($archivedZips.Count)" -ForegroundColor Yellow
foreach ($zip in $archivedZips) {
    $sizeKB = [math]::Round($zip.Length / 1KB, 2)
    Write-Host "  - $($zip.Name) ($sizeKB KB)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[OK] Aufraeumen abgeschlossen!" -ForegroundColor Green

