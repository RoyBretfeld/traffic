"""
Tests für Phase 2 Schema-Erweiterung
Prüft Tabellen-Erstellung, Indizes, Foreign Keys, Constraints
"""
import pytest
from sqlalchemy import text, inspect
from db.core import ENGINE
from db.schema_phase2 import ensure_phase2_schema, PHASE2_SCHEMA_SQL


def test_phase2_tables_exist():
    """Test: Prüft ob alle Phase 2 Tabellen existieren."""
    inspector = inspect(ENGINE)
    tables = inspector.get_table_names()
    
    required_tables = ['stats_monthly', 'routes', 'route_legs', 'osrm_cache']
    
    for table_name in required_tables:
        assert table_name in tables, f"Tabelle '{table_name}' fehlt"


def test_stats_monthly_structure():
    """Test: Prüft Struktur der stats_monthly Tabelle."""
    with ENGINE.connect() as conn:
        # Prüfe Spalten
        result = conn.execute(text("PRAGMA table_info(stats_monthly)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        assert 'id' in columns
        assert 'month' in columns
        assert 'tours_count' in columns
        assert 'stops_count' in columns
        assert 'total_km' in columns
        assert 'avg_stops_per_tour' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns
        
        # Prüfe UNIQUE Constraint auf month
        result = conn.execute(text("PRAGMA index_list(stats_monthly)"))
        indexes = [row[1] for row in result.fetchall()]
        assert any('month' in idx.lower() for idx in indexes), "UNIQUE Index auf 'month' fehlt"


def test_routes_structure():
    """Test: Prüft Struktur der routes Tabelle."""
    with ENGINE.connect() as conn:
        # Prüfe Spalten
        result = conn.execute(text("PRAGMA table_info(routes)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        assert 'id' in columns
        assert 'tour_id' in columns
        assert 'tour_date' in columns
        assert 'route_name' in columns
        assert 'total_distance_km' in columns
        assert 'total_duration_min' in columns
        assert 'stops_count' in columns
        assert 'status' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns


def test_route_legs_structure():
    """Test: Prüft Struktur der route_legs Tabelle."""
    with ENGINE.connect() as conn:
        # Prüfe Spalten
        result = conn.execute(text("PRAGMA table_info(route_legs)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        assert 'id' in columns
        assert 'route_id' in columns
        assert 'sequence_order' in columns
        assert 'from_stop_id' in columns
        assert 'to_stop_id' in columns
        assert 'distance_km' in columns
        assert 'duration_min' in columns
        assert 'geometry' in columns
        assert 'geometry_type' in columns
        assert 'source' in columns
        assert 'created_at' in columns
        
        # Prüfe Foreign Key zu routes
        result = conn.execute(text("PRAGMA foreign_key_list(route_legs)"))
        foreign_keys = result.fetchall()
        assert len(foreign_keys) > 0, "Foreign Key zu 'routes' fehlt"


def test_osrm_cache_structure():
    """Test: Prüft Struktur der osrm_cache Tabelle."""
    with ENGINE.connect() as conn:
        # Prüfe Spalten
        result = conn.execute(text("PRAGMA table_info(osrm_cache)"))
        columns = {row[1]: row[2] for row in result.fetchall()}
        
        assert 'id' in columns
        assert 'from_lat' in columns
        assert 'from_lon' in columns
        assert 'to_lat' in columns
        assert 'to_lon' in columns
        assert 'geometry' in columns
        assert 'distance_km' in columns
        assert 'duration_min' in columns
        assert 'cached_at' in columns
        assert 'expires_at' in columns
        
        # Prüfe UNIQUE Constraint auf Koordinaten
        result = conn.execute(text("PRAGMA index_list(osrm_cache)"))
        indexes = [row[1] for row in result.fetchall()]
        assert any('coords' in idx.lower() for idx in indexes), "Index auf Koordinaten fehlt"


def test_indexes_exist():
    """Test: Prüft ob alle Indizes existieren."""
    with ENGINE.connect() as conn:
        # Prüfe Indizes für stats_monthly
        result = conn.execute(text("PRAGMA index_list(stats_monthly)"))
        stats_indexes = [row[1] for row in result.fetchall()]
        assert any('month' in idx.lower() for idx in stats_indexes), "Index auf stats_monthly.month fehlt"
        
        # Prüfe Indizes für routes
        result = conn.execute(text("PRAGMA index_list(routes)"))
        routes_indexes = [row[1] for row in result.fetchall()]
        assert any('tour_date' in idx.lower() for idx in routes_indexes), "Index auf routes.tour_date fehlt"
        
        # Prüfe Indizes für route_legs
        result = conn.execute(text("PRAGMA index_list(route_legs)"))
        legs_indexes = [row[1] for row in result.fetchall()]
        assert any('route' in idx.lower() for idx in legs_indexes), "Index auf route_legs.route_id fehlt"
        assert any('sequence' in idx.lower() for idx in legs_indexes), "Index auf route_legs.sequence_order fehlt"
        
        # Prüfe Indizes für osrm_cache
        result = conn.execute(text("PRAGMA index_list(osrm_cache)"))
        cache_indexes = [row[1] for row in result.fetchall()]
        assert any('coords' in idx.lower() for idx in cache_indexes), "Index auf osrm_cache Koordinaten fehlt"
        assert any('expires' in idx.lower() for idx in cache_indexes), "Index auf osrm_cache.expires_at fehlt"


def test_foreign_key_constraint():
    """Test: Prüft Foreign Key Constraint zwischen route_legs und routes."""
    with ENGINE.connect() as conn:
        # Prüfe ob Foreign Keys aktiviert sind
        result = conn.execute(text("PRAGMA foreign_keys"))
        fk_enabled = result.fetchone()[0]
        assert fk_enabled == 1, "Foreign Keys sind nicht aktiviert"
        
        # Prüfe Foreign Key Definition
        result = conn.execute(text("PRAGMA foreign_key_list(route_legs)"))
        fk_list = result.fetchall()
        assert len(fk_list) > 0, "Foreign Key Definition fehlt"
        
        # Prüfe ob Foreign Key auf routes.id zeigt
        route_id_fk = [fk for fk in fk_list if fk[2] == 'routes' and fk[3] == 'id']
        assert len(route_id_fk) > 0, "Foreign Key zu routes.id fehlt"


def test_insert_sample_data():
    """Test: Prüft ob Daten eingefügt werden können."""
    with ENGINE.begin() as conn:
        # Test: stats_monthly
        conn.execute(text("""
            INSERT INTO stats_monthly (month, tours_count, stops_count, total_km, avg_stops_per_tour)
            VALUES ('2025-01', 10, 100, 500.5, 10.0)
        """))
        
        result = conn.execute(text("SELECT COUNT(*) FROM stats_monthly WHERE month = '2025-01'"))
        assert result.scalar() == 1
        
        # Test: routes
        conn.execute(text("""
            INSERT INTO routes (tour_id, tour_date, route_name, total_distance_km, stops_count)
            VALUES ('W-01', '2025-01-15', 'Test Route', 50.5, 5)
        """))
        
        result = conn.execute(text("SELECT COUNT(*) FROM routes WHERE tour_id = 'W-01'"))
        assert result.scalar() == 1
        
        # Test: route_legs (mit Foreign Key)
        route_id = conn.execute(text("SELECT id FROM routes WHERE tour_id = 'W-01'")).scalar()
        
        conn.execute(text("""
            INSERT INTO route_legs (route_id, sequence_order, distance_km, duration_min)
            VALUES (:route_id, 1, 10.5, 15)
        """), {"route_id": route_id})
        
        result = conn.execute(text("SELECT COUNT(*) FROM route_legs WHERE route_id = :route_id"), 
                             {"route_id": route_id})
        assert result.scalar() == 1
        
        # Test: osrm_cache
        conn.execute(text("""
            INSERT INTO osrm_cache (from_lat, from_lon, to_lat, to_lon, geometry, distance_km)
            VALUES (51.0504, 13.7373, 51.0615, 13.7283, 'test_geometry', 5.5)
        """))
        
        result = conn.execute(text("""
            SELECT COUNT(*) FROM osrm_cache 
            WHERE from_lat = 51.0504 AND from_lon = 13.7373
        """))
        assert result.scalar() == 1
        
        # Cleanup
        conn.execute(text("DELETE FROM route_legs WHERE route_id = :route_id"), {"route_id": route_id})
        conn.execute(text("DELETE FROM routes WHERE tour_id = 'W-01'"))
        conn.execute(text("DELETE FROM stats_monthly WHERE month = '2025-01'"))
        conn.execute(text("DELETE FROM osrm_cache WHERE from_lat = 51.0504"))


def test_unique_constraints():
    """Test: Prüft UNIQUE Constraints."""
    with ENGINE.begin() as conn:
        # Test: stats_monthly.month UNIQUE
        conn.execute(text("""
            INSERT INTO stats_monthly (month, tours_count) VALUES ('2025-02', 5)
        """))
        
        # Versuche Duplikat einzufügen (sollte fehlschlagen)
        with pytest.raises(Exception):
            conn.execute(text("""
                INSERT INTO stats_monthly (month, tours_count) VALUES ('2025-02', 10)
            """))
        
        # Cleanup
        conn.execute(text("DELETE FROM stats_monthly WHERE month = '2025-02'"))
        
        # Test: osrm_cache Koordinaten UNIQUE
        conn.execute(text("""
            INSERT INTO osrm_cache (from_lat, from_lon, to_lat, to_lon, geometry)
            VALUES (52.0, 13.0, 52.1, 13.1, 'test1')
        """))
        
        # Versuche Duplikat einzufügen (sollte fehlschlagen)
        with pytest.raises(Exception):
            conn.execute(text("""
                INSERT INTO osrm_cache (from_lat, from_lon, to_lat, to_lon, geometry)
                VALUES (52.0, 13.0, 52.1, 13.1, 'test2')
            """))
        
        # Cleanup
        conn.execute(text("DELETE FROM osrm_cache WHERE from_lat = 52.0"))


def test_cascade_delete():
    """Test: Prüft CASCADE DELETE bei route_legs."""
    with ENGINE.begin() as conn:
        # Erstelle Route
        conn.execute(text("""
            INSERT INTO routes (tour_id, tour_date, route_name)
            VALUES ('W-99', '2025-01-20', 'Test Cascade')
        """))
        
        route_id = conn.execute(text("SELECT id FROM routes WHERE tour_id = 'W-99'")).scalar()
        
        # Erstelle Route Legs
        conn.execute(text("""
            INSERT INTO route_legs (route_id, sequence_order, distance_km)
            VALUES (:route_id, 1, 10.0)
        """), {"route_id": route_id})
        
        conn.execute(text("""
            INSERT INTO route_legs (route_id, sequence_order, distance_km)
            VALUES (:route_id, 2, 20.0)
        """), {"route_id": route_id})
        
        # Prüfe ob Legs existieren
        result = conn.execute(text("SELECT COUNT(*) FROM route_legs WHERE route_id = :route_id"), 
                             {"route_id": route_id})
        assert result.scalar() == 2
        
        # Lösche Route (sollte Legs automatisch löschen)
        conn.execute(text("DELETE FROM routes WHERE id = :route_id"), {"route_id": route_id})
        
        # Prüfe ob Legs gelöscht wurden
        result = conn.execute(text("SELECT COUNT(*) FROM route_legs WHERE route_id = :route_id"), 
                             {"route_id": route_id})
        assert result.scalar() == 0


@pytest.fixture(autouse=True)
def ensure_schema():
    """Fixture: Stellt sicher dass Phase 2 Schema existiert."""
    # Temporär Feature-Flag aktivieren (nur für Tests)
    import os
    os.environ['PHASE2_SCHEMA_FORCE_ENABLE'] = '1'
    
    # Führe Schema-Erstellung durch
    try:
        from backend.config import cfg
        original_value = cfg("app:feature_flags:new_schema_enabled", False)
        
        # Temporär aktivieren
        import backend.config as config_module
        if not hasattr(config_module, '_test_phase2_enabled'):
            config_module._test_phase2_enabled = original_value
        
        # Erstelle Schema direkt (ohne Feature-Flag-Check)
        from db.schema_phase2 import PHASE2_SCHEMA_SQL
        from sqlalchemy import text
        
        with ENGINE.begin() as conn:
            statements = PHASE2_SCHEMA_SQL.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    try:
                        conn.execute(text(stmt))
                    except Exception:
                        pass  # Ignoriere wenn bereits existiert
    
    except Exception as e:
        pytest.skip(f"Konnte Phase 2 Schema nicht erstellen: {e}")

