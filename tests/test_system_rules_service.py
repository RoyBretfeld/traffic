"""
Tests für Systemregeln-Service.
Prüft Laden, Speichern und Validierung von Systemregeln.
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
from backend.services.system_rules_service import (
    get_default_rules,
    load_rules_from_file,
    save_system_rules,
    get_effective_system_rules,
    get_rules_diff,
    SYSTEM_RULES_FILE
)
from backend.models.system_rules import SystemRules, SystemRulesUpdate


class TestSystemRulesService:
    """Tests für Systemregeln-Service."""
    
    def test_get_default_rules(self):
        """Test: Standard-Regeln werden korrekt zurückgegeben."""
        rules = get_default_rules()
        assert isinstance(rules, SystemRules)
        assert rules.time_budget_without_return == 65
        assert rules.time_budget_with_return == 90
        assert rules.source == "default"
    
    def test_load_rules_from_file_valid(self):
        """Test: Gültige JSON-Datei wird korrekt geladen."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "system_rules.json"
            test_data = {
                "time_budget_without_return": 70,
                "time_budget_with_return": 95,
                "service_time_per_stop": 2.5,
                "speed_kmh": 55.0,
                "safety_factor": 1.4,
                "depot_lat": 51.0,
                "depot_lon": 13.7,
                "rules_version": "1.0"
            }
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)
            
            # Temporär SYSTEM_RULES_FILE überschreiben
            import backend.services.system_rules_service as service_module
            original_file = service_module.SYSTEM_RULES_FILE
            service_module.SYSTEM_RULES_FILE = test_file
            
            try:
                rules = load_rules_from_file()
                assert rules is not None
                assert rules.time_budget_without_return == 70
                assert rules.source == "file"
            finally:
                service_module.SYSTEM_RULES_FILE = original_file
    
    def test_load_rules_from_file_invalid_json(self):
        """Test: Ungültige JSON-Datei führt zu None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "system_rules.json"
            test_file.write_text("invalid json {")
            
            import backend.services.system_rules_service as service_module
            original_file = service_module.SYSTEM_RULES_FILE
            service_module.SYSTEM_RULES_FILE = test_file
            
            try:
                rules = load_rules_from_file()
                assert rules is None
            finally:
                service_module.SYSTEM_RULES_FILE = original_file
    
    def test_load_rules_from_file_missing(self):
        """Test: Fehlende Datei führt zu None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "nonexistent.json"
            
            import backend.services.system_rules_service as service_module
            original_file = service_module.SYSTEM_RULES_FILE
            service_module.SYSTEM_RULES_FILE = test_file
            
            try:
                rules = load_rules_from_file()
                assert rules is None
            finally:
                service_module.SYSTEM_RULES_FILE = original_file
    
    def test_save_system_rules_atomic_write(self):
        """Test: Atomares Schreiben funktioniert."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "system_rules.json"
            
            import backend.services.system_rules_service as service_module
            original_file = service_module.SYSTEM_RULES_FILE
            service_module.SYSTEM_RULES_FILE = test_file
            
            try:
                update = SystemRulesUpdate(
                    time_budget_without_return=70,
                    time_budget_with_return=95,
                    service_time_per_stop=2.5,
                    speed_kmh=55.0,
                    safety_factor=1.4,
                    depot_lat=51.0,
                    depot_lon=13.7
                )
                
                saved_rules = save_system_rules(update)
                
                # Prüfe dass Datei existiert
                assert test_file.exists()
                
                # Prüfe dass temp-Datei nicht existiert
                temp_file = test_file.with_suffix('.json.tmp')
                assert not temp_file.exists()
                
                # Prüfe dass gespeicherte Regeln korrekt sind
                assert saved_rules.time_budget_without_return == 70
                assert saved_rules.source == "file"
                
                # Roundtrip: Lade wieder
                loaded = load_rules_from_file()
                assert loaded is not None
                assert loaded.time_budget_without_return == 70
                
            finally:
                service_module.SYSTEM_RULES_FILE = original_file
    
    def test_get_rules_diff(self):
        """Test: Diff-Berechnung funktioniert."""
        old_rules = SystemRules(
            time_budget_without_return=65,
            time_budget_with_return=90,
            service_time_per_stop=2.0,
            speed_kmh=50.0,
            safety_factor=1.3,
            depot_lat=51.0111988,
            depot_lon=13.7016485,
            source="default"
        )
        
        new_rules = SystemRules(
            time_budget_without_return=70,
            time_budget_with_return=95,
            service_time_per_stop=2.5,
            speed_kmh=55.0,
            safety_factor=1.4,
            depot_lat=51.0,
            depot_lon=13.7,
            source="file"
        )
        
        diff = get_rules_diff(old_rules, new_rules)
        
        assert "time_budget_without_return" in diff
        assert diff["time_budget_without_return"]["old"] == 65
        assert diff["time_budget_without_return"]["new"] == 70
        
        assert "speed_kmh" in diff
        assert diff["speed_kmh"]["old"] == 50.0
        assert diff["speed_kmh"]["new"] == 55.0
    
    def test_validation_time_budgets(self):
        """Test: Validierung verhindert ungültige Zeitbudgets."""
        with pytest.raises(ValueError, match="Zeitbudget ohne Rückfahrt.*darf nicht größer sein"):
            SystemRulesUpdate(
                time_budget_without_return=100,
                time_budget_with_return=90,  # Ungültig: ohne > mit
                service_time_per_stop=2.0,
                speed_kmh=50.0,
                safety_factor=1.3,
                depot_lat=51.0,
                depot_lon=13.7
            )
    
    def test_validation_positive_values(self):
        """Test: Validierung verhindert negative/Null-Werte."""
        with pytest.raises(ValueError, match="Service-Zeit.*muss größer als 0"):
            SystemRulesUpdate(
                time_budget_without_return=65,
                time_budget_with_return=90,
                service_time_per_stop=0.0,  # Ungültig
                speed_kmh=50.0,
                safety_factor=1.3,
                depot_lat=51.0,
                depot_lon=13.7
            )
        
        with pytest.raises(ValueError, match="Geschwindigkeit.*muss größer als 0"):
            SystemRulesUpdate(
                time_budget_without_return=65,
                time_budget_with_return=90,
                service_time_per_stop=2.0,
                speed_kmh=0.0,  # Ungültig
                safety_factor=1.3,
                depot_lat=51.0,
                depot_lon=13.7
            )

