# tests/test_stop_dto_valid.py
from services.stop_dto import build_stop_dto, build_stop_dto_from_stop

def test_dto_valid_and_resolved_address():
    """Test dass DTO mit gültigen Koordinaten korrekt erstellt wird."""
    dto = build_stop_dto(
        stop_id='X1', 
        display_name='Jochen - PF',
        resolved_address='Pf-Depot Jochen, Dresden',
        lat=51.05, 
        lon=13.74, 
        geo_source='synonym'
    )
    
    assert dto['valid'] is True
    assert dto['id'] == 'X1'
    assert dto['display_name'] == 'Jochen - PF'
    assert 'resolved_address' in dto and dto['resolved_address'].startswith('Pf-Depot')
    assert dto['lat'] == 51.05
    assert dto['lon'] == 13.74
    assert dto['geo_source'] == 'synonym'

def test_dto_invalid_without_coords():
    """Test dass DTO ohne Koordinaten als invalid markiert wird."""
    dto = build_stop_dto(
        stop_id='X2', 
        display_name='Sven - PF',
        resolved_address='Pf-Depot Sven, Dresden',
        lat=None, 
        lon=None, 
        geo_source='synonym'
    )
    
    assert dto['valid'] is False
    assert dto['lat'] is None
    assert dto['lon'] is None
    assert dto['geo_source'] == 'synonym'

def test_dto_with_extra_fields():
    """Test dass zusätzliche Felder korrekt hinzugefügt werden."""
    extra = {
        "status": "ok",
        "markers": [],
        "manual_needed": False
    }
    
    dto = build_stop_dto(
        stop_id='X3',
        display_name='Test Firma',
        resolved_address='Teststraße 1, 01069 Dresden',
        lat=51.05,
        lon=13.74,
        geo_source='cache',
        extra=extra
    )
    
    assert dto['valid'] is True
    assert dto['status'] == 'ok'
    assert dto['markers'] == []
    assert dto['manual_needed'] is False

def test_dto_from_stop_object():
    """Test dass DTO aus Stop-Objekt korrekt erstellt wird."""
    class MockStop:
        def __init__(self):
            self.id = 'STOP123'
            self.name = 'Mock Firma'
            self.address = 'Mockstraße 1, 01069 Dresden'
            self.lat = 51.05
            self.lon = 13.74
            self.geo_source = 'cache'
    
    stop = MockStop()
    dto = build_stop_dto_from_stop(stop)
    
    assert dto['valid'] is True
    assert dto['id'] == 'STOP123'
    assert dto['display_name'] == 'Mock Firma'
    assert dto['resolved_address'] == 'Mockstraße 1, 01069 Dresden'
    assert dto['lat'] == 51.05
    assert dto['lon'] == 13.74
    assert dto['geo_source'] == 'cache'

def test_dto_validation_edge_cases():
    """Test Edge-Cases für DTO-Validierung."""
    # Test mit String-Koordinaten (sollte invalid sein)
    dto1 = build_stop_dto(
        stop_id='X4',
        display_name='Test',
        resolved_address='Test',
        lat="51.05",  # String statt float
        lon="13.74",  # String statt float
        geo_source='cache'
    )
    assert dto1['valid'] is False
    
    # Test mit 0-Koordinaten (sollte valid sein, da es gültige Zahlen sind)
    dto2 = build_stop_dto(
        stop_id='X5',
        display_name='Test',
        resolved_address='Test',
        lat=0.0,
        lon=0.0,
        geo_source='cache'
    )
    assert dto2['valid'] is True
    
    # Test mit gültigen Koordinaten
    dto3 = build_stop_dto(
        stop_id='X6',
        display_name='Test',
        resolved_address='Test',
        lat=51.05,
        lon=13.74,
        geo_source='cache'
    )
    assert dto3['valid'] is True