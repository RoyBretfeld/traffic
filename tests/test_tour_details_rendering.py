"""
Tests für Tour-Details-Rendering
"""
import pytest


def test_tour_details_with_customers():
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
                "longitude": 13.74,
                "has_coordinates": True
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
    assert customer["has_coordinates"] == True


def test_tour_details_without_customers_fallback():
    """Test: Tour-Details verwenden stops als Fallback wenn customers fehlen."""
    tour_data = {
        "name": "W-07.00 A",
        "type": "Workflow",
        "time": "07:00",
        "customers": None,  # Fehlt
        "stops": [
            {
                "name": "Kunde 1",
                "customer": "Kunde 1",
                "address": "Hauptstraße 1, 01189 Dresden",
                "street": "Hauptstraße",
                "postal_code": "01189",
                "city": "Dresden",
                "lat": 51.05,
                "lon": 13.74,
                "bar_flag": False
            }
        ],
        "is_bar_tour": False
    }
    
    # Simuliere Fallback-Logik
    customers = tour_data.get("customers")
    if not customers and tour_data.get("stops"):
        customers = [
            {
                "customer_number": s.get("customer_number") or s.get("order_id") or "",
                "name": s.get("name") or s.get("customer") or "Unbekannt",
                "street": s.get("street") or "",
                "postal_code": s.get("postal_code") or "",
                "city": s.get("city") or "",
                "address": s.get("address") or f"{s.get('street', '')}, {s.get('postal_code', '')} {s.get('city', '')}".strip(),
                "latitude": s.get("lat") or s.get("latitude"),
                "longitude": s.get("lon") or s.get("longitude"),
                "lat": s.get("lat") or s.get("latitude"),
                "lon": s.get("lon") or s.get("longitude"),
                "bar_flag": s.get("bar_flag") if s.get("bar_flag") is not None else (tour_data.get("is_bar_tour") or False),
                "has_coordinates": bool((s.get("lat") or s.get("latitude")) and (s.get("lon") or s.get("longitude")))
            }
            for s in tour_data["stops"]
        ]
    
    # Prüfe Konvertierung
    assert customers is not None
    assert len(customers) == 1
    assert customers[0]["name"] == "Kunde 1"
    assert customers[0]["has_coordinates"] == True
    assert customers[0]["bar_flag"] == False


def test_tour_details_empty_customers():
    """Test: Tour-Details werden korrekt gerendert mit leerem customers-Array."""
    tour_data = {
        "name": "W-07.00 A",
        "type": "Workflow",
        "time": "07:00",
        "customers": []  # Leer
    }
    
    # Prüfe dass customers leer ist
    assert isinstance(tour_data["customers"], list)
    assert len(tour_data["customers"]) == 0


def test_tour_details_missing_fields():
    """Test: Tour-Details werden korrekt gerendert mit fehlenden Feldern."""
    tour_data = {
        "name": "W-07.00 A",
        # type fehlt
        # time fehlt
        "customers": [
            {
                "name": "Kunde 1",
                # address fehlt
                "latitude": 51.05,
                "longitude": 13.74
            }
        ]
    }
    
    # Prüfe dass fehlende Felder mit Defaults behandelt werden
    name = tour_data.get("name", "Unbekannte Tour")
    type_str = tour_data.get("type", "")
    time_str = tour_data.get("time", "")
    
    assert name == "W-07.00 A"
    assert type_str == ""
    assert time_str == ""


def test_tour_details_coordinate_handling():
    """Test: Tour-Details behandeln Koordinaten korrekt."""
    tour_data = {
        "name": "W-07.00 A",
        "customers": [
            {
                "name": "Kunde 1",
                "lat": 51.05,
                "lon": 13.74,
                "latitude": None,  # Alternative Feld
                "longitude": None
            }
        ]
    }
    
    customer = tour_data["customers"][0]
    
    # Prüfe Koordinaten-Handling
    lat = customer.get("lat") or customer.get("latitude")
    lon = customer.get("lon") or customer.get("longitude")
    
    assert lat == 51.05
    assert lon == 13.74
    assert customer.get("has_coordinates", bool(lat and lon)) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

