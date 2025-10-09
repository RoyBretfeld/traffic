# Multi-Tour Generator Test Suite
# Führt alle 6 Tests für den Multi-Tour Generator aus

Write-Host "🚀 Multi-Tour Generator Test Suite" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Prüfen ob Server läuft
Write-Host "`n🔍 Prüfe ob Server läuft..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8111/api/llm-status" -Method Get -TimeoutSec 5
    Write-Host "✅ Server läuft auf Port 8111" -ForegroundColor Green
} catch {
    Write-Host "❌ Server läuft nicht! Bitte starten Sie den Server mit: python start_server.py" -ForegroundColor Red
    exit 1
}

# Prüfen ob Ollama läuft
Write-Host "`n🔍 Prüfe ob Ollama läuft..." -ForegroundColor Yellow
try {
    $ollamaResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    if ($ollamaResponse.models.Count -gt 0) {
        Write-Host "✅ Ollama läuft mit Modell: $($ollamaResponse.models[0].name)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Ollama läuft, aber keine Modelle geladen" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Ollama läuft nicht - Tests verwenden Fallback" -ForegroundColor Yellow
}

# Test ausführen
Write-Host "`n🧪 Führe Tests aus..." -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Green

python tests/test_multi_tour_generator.py

Write-Host "`n✅ Test Suite abgeschlossen!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
