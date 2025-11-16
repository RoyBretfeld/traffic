# Einfacher Server-Start mit venv
# WICHTIG: Aktiviert venv, prüft Health und startet Server mit venv-Python

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🚀 SERVER STARTEN (MIT HEALTH CHECK) 🚀             ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

# Prüfe venv
if (!(Test-Path "venv\Scripts\python.exe")) {
    Write-Host "❌ FEHLER: venv nicht gefunden!"
    Write-Host "   Bitte erstelle venv: python -m venv venv"
    exit 1
}

# Aktiviere venv
Write-Host "🔄 Aktiviere venv..."
& "venv\Scripts\Activate.ps1"

# Verwende venv-Python direkt
$venvPython = (Resolve-Path "venv\Scripts\python.exe").Path
Write-Host "   Python: $venvPython"
Write-Host ""

# Health Check (optional, wird auch in start_server.py gemacht)
Write-Host "🔍 Führe Venv Health Check durch..."
& $venvPython scripts\venv_health_check_standalone.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  WARNUNG: Venv Health Check hat Probleme gefunden"
    Write-Host "   Server startet trotzdem (Health Check wird erneut ausgeführt)"
    Write-Host ""
}

Write-Host ""
Write-Host "🚀 Starte Server..."
Write-Host ""

# Starte Server (Health Check wird automatisch nochmal ausgeführt)
& $venvPython start_server.py

