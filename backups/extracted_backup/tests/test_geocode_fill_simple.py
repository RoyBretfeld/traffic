import pytest
from unittest.mock import patch, MagicMock
import asyncio

def test_fill_missing_empty_list():
    """Test mit leerer Adressliste."""
    from services.geocode_fill import fill_missing
    
    result = asyncio.run(fill_missing([], limit=10, dry_run=True))
    
    assert len(result) == 1  # Nur Meta
    meta = result[0]["_meta"]
    assert meta["count"] == 0
    assert meta["dry_run"] is True

def test_fill_missing_basic_functionality():
    """Einfacher Test der Grundfunktionalität."""
    from services.geocode_fill import fill_missing
    
    # Mock der gesamten httpx.AsyncClient Klasse
    with patch('services.geocode_fill.httpx.AsyncClient') as mock_client:
        # Mock für den Client-Kontext-Manager
        mock_client_instance = MagicMock()
        
        # Mock für die get-Methode
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "50.1", "lon": "8.6"}]
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        
        # Mock für den Kontext-Manager
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Test
        result = asyncio.run(fill_missing(["Test Adresse"], limit=1, dry_run=True))
        
        # Validierung
        assert len(result) == 2  # 1 Ergebnis + 1 Meta
        assert any("result" in x for x in result)
        assert any("_meta" in x for x in result)
        
        # Meta prüfen
        meta = next(x for x in result if "_meta" in x)["_meta"]
        assert meta["count"] == 1
        assert meta["dry_run"] is True

def test_fill_missing_limit():
    """Test der Limit-Funktionalität."""
    from services.geocode_fill import fill_missing
    
    addresses = [f"Adresse {i}" for i in range(10)]
    
    with patch('services.geocode_fill.httpx.AsyncClient') as mock_client:
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "50.0", "lon": "8.0"}]
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = asyncio.run(fill_missing(addresses, limit=3, dry_run=True))
        
        # Sollte nur 3 Adressen verarbeiten
        meta = next(x for x in result if "_meta" in x)["_meta"]
        assert meta["count"] == 3

def test_fill_missing_error_handling():
    """Test der Fehlerbehandlung."""
    from services.geocode_fill import fill_missing
    
    with patch('services.geocode_fill.httpx.AsyncClient') as mock_client:
        mock_client_instance = MagicMock()
        # Mock für HTTP-Fehler
        mock_client_instance.get.side_effect = Exception("Network error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = asyncio.run(fill_missing(["Test Adresse"], limit=1, dry_run=True))
        
        # Sollte trotz Fehler ein Ergebnis zurückgeben
        assert len(result) == 2  # 1 Ergebnis + 1 Meta
        result_item = next(x for x in result if "result" in x)
        assert result_item["result"] is None  # Fehler sollte zu None führen

def test_fill_missing_invalid_response():
    """Test bei ungültigen API-Responses."""
    from services.geocode_fill import fill_missing
    
    with patch('services.geocode_fill.httpx.AsyncClient') as mock_client:
        mock_client_instance = MagicMock()
        # Mock für ungültige Response (leere Liste)
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = asyncio.run(fill_missing(["Test Adresse"], limit=1, dry_run=True))
        
        result_item = next(x for x in result if "result" in x)
        assert result_item["result"] is None  # Leere Liste sollte zu None führen
