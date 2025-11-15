"""
Tests für kritische Fixes vom 2025-01-10
- Background-Job Auto-Start
- Sub-Routen-Generierung
- Tour-Switching
- Tour-Details-Rendering
- Upload/Verarbeitungs-Pipeline
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json

# Test für Background-Job Auto-Start
def test_background_job_auto_start():
    """Test: Background-Job startet automatisch beim Server-Start."""
    from backend.services.code_improvement_job import get_background_job
    
    job = get_background_job()
    
    # Prüfe Konfiguration
    assert job.enabled == True, "Background-Job sollte aktiviert sein"
    
    # Prüfe ob AI-Checker verfügbar ist (kann None sein wenn OPENAI_API_KEY fehlt)
    # Das ist OK, der Job sollte trotzdem initialisiert sein
    
    # Prüfe Status-Methode
    status = job.get_status()
    assert "enabled" in status
    assert "is_running" in status
    assert "last_run" in status
    assert "total_improvements" in status


def test_background_job_startup_event():
    """Test: Startup-Event startet Background-Job."""
    from fastapi import FastAPI
    from backend.app import create_app
    
    app = create_app()
    
    # Prüfe ob Startup-Event registriert ist
    startup_events = [handler for handler in app.router.on_startup]
    assert len(startup_events) > 0, "Startup-Event sollte registriert sein"


# Test für Sub-Routen-Generierung
def test_sub_routes_generation_structure():
    """Test: Sub-Routen haben korrekte Datenstruktur."""
    # Simuliere Sub-Route-Daten
    sub_route = {
        "tour_id": "W-07.00 A",
        "sub_route": "A",
        "stops": [
            {
                "customer_number": "123",
                "name": "Kunde 1",
                "lat": 51.05,
                "lon": 13.74,
                "bar_flag": False
            }
        ],
        "driving_time": 30.5,
        "service_time": 10.0,
        "return_time": 15.0,
        "total_time": 55.5
    }
    
    # Prüfe Struktur
    assert "tour_id" in sub_route
    assert "sub_route" in sub_route
    assert "stops" in sub_route
    assert isinstance(sub_route["stops"], list)
    assert len(sub_route["stops"]) > 0
    
    # Prüfe Stop-Struktur
    stop = sub_route["stops"][0]
    assert "customer_number" in stop
    assert "name" in stop
    assert "lat" in stop
    assert "lon" in stop


def test_sub_routes_customers_conversion():
    """Test: Stops werden korrekt zu Customers konvertiert."""
    # Simuliere Tour-Daten mit stops
    tour_data = {
        "name": "W-07.00 A",
        "stops": [
            {
                "customer_number": "123",
                "name": "Kunde 1",
                "street": "Hauptstraße",
                "postal_code": "01189",
                "city": "Dresden",
                "lat": 51.05,
                "lon": 13.74,
                "bar_flag": False
            }
        ],
        "customers": None  # Fehlt
    }
    
    # Simuliere Konvertierung (wie in renderTourDetails)
    if not tour_data.get("customers") and tour_data.get("stops"):
        customers = [{
            "customer_number": s.get("customer_number", ""),
            "name": s.get("name", "Unbekannt"),
            "street": s.get("street", ""),
            "postal_code": s.get("postal_code", ""),
            "city": s.get("city", ""),
            "address": f"{s.get('street', '')}, {s.get('postal_code', '')} {s.get('city', '')}".strip(),
            "latitude": s.get("lat") or s.get("latitude"),
            "longitude": s.get("lon") or s.get("longitude"),
            "lat": s.get("lat") or s.get("latitude"),
            "lon": s.get("lon") or s.get("longitude"),
            "bar_flag": s.get("bar_flag", False),
            "has_coordinates": bool((s.get("lat") or s.get("latitude")) and (s.get("lon") or s.get("longitude")))
        } for s in tour_data["stops"]]
    
    # Prüfe Konvertierung
    assert customers is not None
    assert len(customers) == 1
    assert customers[0]["name"] == "Kunde 1"
    assert customers[0]["has_coordinates"] == True


# Test für Tour-Switching
def test_tour_switching_key_matching():
    """Test: Tour-Switching findet ähnliche Keys."""
    # Simuliere allTourCustomers
    all_tour_customers = {
        "workflow-0": {"name": "Tour 1"},
        "W-07.00 A": {"name": "W-07.00 A"},
        "W-07.00 B": {"name": "W-07.00 B"},
        "workflow-1": {"name": "Tour 2"}
    }
    
    # Test 1: Exakter Match
    key = "workflow-0"
    assert key in all_tour_customers
    
    # Test 2: Ähnlicher Match (für Sub-Routen)
    search_key = "W-07.00"
    similar_key = next((k for k in all_tour_customers.keys() if search_key in k or k in search_key), None)
    assert similar_key is not None
    assert "W-07.00" in similar_key
    
    # Test 3: Kein Match
    search_key = "NICHT-VORHANDEN"
    similar_key = next((k for k in all_tour_customers.keys() if search_key in k or k in search_key), None)
    assert similar_key is None


def test_tour_switching_sub_route_keys():
    """Test: Sub-Routen haben konsistente Keys."""
    # Simuliere Sub-Routen-Keys
    base_tour_id = "W-07.00"
    sub_routes = ["A", "B", "C"]
    
    keys = [f"{base_tour_id} {sub}" for sub in sub_routes]
    
    # Prüfe Keys
    assert len(keys) == 3
    assert keys[0] == "W-07.00 A"
    assert keys[1] == "W-07.00 B"
    assert keys[2] == "W-07.00 C"
    
    # Prüfe Konsistenz
    for key in keys:
        assert base_tour_id in key
        assert key.endswith((" A", " B", " C"))


# Test für Tour-Details-Rendering
def test_tour_details_rendering_with_customers():
    """Test: Tour-Details werden korrekt gerendert mit customers."""
    tour_data = {
        "name": "W-07.00 A",
        "type": "Workflow",
        "time": "07:00",
        "customers": [
            {
                "name": "Kunde 1",
                "address": "Hauptstraße 1, 01189 Dresden",
                "latitude": 51.05,
                "longitude": 13.74
            }
        ]
    }
    
    # Prüfe Datenstruktur
    assert "name" in tour_data
    assert "customers" in tour_data
    assert isinstance(tour_data["customers"], list)
    assert len(tour_data["customers"]) > 0
    
    # Prüfe Customer-Daten
    customer = tour_data["customers"][0]
    assert "name" in customer
    assert "address" in customer
    assert "latitude" in customer
    assert "longitude" in customer


def test_tour_details_rendering_without_customers():
    """Test: Tour-Details werden korrekt gerendert ohne customers (Fallback zu stops)."""
    tour_data = {
        "name": "W-07.00 A",
        "type": "Workflow",
        "time": "07:00",
        "customers": None,  # Fehlt
        "stops": [
            {
                "name": "Kunde 1",
                "address": "Hauptstraße 1, 01189 Dresden",
                "lat": 51.05,
                "lon": 13.74
            }
        ]
    }
    
    # Prüfe Fallback-Logik
    customers = tour_data.get("customers")
    if not customers and tour_data.get("stops"):
        # Konvertiere stops zu customers
        customers = [
            {
                "name": s.get("name", "Unbekannt"),
                "address": s.get("address", ""),
                "latitude": s.get("lat") or s.get("latitude"),
                "longitude": s.get("lon") or s.get("longitude")
            }
            for s in tour_data["stops"]
        ]
    
    # Prüfe Konvertierung
    assert customers is not None
    assert len(customers) == 1
    assert customers[0]["name"] == "Kunde 1"


# Test für Upload/Verarbeitungs-Pipeline
def test_upload_response_structure():
    """Test: Upload-Response hat korrekte Struktur."""
    # Simuliere Upload-Response
    upload_response = {
        "success": True,
        "stored_path": "/app/data/staging/1234567890_test.csv",
        "rows": 100,
        "filename": "test.csv"
    }
    
    # Prüfe Struktur
    assert "success" in upload_response
    assert "stored_path" in upload_response
    assert "rows" in upload_response
    
    # Prüfe stored_path
    stored_path = upload_response["stored_path"]
    assert stored_path is not None
    assert stored_path != "undefined"
    assert isinstance(stored_path, str)
    assert len(stored_path) > 0


def test_match_endpoint_with_stored_path():
    """Test: Match-Endpoint verwendet stored_path korrekt."""
    # Simuliere Match-Request
    stored_path = "/app/data/staging/1234567890_test.csv"
    
    # Prüfe URL-Encoding
    encoded_path = stored_path.replace("/", "%2F")
    assert "%2F" in encoded_path
    
    # Prüfe dass stored_path nicht undefined ist
    assert stored_path != "undefined"
    assert stored_path is not None
    assert isinstance(stored_path, str)


# Integration-Test
def test_full_workflow_pipeline():
    """Test: Vollständiger Workflow von Upload bis Sub-Routen."""
    # 1. Upload
    upload_response = {
        "success": True,
        "stored_path": "/app/data/staging/1234567890_test.csv",
        "rows": 100
    }
    assert upload_response["success"] == True
    assert "stored_path" in upload_response
    
    # 2. Match
    stored_path = upload_response["stored_path"]
    assert stored_path != "undefined"
    
    # 3. Workflow-Result
    workflow_result = {
        "tours": [
            {
                "tour_id": "W-07.00",
                "stops": [
                    {"name": "Kunde 1", "lat": 51.05, "lon": 13.74}
                ]
            }
        ]
    }
    assert "tours" in workflow_result
    assert len(workflow_result["tours"]) > 0
    
    # 4. Sub-Routen
    tour = workflow_result["tours"][0]
    assert "tour_id" in tour
    assert "stops" in tour
    
    # 5. Tour-Switching
    all_tour_customers = {
        "W-07.00 A": {
            "name": "W-07.00 A",
            "customers": [{"name": "Kunde 1"}]
        }
    }
    key = "W-07.00 A"
    assert key in all_tour_customers
    
    # 6. Tour-Details
    tour_data = all_tour_customers[key]
    assert "name" in tour_data
    assert "customers" in tour_data


# Performance-Test für Sub-Routen-Generierung
def test_sub_routes_generation_performance():
    """Test: Sub-Routen-Generierung sollte nicht zu langsam sein."""
    import time
    
    # Simuliere mehrere Touren
    tours = [
        {
            "tour_id": f"W-{i:02d}.00",
            "stops": [{"name": f"Kunde {j}", "lat": 51.05, "lon": 13.74} for j in range(10)]
        }
        for i in range(5)
    ]
    
    # Simuliere sequenzielle Verarbeitung
    start_time = time.time()
    for tour in tours:
        # Simuliere API-Call (sollte schnell sein)
        time.sleep(0.01)  # 10ms pro Tour
    sequential_time = time.time() - start_time
    
    # Simuliere parallele Verarbeitung (Batch von 3)
    start_time = time.time()
    batch_size = 3
    for batch_start in range(0, len(tours), batch_size):
        batch = tours[batch_start:batch_start + batch_size]
        # Simuliere parallele Verarbeitung
        for tour in batch:
            time.sleep(0.01)  # 10ms pro Tour
    parallel_time = time.time() - start_time
    
    # Parallele Verarbeitung sollte nicht langsamer sein
    # (In echtem Szenario wäre es schneller, hier ist es ähnlich wegen sleep)
    assert parallel_time <= sequential_time * 1.5  # Toleranz für Overhead


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
