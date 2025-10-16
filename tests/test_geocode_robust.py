import pytest
import httpx
import respx
from unittest.mock import patch
from repositories.geo_fail_repo import skip_set, mark_temp, mark_nohit, clear, get_fail_stats
from services.geocode_fill import fill_missing

@pytest.mark.asyncio
@respx.mock
async def test_429_retry_and_nohit(monkeypatch):
    """Test 429 Rate-Limiting mit Retry-After und No-Hit-Behandlung."""
    # Mock Nominatim-Endpoint
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "1"}),
        httpx.Response(200, json=[{"lat": "51.05", "lon": "13.74"}]),
        httpx.Response(200, json=[]),  # zweite Adresse: kein Treffer
    ]
    
    # Test mit dry_run=True (keine DB-Updates)
    out = await fill_missing(["Fröbelstraße 1", "Nicht Existente 999"], limit=2, dry_run=True)
    
    # Prüfe Ergebnisse
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 2
    
    # Erste Adresse sollte erfolgreich sein
    ok_result = next((r for r in results if r.get("status") == "ok"), None)
    assert ok_result is not None
    assert ok_result["result"]["lat"] == 51.05
    assert ok_result["result"]["lon"] == 13.74
    
    # Zweite Adresse sollte No-Hit sein
    nohit_result = next((r for r in results if r.get("status") == "nohit"), None)
    assert nohit_result is not None
    assert nohit_result["result"] is None

@pytest.mark.asyncio
@respx.mock
async def test_temp_errors_marked(monkeypatch):
    """Test dass temporäre Fehler im Fail-Cache markiert werden."""
    # Mock Timeout-Fehler
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        side_effect=httpx.ConnectTimeout("Connection timeout")
    )
    
    # Test mit dry_run=False (DB-Updates aktiviert)
    out = await fill_missing(["Löbtauer Straße 2"], limit=1, dry_run=False)
    
    # Sollte Fehlerstatus liefern
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "error"
    assert "timeout" in results[0].get("error", "").lower()
    
    # Fail-Cache sollte die Adresse enthalten
    skip_addresses = skip_set(["Löbtauer Straße 2"])
    assert "Löbtauer Straße 2" in skip_addresses

@pytest.mark.asyncio
@respx.mock
async def test_fail_cache_skip_functionality(monkeypatch):
    """Test dass Fail-Cache-Adressen übersprungen werden."""
    # Adresse im Fail-Cache markieren
    mark_temp("Test Straße 123", minutes=60, reason="test_error")
    
    # Mock für Nominatim (sollte nicht aufgerufen werden)
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(return_value=httpx.Response(200, json=[{"lat": "50.0", "lon": "8.0"}]))
    
    # Test mit Adressen, eine davon im Fail-Cache
    out = await fill_missing(["Test Straße 123", "Normale Straße 456"], limit=2, dry_run=True)
    
    # Prüfe dass nur eine Adresse verarbeitet wurde
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1  # Nur "Normale Straße 456" sollte verarbeitet werden
    assert results[0]["address"] == "Normale Straße 456"
    
    # Nominatim sollte nur einmal aufgerufen worden sein
    assert route.calls.call_count == 1

@pytest.mark.asyncio
@respx.mock
async def test_success_clears_fail_cache(monkeypatch):
    """Test dass erfolgreiche Geocoding-Adressen aus dem Fail-Cache entfernt werden."""
    # Adresse im Fail-Cache markieren
    mark_temp("Erfolgreiche Straße 789", minutes=60, reason="test_error")
    
    # Mock erfolgreiche Antwort
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(return_value=httpx.Response(200, json=[{"lat": "51.0", "lon": "13.0"}]))
    
    # Test mit dry_run=False
    out = await fill_missing(["Erfolgreiche Straße 789"], limit=1, dry_run=False)
    
    # Sollte erfolgreich sein
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "ok"
    
    # Fail-Cache sollte die Adresse nicht mehr enthalten
    skip_addresses = skip_set(["Erfolgreiche Straße 789"])
    assert "Erfolgreiche Straße 789" not in skip_addresses

@pytest.mark.asyncio
@respx.mock
async def test_nohit_marked_correctly(monkeypatch):
    """Test dass No-Hit-Adressen korrekt markiert werden."""
    # Mock leere Antwort (No-Hit)
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(return_value=httpx.Response(200, json=[]))
    
    # Test mit dry_run=False
    out = await fill_missing(["Nicht Existente Straße 999"], limit=1, dry_run=False)
    
    # Sollte No-Hit-Status haben
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "nohit"
    assert results[0]["result"] is None
    
    # Fail-Cache sollte die Adresse enthalten
    skip_addresses = skip_set(["Nicht Existente Straße 999"])
    assert "Nicht Existente Straße 999" in skip_addresses

def test_fail_cache_stats():
    """Test der Fail-Cache-Statistiken."""
    # Zuerst Cache leeren
    clear("Test Statistik Adresse")
    
    # Statistiken abrufen
    stats = get_fail_stats()
    initial_total = stats["total"]
    
    # Adresse markieren
    mark_temp("Test Statistik Adresse", minutes=60, reason="test_stats")
    
    # Statistiken erneut abrufen
    stats = get_fail_stats()
    assert stats["total"] == initial_total + 1
    assert stats["active"] >= 1  # Mindestens eine aktive Adresse
    
    # Cleanup
    clear("Test Statistik Adresse")

@pytest.mark.asyncio
@respx.mock
async def test_exponential_backoff_on_timeout(monkeypatch):
    """Test exponentielles Backoff bei Timeout-Fehlern."""
    # Mock Timeout-Fehler für alle Versuche
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(side_effect=httpx.ReadTimeout("Read timeout"))
    
    # Test mit dry_run=True
    out = await fill_missing(["Timeout Test Straße"], limit=1, dry_run=True)
    
    # Sollte Fehlerstatus haben
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "error"
    
    # Nominatim sollte 3 Mal aufgerufen worden sein (MAX_RETRIES)
    assert route.calls.call_count == 3
