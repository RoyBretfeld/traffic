# Server mit Live-Logging starten
# Die Logs werden in logs/debug.log geschrieben UND auf Console angezeigt
# WICHTIG: Aktiviert venv automatisch!

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🚀 SERVER MIT DEBUG-LOGGING STARTEN 🚀              ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

# Prüfe und aktiviere venv
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ venv gefunden - aktiviere..."
    & "venv\Scripts\Activate.ps1"
    
    # WICHTIG: Setze Python-Pfad auf venv-Python
    $venvPython = (Resolve-Path "venv\Scripts\python.exe").Path
    $env:PYTHONPATH = $PWD
    Write-Host "   Python: $venvPython"
    
    # Teste SQLAlchemy
    Write-Host "   Teste SQLAlchemy..."
    & $venvPython -c "from sqlalchemy import text; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ SQLAlchemy funktioniert"
    } else {
        Write-Host "   ❌ SQLAlchemy-Fehler! Installiere neu..."
        & $venvPython -m pip install --force-reinstall sqlalchemy==2.0.44
    }
} else {
    Write-Host "❌ FEHLER: venv nicht gefunden!"
    Write-Host "   Bitte erstelle venv: python -m venv venv"
    exit 1
}

Write-Host ""
Write-Host "📝 LOG-DATEI: logs\debug.log"
Write-Host ""
Write-Host "💡 TIPPS:"
Write-Host "  • Console OFFEN lassen"
Write-Host "  • Log-Datei live öffnen:"
Write-Host "    notepad logs\debug.log"
Write-Host ""
Write-Host "🔍 TESTEN:"
Write-Host "  1. Browser: CSV hochladen"
Write-Host "  2. Sub-Routen generieren"
Write-Host "  3. Log-Datei checken!"
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# Lösche alte Log-Datei
if (Test-Path "logs\debug.log") {
    Remove-Item "logs\debug.log" -Force
    Write-Host "✅ Alte Log-Datei gelöscht"
}

# Erstelle logs-Verzeichnis
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "✅ logs/-Verzeichnis erstellt"
}

Write-Host ""
Write-Host "🚀 Starte Server..."
Write-Host ""

# Server starten mit venv-Python (Output geht auch auf Console)
$venvPython = (Resolve-Path "venv\Scripts\python.exe").Path
& $venvPython start_server.py

