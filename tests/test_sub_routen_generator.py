#!/usr/bin/env python3
"""
Tests für Sub-Routen-Generator
Testet Zeitberechnung, Haversine, OSRM-Fallback
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict


class TestHaversineDistance:
    """Tests für Haversine-Distanzberechnung"""
    
    def test_haversine_with_valid_coordinates(self):
        """Test: Haversine mit gültigen Koordinaten"""
        from backend.routes.workflow_api import _haversine_distance_km
        
        # Dresden Hauptbahnhof → Dresden Neustadt
        lat1, lon1 = 51.0404, 13.7320  # Hbf
        lat2, lon2 = 51.0636, 13.7404  # Neustadt
        
        distance = _haversine_distance_km(lat1, lon1, lat2, lon2)
        
        # Prüfe Plausibilität (ca. 2-3 km)
        assert 2.0 < distance < 4.0, f"Unerwartete Distanz: {distance} km"
    
    def test_haversine_with_zero_distance(self):
        """Test: Haversine mit gleichen Koordinaten"""
        from backend.routes.workflow_api import _haversine_distance_km
        
        lat, lon = 51.0404, 13.7320
        distance = _haversine_distance_km(lat, lon, lat, lon)
        
        # Sollte 0 oder sehr klein sein
        assert distance < 0.001, f"Distanz sollte ~0 sein: {distance}"
    
    def test_haversine_with_invalid_coordinates(self):
        """Test: Haversine mit ungültigen Koordinaten"""
        from backend.routes.workflow_api import _haversine_distance_km
        
        # Außerhalb gültiger Bereiche
        invalid_cases = [
            (91.0, 0.0, 51.0, 13.0),    # Lat > 90
            (51.0, 181.0, 51.0, 13.0),  # Lon > 180
            (-91.0, 0.0, 51.0, 13.0),   # Lat < -90
            (51.0, -181.0, 51.0, 13.0), # Lon < -180
        ]
        
        for lat1, lon1, lat2, lon2 in invalid_cases:
            distance = _haversine_distance_km(lat1, lon1, lat2, lon2)
            assert distance == 0.0, f"Ungültige Koordinaten sollten 0 zurückgeben: {(lat1, lon1, lat2, lon2)}"
    
    def test_haversine_with_non_numeric_input(self):
        """Test: Haversine mit nicht-numerischen Werten"""
        from backend.routes.workflow_api import _haversine_distance_km
        
        invalid_inputs = [
            ("51.0", 13.0, 51.0, 13.0),     # String statt float
            (None, 13.0, 51.0, 13.0),       # None
            (51.0, 13.0, "invalid", 13.0),  # String
        ]
        
        for lat1, lon1, lat2, lon2 in invalid_inputs:
            distance = _haversine_distance_km(lat1, lon1, lat2, lon2)
            assert distance == 0.0, f"Nicht-numerische Werte sollten 0 zurückgeben: {(lat1, lon1, lat2, lon2)}"


class TestCalculateTourTime:
    """Tests für Tour-Zeitberechnung"""
    
    def test_calculate_tour_time_with_empty_stops(self):
        """Test: Zeitberechnung mit leerer Liste"""
        from backend.routes.workflow_api import _calculate_tour_time
        
        time = _calculate_tour_time([])
        assert time == 0.0, f"Leere Liste sollte 0 zurückgeben: {time}"
    
    def test_calculate_tour_time_with_single_stop(self):
        """Test: Zeitberechnung mit einem Stop"""
        from backend.routes.workflow_api import _calculate_tour_time
        
        stops = [
            {"lat": 51.0404, "lon": 13.7320, "name": "Test Stop"}
        ]
        
        time = _calculate_tour_time(stops)
        
        # Sollte mindestens 10 Minuten sein (Fallback-Minimum)
        assert time >= 10.0, f"Einzelner Stop sollte >= 10 Min sein: {time}"
    
    def test_calculate_tour_time_with_multiple_stops(self):
        """Test: Zeitberechnung mit mehreren Stops"""
        from backend.routes.workflow_api import _calculate_tour_time
        
        stops = [
            {"lat": 51.0404, "lon": 13.7320, "name": "Stop 1"},
            {"lat": 51.0636, "lon": 13.7404, "name": "Stop 2"},
            {"lat": 51.0504, "lon": 13.7373, "name": "Stop 3"}
        ]
        
        time = _calculate_tour_time(stops)
        
        # Sollte > 0 und plausibel sein
        assert time > 0, f"Tour mit Stopps sollte > 0 sein: {time}"
        assert time < 1000, f"Zeitschätzung unrealistisch hoch: {time}"
    
    def test_calculate_tour_time_with_invalid_coordinates(self):
        """Test: Zeitberechnung mit ungültigen Koordinaten"""
        from backend.routes.workflow_api import _calculate_tour_time
        
        stops = [
            {"lat": None, "lon": 13.7320, "name": "Invalid Stop 1"},
            {"lat": 51.0404, "lon": None, "name": "Invalid Stop 2"},
            {"lat": "invalid", "lon": 13.7320, "name": "Invalid Stop 3"}
        ]
        
        time = _calculate_tour_time(stops)
        
        # Sollte Fallback verwenden (basierend auf Anzahl Stopps)
        assert time >= 10.0, f"Fallback-Minimum sollte >= 10 sein: {time}"
    
    def test_calculate_tour_time_with_osrm_unavailable(self):
        """Test: Zeitberechnung wenn OSRM nicht verfügbar"""
        from backend.routes.workflow_api import _calculate_tour_time
        
        stops = [
            {"lat": 51.0404, "lon": 13.7320, "name": "Stop 1"},
            {"lat": 51.0636, "lon": 13.7404, "name": "Stop 2"}
        ]
        
        # Mock OSRM-Client als nicht verfügbar
        with patch('backend.routes.workflow_api.get_osrm_client') as mock_client:
            mock_osrm = Mock()
            mock_osrm.available = False
            mock_client.return_value = mock_osrm
            
            time = _calculate_tour_time(stops)
            
            # Sollte Haversine-Fallback verwenden
            assert time > 0, f"Haversine-Fallback sollte > 0 sein: {time}"
            assert time < 100, f"Fallback-Zeit unrealistisch: {time}"


class TestOptimizeTourStops:
    """Tests für Tour-Optimierung"""
    
    def test_optimize_empty_list(self):
        """Test: Optimierung mit leerer Liste"""
        from backend.routes.workflow_api import optimize_tour_stops
        
        result = optimize_tour_stops([])
        assert result == [], "Leere Liste sollte leere Liste zurückgeben"
    
    def test_optimize_single_stop(self):
        """Test: Optimierung mit einem Stop"""
        from backend.routes.workflow_api import optimize_tour_stops
        
        stops = [{"lat": 51.0404, "lon": 13.7320, "name": "Stop 1"}]
        result = optimize_tour_stops(stops)
        
        assert len(result) == 1, "Einzelner Stop sollte unverändert bleiben"
        assert result[0] == stops[0]
    
    def test_optimize_multiple_stops(self):
        """Test: Optimierung mit mehreren Stops"""
        from backend.routes.workflow_api import optimize_tour_stops
        
        stops = [
            {"lat": 51.0404, "lon": 13.7320, "name": "Stop 1"},
            {"lat": 51.0636, "lon": 13.7404, "name": "Stop 2"},
            {"lat": 51.0504, "lon": 13.7373, "name": "Stop 3"}
        ]
        
        result = optimize_tour_stops(stops, use_llm=False)  # Ohne LLM (Nearest Neighbor)
        
        assert len(result) == len(stops), "Anzahl Stopps sollte gleich bleiben"
        # Prüfe ob alle Stopps vorhanden sind
        result_names = [s["name"] for s in result]
        for stop in stops:
            assert stop["name"] in result_names, f"Stop {stop['name']} fehlt in Ergebnis"
    
    def test_optimize_with_invalid_coordinates(self):
        """Test: Optimierung mit ungültigen Koordinaten"""
        from backend.routes.workflow_api import optimize_tour_stops
        
        stops = [
            {"lat": 51.0404, "lon": 13.7320, "name": "Valid Stop"},
            {"lat": None, "lon": 13.7404, "name": "Invalid Stop 1"},
            {"lat": 51.0504, "lon": None, "name": "Invalid Stop 2"}
        ]
        
        result = optimize_tour_stops(stops, use_llm=False)
        
        # Sollte nur gültige Stopps zurückgeben
        assert len(result) > 0, "Sollte mindestens einen gültigen Stop zurückgeben"
        # Aber nicht mehr als ursprünglich
        assert len(result) <= len(stops)


class TestEnforceTimebox:
    """Tests für Timebox-Validierung und Splitting"""
    
    def test_enforce_timebox_with_valid_tour(self):
        """Test: Tour innerhalb der Zeitgrenzen"""
        from backend.routes.workflow_api import enforce_timebox
        
        # Kleine Tour (sollte nicht gesplittet werden)
        stops = [
            {"lat": 51.0404, "lon": 13.7320, "name": "Stop 1"},
            {"lat": 51.0636, "lon": 13.7404, "name": "Stop 2"}
        ]
        
        result = enforce_timebox("TEST-TOUR", stops, max_depth=3)
        
        # Sollte Liste von Tours zurückgeben
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Prüfe Struktur
        for tour in result:
            assert "tour_id" in tour
            assert "stops" in tour
            assert isinstance(tour["stops"], list)
    
    def test_enforce_timebox_with_empty_stops(self):
        """Test: Timebox mit leeren Stops"""
        from backend.routes.workflow_api import enforce_timebox
        
        result = enforce_timebox("EMPTY-TOUR", [], max_depth=3)
        assert result == [], "Leere Stops sollten leere Liste zurückgeben"
    
    def test_enforce_timebox_max_depth(self):
        """Test: Timebox erreicht maximale Rekursionstiefe"""
        from backend.routes.workflow_api import enforce_timebox
        
        # Sehr viele Stops (würde normalerweise splitten)
        stops = [{"lat": 51.0 + i*0.01, "lon": 13.7 + i*0.01, "name": f"Stop {i}"} for i in range(50)]
        
        # Mit max_depth=0 sollte keine Splits gemacht werden
        result = enforce_timebox("LARGE-TOUR", stops, max_depth=0)
        
        # Sollte trotzdem eine Tour zurückgeben (ohne Splitting)
        assert len(result) == 1, "Bei max_depth=0 sollte keine Splits geben"


class TestSafePrint:
    """Tests für safe_print Utility"""
    
    def test_safe_print_with_ascii(self):
        """Test: safe_print mit ASCII-Text"""
        from backend.utils.safe_print import safe_print
        
        # Sollte nicht crashen
        try:
            safe_print("Test ASCII Text")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"safe_print crashed with ASCII: {e}")
        
        assert success
    
    def test_safe_print_with_unicode(self):
        """Test: safe_print mit Unicode-Zeichen"""
        from backend.utils.safe_print import safe_print
        
        # Sollte nicht crashen (auch wenn Konsole es nicht unterstützt)
        try:
            safe_print("Test Unicode: ö ä ü → ←")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"safe_print crashed with Unicode: {e}")
        
        assert success
    
    def test_safe_print_with_special_characters(self):
        """Test: safe_print mit Sonderzeichen"""
        from backend.utils.safe_print import safe_print
        
        # Sollte nicht crashen
        try:
            safe_print("Test Special: ✓ ✗ ⚠ 📦")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"safe_print crashed with special chars: {e}")
        
        assert success


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

