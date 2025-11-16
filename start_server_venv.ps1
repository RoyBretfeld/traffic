# Server mit aktiviertem venv starten
# Löst das SQLAlchemy-Import-Problem

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🚀 SERVER MIT VENV STARTEN 🚀                      ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

# Prüfe ob venv existiert
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ FEHLER: venv nicht gefunden!"
    Write-Host "   Bitte erstelle ein venv: python -m venv venv"
    Write-Host "   Dann installiere Dependencies: .\venv\Scripts\Activate.ps1; pip install -r requirements.txt"
    exit 1
}

Write-Host "✅ venv gefunden"
Write-Host ""

# Aktiviere venv
Write-Host "🔄 Aktiviere venv..."
& "venv\Scripts\Activate.ps1"

# Prüfe SQLAlchemy
Write-Host "🔍 Prüfe SQLAlchemy..."
$sqlalchemy = python -m pip show sqlalchemy 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SQLAlchemy nicht gefunden!"
    Write-Host "   Installiere Dependencies..."
    pip install -r requirements.txt
} else {
    Write-Host "✅ SQLAlchemy gefunden"
}

Write-Host ""
Write-Host "🚀 Starte Server..."
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# Server starten
python start_server.py

