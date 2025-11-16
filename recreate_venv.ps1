# Erstellt venv komplett neu
# WICHTIG: Löscht das alte venv und erstellt ein neues!

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🔄 VENV NEU ERSTELLEN 🔄                             ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "⚠️  WARNUNG: Dies löscht das aktuelle venv und erstellt ein neues!"
Write-Host ""

$confirm = Read-Host "Fortfahren? (j/n)"
if ($confirm -ne "j" -and $confirm -ne "J" -and $confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Abgebrochen."
    exit 0
}

Write-Host ""
Write-Host "🗑️  Lösche altes venv..."
if (Test-Path "venv") {
    Remove-Item -Path "venv" -Recurse -Force
    Write-Host "✅ Altes venv gelöscht"
}

Write-Host ""
Write-Host "🆕 Erstelle neues venv..."
python -m venv venv

Write-Host ""
Write-Host "🔄 Aktiviere venv..."
& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "📦 Upgrade pip..."
python -m pip install --upgrade pip

Write-Host ""
Write-Host "📦 Installiere alle Dependencies (kann einige Minuten dauern)..."
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "✅ VENV neu erstellt!"
Write-Host ""
Write-Host "🧪 Teste SQLAlchemy..."
python -c "from sqlalchemy import text; print('✅ SQLAlchemy funktioniert!')"

Write-Host ""
Write-Host "🚀 Du kannst jetzt den Server starten:"
Write-Host "   python start_server.py"
Write-Host "   ODER: .\START_SERVER_WITH_LOGS.ps1"
Write-Host ""

