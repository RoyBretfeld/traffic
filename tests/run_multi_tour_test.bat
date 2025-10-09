@echo off
echo 🚀 Multi-Tour Generator Test Suite
echo =================================

echo.
echo 🔍 Prüfe ob Server läuft...
curl -s http://localhost:8111/api/llm-status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Server läuft auf Port 8111
) else (
    echo ❌ Server läuft nicht! Bitte starten Sie den Server mit: python start_server.py
    pause
    exit /b 1
)

echo.
echo 🔍 Prüfe ob Ollama läuft...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama läuft
) else (
    echo ⚠️ Ollama läuft nicht - Tests verwenden Fallback
)

echo.
echo 🧪 Führe Tests aus...
echo =================================

python tests/test_multi_tour_generator.py

echo.
echo ✅ Test Suite abgeschlossen!
echo =================================
pause
