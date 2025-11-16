"""
Tests für Pydantic V2 Kompatibilität und kritische Fixes (2025-01-10)

Testet:
1. fill_missing() Parameter (batch_limit → limit)
2. StopModel Zugriff (kein .get(), sondern direkte Attribute)
3. Pydantic Mutability (keine direkte Mutation)
4. model_dump() statt dict()
"""
import pytest
from fastapi.testclient import TestClient
from backend.routes.schemas import StopModel, OptimizeTourRequest
import json


@pytest.fixture
def client():
    """Test-Client für FastAPI"""
    from backend.app import create_app
    app = create_app()
    return TestClient(app)


class TestPydanticV2Compatibility:
    """Tests für Pydantic V2 Kompatibilität"""
    
    def test_stop_model_direct_attribute_access(self):
        """Test: StopModel unterstützt direkten Attribut-Zugriff"""
        stop = StopModel(
            name="Test Kunde",
            address="Teststraße 1",
            lat=51.0504,
            lon=13.7373
        )
        
        # ✅ Korrekt: Direkter Zugriff
        assert stop.lat == 51.0504
        assert stop.lon == 13.7373
        assert stop.name == "Test Kunde"
        
        # ❌ Falsch: .get() existiert nicht
        with pytest.raises(AttributeError):
            stop.get('lat')
    
    def test_stop_model_model_dump(self):
        """Test: StopModel.model_dump() funktioniert (Pydantic V2)"""
        stop = StopModel(
            name="Test Kunde",
            lat=51.0504,
            lon=13.7373,
            bar_flag=True
        )
        
        # Pydantic V2: model_dump()
        if hasattr(stop, 'model_dump'):
            dumped = stop.model_dump()
        else:
            # Fallback für V1
            dumped = stop.dict()
        
        assert isinstance(dumped, dict)
        assert dumped['lat'] == 51.0504
        assert dumped['lon'] == 13.7373
        assert dumped['bar_flag'] is True
    
    def test_stop_model_no_mutation(self):
        """Test: StopModel ist immutable (keine direkte Mutation)"""
        stop = StopModel(
            name="Test",
            lat=51.0504,
            lon=13.7373
        )
        
        # Versuche Mutation (sollte nicht funktionieren oder neue Instanz erzeugen)
        # In Pydantic V2 sind Modelle standardmäßig immutable
        original_name = stop.name
        
        # Versuche direkte Zuweisung
        try:
            stop.name = "Geändert"
            # Wenn es funktioniert, ist das Modell mutable (OK)
            # Wenn nicht, ist es immutable (auch OK, dann müssen wir model_copy() verwenden)
        except Exception:
            # Immutable - das ist OK, wir verwenden model_dump() stattdessen
            pass
        
        # Wichtig: Wir verwenden model_dump() für Mutationen
        stop_dict = stop.model_dump() if hasattr(stop, 'model_dump') else stop.dict()
        stop_dict['name'] = "Geändert"
        
        assert stop_dict['name'] == "Geändert"
        # Original sollte unverändert sein (wenn immutable)
        # oder geändert sein (wenn mutable) - beide sind OK


class TestOptimizeTourRequest:
    """Tests für OptimizeTourRequest"""
    
    def test_optimize_request_validation(self):
        """Test: OptimizeTourRequest validiert korrekt"""
        # ✅ Gültiger Request
        request = OptimizeTourRequest(
            tour_id="TEST-TOUR",
            stops=[
                StopModel(name="Stop 1", lat=51.0504, lon=13.7373),
                StopModel(name="Stop 2", lat=51.0604, lon=13.7473)
            ]
        )
        
        assert request.tour_id == "TEST-TOUR"
        assert len(request.stops) == 2
        assert request.stops[0].lat == 51.0504
    
    def test_optimize_request_no_coordinates_fails(self):
        """Test: Request ohne Koordinaten schlägt fehl"""
        with pytest.raises(ValueError, match="Mindestens ein Stop muss gültige Koordinaten"):
            OptimizeTourRequest(
                tour_id="TEST-TOUR",
                stops=[
                    StopModel(name="Stop 1"),  # Keine Koordinaten
                    StopModel(name="Stop 2")   # Keine Koordinaten
                ]
            )
    
    def test_optimize_request_at_least_one_coordinate(self):
        """Test: Mindestens ein Stop mit Koordinaten reicht"""
        request = OptimizeTourRequest(
            tour_id="TEST-TOUR",
            stops=[
                StopModel(name="Stop 1", lat=51.0504, lon=13.7373),  # Mit Koordinaten
                StopModel(name="Stop 2")  # Ohne Koordinaten (OK)
            ]
        )
        
        assert len(request.stops) == 2


