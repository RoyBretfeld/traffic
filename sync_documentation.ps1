
# Dokumentations-Synchronisierungs-Skript
# Synchronisiert alle .md Dateien und wichtige Dokumentationsdateien
# Zwischen: C:\Workflow\TrafficApp und C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0

param(
    [string]$Source = "C:\Workflow\TrafficApp",
    [string]$Destination = "C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0",
    [switch]$FullSync
)

function Sync-Documentation {
    param(
        [string]$Source,
        [string]$Destination,
        [bool]$Full
    )
    
    Write-Host "🔄 Starte Dokumentations-Synchronisierung..." -ForegroundColor Cyan
    Write-Host "📁 Quelle:  $Source" -ForegroundColor Gray
    Write-Host "📁 Ziel:    $Destination" -ForegroundColor Gray
    Write-Host ""
    
    # Dokumentations-Dateien
    $docFiles = @(
        "README.md",
        "CHANGELOG.md",
        "CURSOR_RULES.md",
        "ADRESS_ERKENNUNG_DOKUMENTATION.md",
        "SYSTEMABSCHLUSS_DOKUMENTATION.md",
        "MIGRATION_TO_OPENAI.md",
        "README_CSV_PARSING.md",
        "FILE_INPUT_FIX_REPORT.md",
        "STATUS_REPORT.md"
    )
    
    # Dokumentations-Verzeichnisse
    $docDirs = @("docs")
    
    $syncedCount = 0
    $errorCount = 0
    
    # Synchronisiere individuelle Dateien
    foreach ($file in $docFiles) {
        $sourcePath = Join-Path $Source $file
        $destPath = Join-Path $Destination $file
        
        if (Test-Path $sourcePath) {
            try {
                Copy-Item -Path $sourcePath -Destination $destPath -Force -ErrorAction Stop
                Write-Host "✅ $file" -ForegroundColor Green
                $syncedCount++
            }
            catch {
                Write-Host "❌ $file - Fehler: $_" -ForegroundColor Red
                $errorCount++
            }
        }
    }
    
    # Synchronisiere Verzeichnisse (wenn FullSync)
    if ($Full) {
        foreach ($dir in $docDirs) {
            $sourcePath = Join-Path $Source $dir
            $destPath = Join-Path $Destination $dir
            
            if (Test-Path $sourcePath) {
                try {
                    # Entferne altes Verzeichnis und erstelle neu
                    if (Test-Path $destPath) {
                        Remove-Item -Path $destPath -Recurse -Force
                    }
                    Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force -ErrorAction Stop
                    Write-Host "✅ $dir/" -ForegroundColor Green
                    $syncedCount++
                }
                catch {
                    Write-Host "❌ $dir/ - Fehler: $_" -ForegroundColor Red
                    $errorCount++
                }
            }
        }
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "✨ Synchronisierung abgeschlossen!" -ForegroundColor Green
    Write-Host "   ✅ $syncedCount Dateien synchronisiert" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "   ❌ $errorCount Fehler" -ForegroundColor Red
    }
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

# Starte Synchronisierung
Sync-Documentation -Source $Source -Destination $Destination -Full $FullSync

# Automatische Synchronisierung bei Änderungen (optional)
# Kann mit -Watch aktiviert werden für Echtzeit-Überwachung
