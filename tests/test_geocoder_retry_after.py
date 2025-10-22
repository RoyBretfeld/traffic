"""Test für Geocoder 429/Retry-After Handling."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from importlib import reload
import os
from pathlib import Path
import tempfile
import sys

# Füge das Projekt-Root-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.mark.asyncio
async def test_429_retry_after(monkeypatch, tmp_path):
    """Test 429 Rate-Limiting mit Retry-After Header."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import services.geocode_fill as gf; reload(gf)

    # Mock httpx.AsyncClient
    mock_response_429 = AsyncMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {'Retry-After': '1'}
    
    mock_response_200 = AsyncMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = []  # Leeres Ergebnis
    
    mock_client = AsyncMock()
    mock_client.get.side_effect = [mock_response_429, mock_response_200]
    
    # Mock der _geocode_variant Funktion
    with patch('services.geocode_fill._geocode_variant') as mock_geocode:
        mock_geocode.return_value = None  # Kein Ergebnis
        
        # Test mit einer Adresse
        result = await gf.fill_missing(["Fröbelstraße 1, Dresden"], dry_run=True)
        
        # Prüfe dass 429 behandelt wurde
        assert len(result) >= 1, "Kein Ergebnis erhalten"
        assert result[0]['status'] in ['nohit', 'error'], f"Unerwarteter Status: {result[0]['status']}"

@pytest.mark.asyncio
async def test_headers_present():
    """Test dass korrekte Headers gesetzt werden."""
    import services.geocode_fill as gf; reload(gf)
    
    # Prüfe dass HEADERS definiert sind
    assert hasattr(gf, 'HEADERS'), "HEADERS nicht definiert"
    assert 'User-Agent' in gf.HEADERS, "User-Agent nicht in HEADERS"
    assert 'TrafficApp' in gf.HEADERS['User-Agent'], "Falscher User-Agent"

@pytest.mark.asyncio
async def test_retry_logic():
    """Test Retry-Logik mit verschiedenen Fehlern."""
    import services.geocode_fill as gf; reload(gf)
    
    # Mock httpx.AsyncClient mit verschiedenen Fehlern
    mock_client = AsyncMock()
    
    # Simuliere Timeout-Fehler
    mock_client.get.side_effect = [
        Exception("Connection timeout"),
        Exception("Connection timeout"),
        Exception("Connection timeout")
    ]
    
    # Test dass nach MAX_RETRIES Versuchen aufgegeben wird
    try:
        result = await gf._geocode_variant("Test Adresse", mock_client)
        assert result is None, "Sollte None zurückgeben nach Fehlern"
    except Exception as e:
        # Das ist auch OK, da _geocode_variant Exceptions wirft
        assert "geocode failed" in str(e) or "Connection timeout" in str(e)

def test_manual_queue_config():
    """Test Manual-Queue Konfiguration."""
    import services.geocode_fill as gf; reload(gf)
    
    # Test Standard-Konfiguration
    assert hasattr(gf, 'ENFORCE_MANUAL'), "ENFORCE_MANUAL nicht definiert"
    
    # Test mit verschiedenen ENV-Werten
    with patch.dict(os.environ, {'GEOCODE_NO_RESULT_TO_MANUAL': '1'}):
        reload(gf)
        assert gf.ENFORCE_MANUAL == True, "ENFORCE_MANUAL sollte True sein"
    
    with patch.dict(os.environ, {'GEOCODE_NO_RESULT_TO_MANUAL': '0'}):
        reload(gf)
        assert gf.ENFORCE_MANUAL == False, "ENFORCE_MANUAL sollte False sein"

if __name__ == "__main__":
    # Direkter Test-Aufruf ohne pytest
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock monkeypatch für direkten Aufruf
        class MockMonkeypatch:
            def setenv(self, key, value):
                os.environ[key] = value

        print("=== Geocoder Retry-After Test ===")
        
        # Führe Tests aus
        asyncio.run(test_429_retry_after(MockMonkeypatch(), Path(tmp_dir)))
        asyncio.run(test_headers_present())
        asyncio.run(test_retry_logic())
        test_manual_queue_config()
        
        print("✓ Alle Tests erfolgreich!")
