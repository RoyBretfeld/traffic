import pytest
import json
from unittest.mock import patch, MagicMock
import asyncio

def test_fill_missing_sync():
    """Synchroner Test des Geocoding-Services."""
    from services.geocode_fill import fill_missing
    
    # Mock für httpx.AsyncClient
    mock_response1 = MagicMock()
    mock_response1.json.return_value = [{"lat": "50.1", "lon": "8.6"}]
    mock_response1.raise_for_status.return_value = None
    
    mock_response2 = MagicMock()
    mock_response2.json.return_value = [{"lat": "51.05", "lon": "13.74"}]
    mock_response2.raise_for_status.return_value = None
    
    async def mock_get(url):
        if "Fröbelstraße" in url:
            return mock_response1
        else:
            return mock_response2
    
    async def mock_client_context():
        client = MagicMock()
        client.get = mock_get
        return client
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_class.return_value.__aenter__ = mock_client_context
        
        # Test mit dry_run=True
        result = asyncio.run(fill_missing(["Fröbelstraße 1", "Löbtauer Straße 2"], limit=2, dry_run=True))
        
        # Validierung
        assert len(result) == 3  # 2 Ergebnisse + 1 Meta
        assert any(isinstance(x.get("result"), dict) for x in result)
        assert any("_meta" in x for x in result)
        
        # Meta-Informationen prüfen
        meta = next(x for x in result if "_meta" in x)["_meta"]
        assert meta["count"] == 2
        assert meta["dry_run"] is True
        assert meta["t_sec"] > 0

def test_fill_missing_empty_list():
    """Test mit leerer Adressliste."""
    from services.geocode_fill import fill_missing
    
    result = asyncio.run(fill_missing([], limit=10, dry_run=True))
    
    assert len(result) == 1  # Nur Meta
    meta = result[0]["_meta"]
    assert meta["count"] == 0
    assert meta["dry_run"] is True

def test_fill_missing_limit():
    """Test der Limit-Funktionalität."""
    from services.geocode_fill import fill_missing
    
    addresses = [f"Adresse {i}" for i in range(10)]
    
    # Mock für erfolgreiche Responses
    mock_response = MagicMock()
    mock_response.json.return_value = [{"lat": "50.0", "lon": "8.0"}]
    mock_response.raise_for_status.return_value = None
    
    async def mock_get(url):
        return mock_response
    
    async def mock_client_context():
        client = MagicMock()
        client.get = mock_get
        return client
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_class.return_value.__aenter__ = mock_client_context
        
        result = asyncio.run(fill_missing(addresses, limit=3, dry_run=True))
        
        # Sollte nur 3 Adressen verarbeiten
        meta = next(x for x in result if "_meta" in x)["_meta"]
        assert meta["count"] == 3

def test_fill_missing_http_error():
    """Test bei HTTP-Fehlern."""
    from services.geocode_fill import fill_missing
    
    async def mock_get(url):
        raise Exception("Network error")
    
    async def mock_client_context():
        client = MagicMock()
        client.get = mock_get
        return client
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_class.return_value.__aenter__ = mock_client_context
        
        result = asyncio.run(fill_missing(["Test Adresse"], limit=1, dry_run=True))
        
        # Sollte trotz Fehler ein Ergebnis zurückgeben
        assert len(result) == 2  # 1 Ergebnis + 1 Meta
        result_item = next(x for x in result if "result" in x)
        assert result_item["result"] is None  # Fehler sollte zu None führen

def test_fill_missing_invalid_response():
    """Test bei ungültigen API-Responses."""
    from services.geocode_fill import fill_missing
    
    # Mock für ungültige Response (leere Liste)
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    
    async def mock_get(url):
        return mock_response
    
    async def mock_client_context():
        client = MagicMock()
        client.get = mock_get
        return client
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_class.return_value.__aenter__ = mock_client_context
        
        result = asyncio.run(fill_missing(["Test Adresse"], limit=1, dry_run=True))
        
        result_item = next(x for x in result if "result" in x)
        assert result_item["result"] is None  # Leere Liste sollte zu None führen

def test_fill_missing_deduplication():
    """Test der Adress-Deduplizierung."""
    from services.geocode_fill import fill_missing
    
    # Gleiche Adresse mehrfach
    addresses = ["Löbtauer Straße 1", "Löbtauer Straße 1", "Hauptstraße 42"]
    
    mock_response = MagicMock()
    mock_response.json.return_value = [{"lat": "50.0", "lon": "8.0"}]
    mock_response.raise_for_status.return_value = None
    
    async def mock_get(url):
        return mock_response
    
    async def mock_client_context():
        client = MagicMock()
        client.get = mock_get
        return client
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client_class.return_value.__aenter__ = mock_client_context
        
        result = asyncio.run(fill_missing(addresses, limit=10, dry_run=True))
        
        # Sollte nur 2 unique Adressen verarbeiten
        meta = next(x for x in result if "_meta" in x)["_meta"]
        assert meta["count"] == 2
