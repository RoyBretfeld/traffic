import pytest
import httpx
import respx
from unittest.mock import patch
from pathlib import Path
import tempfile
import os

@pytest.fixture
def temp_db(monkeypatch):
    """Erstellt eine temporäre SQLite-Datenbank für Tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    # Setze DATABASE_URL für Tests
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    
    # Initialisiere DB-Schema
    from importlib import reload
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import db.schema_fail as schema_fail; reload(schema_fail); schema_fail.ensure_fail_schema()
    
    return db_path

def test_fail_cache_basic_functionality(temp_db):
    """Test grundlegende Fail-Cache-Funktionalität."""
    from repositories.geo_fail_repo import skip_set, mark_temp, mark_nohit, clear, get_fail_stats
    
    # Zuerst Cache leeren
    clear("Test Adresse")
    
    # Statistiken abrufen
    stats = get_fail_stats()
    initial_total = stats["total"]
    
    # Adresse markieren
    mark_temp("Test Adresse", minutes=60, reason="test_error")
    
    # Statistiken erneut abrufen
    stats = get_fail_stats()
    assert stats["total"] == initial_total + 1
    assert stats["active"] >= 1
    
    # Adresse sollte im Skip-Set sein
    skip_addresses = skip_set(["Test Adresse"])
    assert "Test Adresse" in skip_addresses
    
    # Adresse löschen
    clear("Test Adresse")
    
    # Adresse sollte nicht mehr im Skip-Set sein
    skip_addresses = skip_set(["Test Adresse"])
    assert "Test Adresse" not in skip_addresses

def test_nohit_marking(temp_db):
    """Test No-Hit-Markierung."""
    from repositories.geo_fail_repo import skip_set, mark_nohit, clear
    
    # No-Hit markieren
    mark_nohit("Nicht Existente Straße", minutes=1440, reason="no_result")
    
    # Adresse sollte im Skip-Set sein
    skip_addresses = skip_set(["Nicht Existente Straße"])
    assert "Nicht Existente Straße" in skip_addresses
    
    # Cleanup
    clear("Nicht Existente Straße")

@pytest.mark.asyncio
@respx.mock
async def test_geocode_retry_basic(temp_db):
    """Test grundlegende Retry-Funktionalität."""
    from services.geocode_fill import fill_missing
    
    # Mock erfolgreiche Antwort
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(return_value=httpx.Response(200, json=[{"lat": "51.0", "lon": "13.0"}]))
    
    # Test mit dry_run=True
    out = await fill_missing(["Test Straße 123"], limit=1, dry_run=True)
    
    # Prüfe Ergebnisse
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "ok"
    assert results[0]["result"]["lat"] == 51.0
    assert results[0]["result"]["lon"] == 13.0

@pytest.mark.asyncio
@respx.mock
async def test_geocode_429_handling(temp_db):
    """Test 429 Rate-Limiting-Behandlung."""
    from services.geocode_fill import fill_missing
    
    # Mock 429 dann Erfolg
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "1"}),
        httpx.Response(200, json=[{"lat": "51.0", "lon": "13.0"}])
    ]
    
    # Test mit dry_run=True
    out = await fill_missing(["Test Straße 456"], limit=1, dry_run=True)
    
    # Sollte erfolgreich sein trotz 429
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "ok"
    
    # Nominatim sollte 2 Mal aufgerufen worden sein (429 + Erfolg)
    assert route.calls.call_count == 2

@pytest.mark.asyncio
@respx.mock
async def test_geocode_timeout_handling(temp_db):
    """Test Timeout-Behandlung."""
    from services.geocode_fill import fill_missing
    
    # Mock Timeout-Fehler
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(side_effect=httpx.ReadTimeout("Read timeout"))
    
    # Test mit dry_run=True
    out = await fill_missing(["Test Straße 789"], limit=1, dry_run=True)
    
    # Sollte Fehlerstatus haben
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "error"
    assert "timeout" in results[0].get("error", "").lower()
    
    # Nominatim sollte 3 Mal aufgerufen worden sein (MAX_RETRIES)
    assert route.calls.call_count == 3

@pytest.mark.asyncio
@respx.mock
async def test_geocode_nohit_handling(temp_db):
    """Test No-Hit-Behandlung."""
    from services.geocode_fill import fill_missing
    
    # Mock leere Antwort (No-Hit)
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.mock(return_value=httpx.Response(200, json=[]))
    
    # Test mit dry_run=True
    out = await fill_missing(["Nicht Existente Straße"], limit=1, dry_run=True)
    
    # Sollte No-Hit-Status haben
    results = [o for o in out if not o.get("_meta")]
    assert len(results) == 1
    assert results[0].get("status") == "nohit"
    assert results[0]["result"] is None
