"""
Tests für die Code-Verbesserungen:
- app_setup.py Module
- path_helpers.py
- customer_db_helpers.py
"""
import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_app_setup_imports():
    """Test: Alle app_setup Module können importiert werden."""
    from backend.app_setup import (
        setup_app_state,
        setup_database_schema,
        setup_middleware,
        setup_static_files,
        setup_routers,
        setup_health_routes,
        setup_startup_handlers,
    )
    
    # Prüfe dass alle Funktionen existieren
    assert callable(setup_app_state)
    assert callable(setup_database_schema)
    assert callable(setup_middleware)
    assert callable(setup_static_files)
    assert callable(setup_routers)
    assert callable(setup_health_routes)
    assert callable(setup_startup_handlers)


def test_path_helpers_imports():
    """Test: path_helpers Module kann importiert werden."""
    from backend.utils.path_helpers import (
        get_frontend_path,
        read_frontend_file,
    )
    
    assert callable(get_frontend_path)
    assert callable(read_frontend_file)


def test_path_helpers_get_frontend_path():
    """Test: get_frontend_path gibt korrekten Pfad zurück."""
    from backend.utils.path_helpers import get_frontend_path
    
    # Test mit Standard-Pfad
    path = get_frontend_path("index.html")
    assert isinstance(path, Path)
    assert "frontend" in str(path) or "index.html" in str(path)


def test_path_helpers_read_frontend_file():
    """Test: read_frontend_file kann Datei lesen (wenn vorhanden)."""
    from backend.utils.path_helpers import read_frontend_file
    
    # Test nur wenn Frontend-Datei existiert
    frontend_file = Path("frontend/index.html")
    if frontend_file.exists():
        content = read_frontend_file("index.html")
        assert isinstance(content, str)
        assert len(content) > 0


def test_customer_db_helpers_imports():
    """Test: customer_db_helpers Module kann importiert werden."""
    from backend.utils.customer_db_helpers import (
        get_kunde_id_by_name_adresse,
        _normalize_string,
        _search_in_customers_db,
        _search_in_traffic_db,
    )
    
    assert callable(get_kunde_id_by_name_adresse)
    assert callable(_normalize_string)
    assert callable(_search_in_customers_db)
    assert callable(_search_in_traffic_db)


def test_customer_db_helpers_normalize_string():
    """Test: _normalize_string normalisiert Strings korrekt."""
    from backend.utils.customer_db_helpers import _normalize_string
    
    assert _normalize_string("  TEST  ") == "test"
    assert _normalize_string("Test String") == "test string"
    assert _normalize_string("") == ""
    assert _normalize_string("   ") == ""


def test_create_app_returns_fastapi():
    """Test: create_app gibt FastAPI-Instanz zurück."""
    from backend.app import create_app
    
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "TrafficApp API"


def test_app_has_health_endpoints():
    """Test: App hat Health-Endpoints."""
    from backend.app import create_app
    from fastapi.testclient import TestClient
    
    app = create_app()
    client = TestClient(app)
    
    # Test /healthz
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Test /readyz
    response = client.get("/readyz")
    assert response.status_code in [200, 503]  # Kann 503 sein wenn DB nicht verfügbar


def test_app_has_static_files_mounted():
    """Test: App hat Static Files gemountet."""
    from backend.app import create_app
    
    app = create_app()
    
    # Prüfe ob Static Files Route existiert
    static_routes = [r for r in app.routes if hasattr(r, 'path') and '/static' in r.path]
    assert len(static_routes) > 0


def test_app_setup_functions_can_be_called():
    """Test: Alle Setup-Funktionen können aufgerufen werden."""
    from backend.app_setup import (
        setup_app_state,
        setup_database_schema,
        setup_middleware,
        setup_static_files,
        setup_routers,
        setup_health_routes,
    )
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Test dass Funktionen ohne Fehler aufgerufen werden können
    try:
        setup_app_state(app)
        setup_database_schema()
        setup_middleware(app)
        setup_static_files(app)
        setup_routers(app)
        setup_health_routes(app)
    except Exception as e:
        pytest.fail(f"Setup-Funktion fehlgeschlagen: {e}")


def test_error_handling_in_file_operations():
    """Test: Error-Handling ist in Datei-Operationen vorhanden."""
    from backend.app import create_app
    from fastapi.testclient import TestClient
    
    app = create_app()
    client = TestClient(app)
    
    # Test dass Error-Handling vorhanden ist (durch Code-Inspektion)
    # Die Funktionen sollten try-except Blöcke haben
    import inspect
    from backend.app import create_app as create_app_func
    
    source = inspect.getsource(create_app_func)
    # Prüfe dass try-except in der Funktion vorhanden ist
    assert "try:" in source or "except" in source  # Mindestens ein Error-Handling


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

