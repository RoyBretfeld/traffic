# Repariert beschädigtes venv durch Neuinstallation aller Packages
# WICHTIG: Führt KEIN komplettes venv-Neuerstellen durch (zu langsam)

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🔧 VENV REPARIEREN 🔧                                ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
Write-Host ""

# Prüfe ob venv existiert
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ FEHLER: venv nicht gefunden!"
    Write-Host "   Bitte erstelle ein venv: python -m venv venv"
    exit 1
}

Write-Host "✅ venv gefunden"
Write-Host ""

# Aktiviere venv
Write-Host "🔄 Aktiviere venv..."
& "venv\Scripts\Activate.ps1"

# Lösche beschädigte dist-info Verzeichnisse
Write-Host "🧹 Lösche beschädigte Metadaten..."
Get-ChildItem -Path "venv\Lib\site-packages" -Filter "*.dist-info" -Directory -ErrorAction SilentlyContinue | 
    Where-Object { !(Test-Path "$($_.FullName)\METADATA") } | 
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Installiere pip neu
Write-Host "📦 Installiere pip neu..."
python -m pip install --force-reinstall --no-deps pip

# Installiere setuptools neu
Write-Host "📦 Installiere setuptools neu..."
python -m pip install --force-reinstall --no-deps setuptools wheel

# Installiere alle Dependencies neu
Write-Host "📦 Installiere alle Dependencies neu (kann einige Minuten dauern)..."
python -m pip install --force-reinstall --no-cache-dir -r requirements.txt

Write-Host ""
Write-Host "✅ VENV repariert!"
Write-Host ""
Write-Host "🧪 Teste SQLAlchemy..."
python -c "from sqlalchemy import text; print('✅ SQLAlchemy funktioniert!')"

Write-Host ""
Write-Host "🚀 Du kannst jetzt den Server starten:"
Write-Host "   python start_server.py"
Write-Host ""

