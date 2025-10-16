import pytest
import json
from services.geocode_fill import fill_missing
import httpx
from unittest.mock import AsyncMock, patch
import asyncio

@pytest.mark.asyncio
async def test_fill_missing_mocked():
    """Test des Geocoding-Services mit gemockten HTTP-Responses."""
    
    # Mock für httpx.AsyncClient
    mock_response1 = httpx.Response(
        200,
        json=[{"lat": "50.1", "lon": "8.6", "display_name": "Fröbelstraße 1, Frankfurt"}]
    )
    mock_response2 = httpx.Response(
        200,
        json=[{"lat": "51.05", "lon": "13.74", "display_name": "Löbtauer Straße 2, Dresden"}]
    )
    
    with patch('httpx.AsyncClient') as mock_client:
        # Mock des Client-Kontextmanagers
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = [mock_response1, mock_response2]
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Test mit dry_run=True (keine DB-Updates)
        out = await fill_missing(["Fröbelstraße 1", "Löbtauer Straße 2"], limit=2, dry_run=True)
        
        # Validierung
        assert len(out) == 3  # 2 Ergebnisse + 1 Meta
        assert any(isinstance(x.get("result"), dict) for x in out)
        assert any("_meta" in x for x in out)
        
        # Meta-Informationen prüfen
        meta = next(x for x in out if "_meta" in x)["_meta"]
        assert meta["count"] == 2
        assert meta["dry_run"] is True
        assert meta["t_sec"] > 0

@pytest.mark.asyncio
async def test_fill_missing_empty_list():
    """Test mit leerer Adressliste."""
    out = await fill_missing([], limit=10, dry_run=True)
    
    assert len(out) == 1  # Nur Meta
    meta = out[0]["_meta"]
    assert meta["count"] == 0
    assert meta["dry_run"] is True

@pytest.mark.asyncio
async def test_fill_missing_limit():
    """Test der Limit-Funktionalität."""
    addresses = [f"Adresse {i}" for i in range(10)]
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        # Mock für erfolgreiche Geocoding-Responses
        mock_response = httpx.Response(200, json=[{"lat": "50.0", "lon": "8.0"}])
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        out = await fill_missing(addresses, limit=3, dry_run=True)
        
        # Sollte nur 3 Adressen verarbeiten
        meta = next(x for x in out if "_meta" in x)["_meta"]
        assert meta["count"] == 3

@pytest.mark.asyncio
async def test_fill_missing_http_error():
    """Test bei HTTP-Fehlern."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        # Mock für HTTP-Fehler
        mock_client_instance.get.side_effect = httpx.HTTPError("Network error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        out = await fill_missing(["Test Adresse"], limit=1, dry_run=True)
        
        # Sollte trotz Fehler ein Ergebnis zurückgeben
        assert len(out) == 2  # 1 Ergebnis + 1 Meta
        result = next(x for x in out if "result" in x)
        assert result["result"] is None  # Fehler sollte zu None führen

@pytest.mark.asyncio
async def test_fill_missing_invalid_response():
    """Test bei ungültigen API-Responses."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        # Mock für ungültige Response (leere Liste)
        mock_response = httpx.Response(200, json=[])
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        out = await fill_missing(["Test Adresse"], limit=1, dry_run=True)
        
        result = next(x for x in out if "result" in x)
        assert result["result"] is None  # Leere Liste sollte zu None führen

@pytest.mark.asyncio
async def test_fill_missing_deduplication():
    """Test der Adress-Deduplizierung."""
    # Gleiche Adresse mehrfach
    addresses = ["Löbtauer Straße 1", "Löbtauer Straße 1", "Hauptstraße 42"]
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client_instance = AsyncMock()
        mock_response = httpx.Response(200, json=[{"lat": "50.0", "lon": "8.0"}])
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        out = await fill_missing(addresses, limit=10, dry_run=True)
        
        # Sollte nur 2 unique Adressen verarbeiten
        meta = next(x for x in out if "_meta" in x)["_meta"]
        assert meta["count"] == 2