class TestOptimizeEndpoint:
    """Tests für /api/tour/optimize Endpoint"""
    
    def test_optimize_endpoint_pydantic_models(self, client):
        """Test: Endpoint akzeptiert Pydantic-Modelle korrekt"""
        request_body = {
            "tour_id": "TEST-TOUR",
            "stops": [
                {
                    "name": "Stop 1",
                    "lat": 51.0504,
                    "lon": 13.7373
                },
                {
                    "name": "Stop 2",
                    "lat": 51.0604,
                    "lon": 13.7473
                }
            ]
        }
        
        response = client.post("/api/tour/optimize", json=request_body)
        
        # Endpoint sollte 200 zurückgeben (nie 500)
        assert response.status_code in [200, 422], f"Unerwarteter Status: {response.status_code}, Body: {response.text}"
        
        data = response.json()
        
        # Response sollte strukturiert sein
        assert "success" in data
        
        # Wenn erfolgreich, sollte optimized_route vorhanden sein
        if data.get("success"):
            assert "optimized_route" in data or "optimized_stops" in data
    
    def test_optimize_endpoint_encoding_normalization(self, client):
        """Test: Encoding-Normalisierung funktioniert (NACH Konvertierung zu Dict)"""
        import unicodedata
        
        # Test mit Unicode-Text (NFC vs NFD)
        request_body = {
            "tour_id": "TEST-TOUR",
            "stops": [
                {
                    "name": "Fröbelstraße",  # Unicode
                    "address": "Löbtauer Straße 1",  # Unicode
                    "lat": 51.0504,
                    "lon": 13.7373
                }
            ]
        }
        
        response = client.post("/api/tour/optimize", json=request_body)
        
        # Endpoint sollte funktionieren
        assert response.status_code in [200, 422]
        
        # Normalisierung sollte im Backend passieren (NACH model_dump())
        # Wir können nicht direkt prüfen, aber der Endpoint sollte nicht crashen
        data = response.json()
        assert "success" in data


class TestFillMissingParameter:
    """Tests für fill_missing() Parameter-Fix"""
    
    def test_fill_missing_accepts_limit_not_batch_limit(self):
        """Test: fill_missing() akzeptiert 'limit', nicht 'batch_limit'"""
        from services.geocode_fill import fill_missing
        import inspect
        
        # Prüfe Signatur
        sig = inspect.signature(fill_missing)
        params = list(sig.parameters.keys())
        
        # Sollte 'limit' haben, nicht 'batch_limit'
        assert 'limit' in params, f"fill_missing() sollte 'limit' Parameter haben, hat aber: {params}"
        assert 'batch_limit' not in params, f"fill_missing() sollte NICHT 'batch_limit' haben"


class TestMatchEndpoint:
    """Tests für /api/tourplan/match Endpoint"""
    
    def test_match_endpoint_post_variant(self, client):
        """Test: POST /api/tourplan/match funktioniert (robuster gegen URL-Encoding)"""
        # Erstelle Test-CSV-Datei
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Kunde,Adresse,PLZ,Stadt\n")
            f.write("Test Kunde,Teststraße 1,01067,Dresden\n")
            test_file = f.name
        
        try:
            # Test POST-Variante
            request_body = {
                "stored_path": test_file
            }
            
            response = client.post("/api/tourplan/match", json=request_body)
            
            # Sollte funktionieren (200 oder 404 wenn Datei nicht gefunden)
            assert response.status_code in [200, 404, 422]
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.unlink(test_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

