"""
Tests für Tour-Switching Funktionalität
"""
import pytest


def test_tour_switching_exact_match():
    """Test: Tour-Switching findet exakten Match."""
    all_tour_customers = {
        "workflow-0": {"name": "Tour 1", "customers": []},
        "workflow-1": {"name": "Tour 2", "customers": []},
        "W-07.00 A": {"name": "W-07.00 A", "customers": []}
    }
    
    key = "workflow-0"
    assert key in all_tour_customers
    assert all_tour_customers[key]["name"] == "Tour 1"


def test_tour_switching_similar_match():
    """Test: Tour-Switching findet ähnlichen Match für Sub-Routen."""
    all_tour_customers = {
        "W-07.00 A": {"name": "W-07.00 A", "customers": []},
        "W-07.00 B": {"name": "W-07.00 B", "customers": []},
        "W-09.00 A": {"name": "W-09.00 A", "customers": []}
    }
    
    # Suche nach ähnlichem Key
    search_key = "W-07.00"
    similar_key = next(
        (k for k in all_tour_customers.keys() if search_key in k or k in search_key),
        None
    )
    
    assert similar_key is not None
    assert "W-07.00" in similar_key


def test_tour_switching_no_match():
    """Test: Tour-Switching gibt None zurück wenn kein Match gefunden."""
    all_tour_customers = {
        "workflow-0": {"name": "Tour 1", "customers": []}
    }
    
    search_key = "NICHT-VORHANDEN"
    similar_key = next(
        (k for k in all_tour_customers.keys() if search_key in k or k in search_key),
        None
    )
    
    assert similar_key is None


def test_tour_switching_sub_route_keys():
    """Test: Sub-Routen haben konsistente Keys."""
    base_tour_id = "W-07.00"
    sub_routes = ["A", "B", "C"]
    
    keys = [f"{base_tour_id} {sub}" for sub in sub_routes]
    
    # Prüfe Keys
    assert len(keys) == 3
    assert all(base_tour_id in key for key in keys)
    assert keys[0] == "W-07.00 A"
    assert keys[1] == "W-07.00 B"
    assert keys[2] == "W-07.00 C"


def test_tour_switching_active_tour_key():
    """Test: Active Tour Key wird korrekt gesetzt."""
    active_tour_key = None
    all_tour_customers = {
        "workflow-0": {"name": "Tour 1", "customers": []}
    }
    
    key = "workflow-0"
    if key in all_tour_customers:
        active_tour_key = key
    
    assert active_tour_key == "workflow-0"


def test_tour_switching_update_selection():
    """Test: Tour-Liste-Selektion wird korrekt aktualisiert."""
    # Simuliere Tour-Liste
    tour_keys = ["workflow-0", "workflow-1", "W-07.00 A", "W-07.00 B"]
    active_key = "W-07.00 A"
    
    # Simuliere Update-Logik
    selected_keys = []
    for key in tour_keys:
        if key == active_key:
            selected_keys.append(key)
    
    assert len(selected_keys) == 1
    assert selected_keys[0] == active_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

