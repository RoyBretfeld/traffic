# FAMO TrafficApp - Ollama Setup Script

Write-Host "🤖 FAMO TrafficApp - Ollama Setup" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Modell-Pfad setzen
$ModelsPath = "$PSScriptRoot"
$env:OLLAMA_MODELS = $ModelsPath
Write-Host "📁 Modell-Pfad gesetzt: $ModelsPath" -ForegroundColor Yellow

# Prüfen ob Ollama läuft
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Ollama läuft bereits!" -ForegroundColor Green
    
    # Modelle anzeigen
    $models = ($response.Content | ConvertFrom-Json).models
    if ($models -and $models.Count -gt 0) {
        Write-Host "📦 Verfügbare Modelle:" -ForegroundColor Cyan
        foreach ($model in $models) {
            Write-Host "  - $($model.name)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  Keine Modelle installiert" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Ollama läuft nicht oder ist nicht installiert" -ForegroundColor Red
    Write-Host "📥 Bitte installieren Sie Ollama von: https://ollama.com" -ForegroundColor Yellow
    Write-Host "🚀 Dann starten Sie: ollama serve" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Nächste Schritte:" -ForegroundColor Green
Write-Host "1. Ollama starten: ollama serve" -ForegroundColor White
Write-Host "2. Modell laden: ollama pull qwen2.5:0.5b" -ForegroundColor White
Write-Host "3. FAMO Server neu starten" -ForegroundColor White

Read-Host "Drücken Sie Enter zum Beenden"
