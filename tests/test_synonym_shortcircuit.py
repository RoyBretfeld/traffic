# tests/test_synonym_shortcircuit.py
import pytest
import respx
import httpx
from importlib import reload

@pytest.mark.asyncio
@respx.mock
async def test_pf_synonym_skips_geocoder(monkeypatch):
    """Test dass PF-Synonyme den Geocoder umgehen (Short-Circuit)."""
    # Geocoder-Endpoint darf NICHT aufgerufen werden
    route = respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[])
    )

    import repositories.geo_repo as repo
    reload(repo)
    import services.geocode_fill as gf
    reload(gf)

    async with httpx.AsyncClient() as c:
        out = await gf._geocode_one('Jochen - PF', c)

    # Synonym-Treffer sollte zurückkommen
    assert out and out.get('_note') == 'synonym'
    assert out.get('lat') == '51.05'  # Jochen-Koordinaten
    assert out.get('lon') == '13.7373'

@pytest.mark.asyncio
@respx.mock
async def test_sven_synonym_skips_geocoder(monkeypatch):
    """Test dass Sven-PF-Synonyme den Geocoder umgehen."""
    # Geocoder-Endpoint darf NICHT aufgerufen werden
    route = respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[])
    )

    import repositories.geo_repo as repo
    reload(repo)
    import services.geocode_fill as gf
    reload(gf)

    async with httpx.AsyncClient() as c:
        out = await gf._geocode_one('Sven - PF', c)

    # Synonym-Treffer sollte zurückkommen
    assert out and out.get('_note') == 'synonym'
    assert out.get('lat') == '51.06'  # Sven-Koordinaten
    assert out.get('lon') == '13.73'

def test_synonym_resolution():
    """Test dass Synonym-Auflösung korrekt funktioniert."""
    from common.synonyms import resolve_synonym
    
    # Test verschiedene Schreibweisen
    test_cases = [
        ('Jochen - PF', 'PF:JOCHEN'),
        ('PF JOCHEN', 'PF:JOCHEN'),
        ('Sven - PF', 'PF:SVEN'),
        ('PF SVEN', 'PF:SVEN'),
    ]
    
    for input_name, expected_key in test_cases:
        hit = resolve_synonym(input_name)
        assert hit is not None, f"Synonym für '{input_name}' sollte gefunden werden"
        assert hit.key == expected_key, f"Falscher Key für '{input_name}': {hit.key} != {expected_key}"

def test_synonym_coordinates():
    """Test dass Synonym-Koordinaten korrekt sind."""
    from common.synonyms import resolve_synonym
    
    # Jochen-Koordinaten testen
    jochen = resolve_synonym('Jochen - PF')
    assert jochen is not None
    assert jochen.lat == 51.0500
    assert jochen.lon == 13.7373
    assert jochen.resolved_address == "Pf-Depot Jochen, Dresden"
    
    # Sven-Koordinaten testen
    sven = resolve_synonym('Sven - PF')
    assert sven is not None
    assert sven.lat == 51.0600
    assert sven.lon == 13.7300
    assert sven.resolved_address == "Pf-Depot Sven, Dresden"

def test_synonym_customer_numbers():
    """Test dass Kundennummern für Synonyme korrekt aufgelöst werden."""
    from common.synonyms import resolve_customer_number
    
    # Test Kundennummern-Auflösung
    jochen_num = resolve_customer_number('Jochen - PF')
    assert jochen_num == 9999  # Beispiel-Kundennummer
    
    sven_num = resolve_customer_number('Sven - PF')
    assert sven_num == 9998  # Beispiel-Kundennummer
    
    # Nicht-Synonym sollte None zurückgeben
    normal_num = resolve_customer_number('Normale Firma')
    assert normal_num is None