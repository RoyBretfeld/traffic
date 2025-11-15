# Server mit Live-Logging starten
# Die Logs werden in logs/debug.log geschrieben UND auf Console angezeigt

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗"
Write-Host "║          🚀 SERVER MIT DEBUG-LOGGING STARTEN 🚀              ║"
Write-Host "╚═══════════════════════════════════════════════════════════════╝"
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

# Server starten (Output geht auch auf Console)
python start_server.py

