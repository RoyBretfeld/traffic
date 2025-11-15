"""
Service-Layer für Systemregeln.
Zentrale Logik für Laden, Speichern und Validierung von Systemregeln.
"""
from pathlib import Path
import os
import json
import logging
from typing import Optional, Dict, Any
from backend.models.system_rules import SystemRules, SystemRulesUpdate

logger = logging.getLogger(__name__)

# Pfad zur Systemregeln-JSON-Datei
SYSTEM_RULES_FILE = Path("config/system_rules.json")

# Standardwerte
DEFAULT_RULES = {
    "time_budget_without_return": 65,
    "time_budget_with_return": 90,
    "service_time_per_stop": 2.0,
    "speed_kmh": 50.0,
    "safety_factor": 1.3,
    "depot_lat": 51.0111988,
    "depot_lon": 13.7016485,
    "rules_version": "1.0"
}


def get_default_rules() -> SystemRules:
    """Gibt Standard-Systemregeln zurück."""
    return SystemRules(**DEFAULT_RULES, source="default")


def load_rules_from_file() -> Optional[SystemRules]:
    """
    Lädt Systemregeln aus JSON-Datei.
    
    Returns:
        SystemRules wenn Datei existiert und gültig ist, sonst None
    """
    if not SYSTEM_RULES_FILE.exists():
        return None
    
    try:
        with open(SYSTEM_RULES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validiere mit Pydantic
        rules = SystemRules(**data, source="file")
        logger.debug(f"Systemregeln geladen aus {SYSTEM_RULES_FILE}")
        return rules
        
    except json.JSONDecodeError as e:
        logger.error(
            f"Ungültige JSON-Datei {SYSTEM_RULES_FILE}: {e}",
            exc_info=True
        )
        return None
    except Exception as e:
        logger.error(
            f"Fehler beim Laden der Systemregeln aus {SYSTEM_RULES_FILE}: {e}",
            exc_info=True
        )
        return None


def load_rules_from_env() -> Optional[SystemRules]:
    """
    Lädt Systemregeln aus Environment-Variablen.
    
    Returns:
        SystemRules wenn Env-Variablen gesetzt sind, sonst None
    """
    try:
        env_rules = {}
        
        # Prüfe ob mindestens eine Env-Variable gesetzt ist
        if os.getenv("TIME_BUDGET_WITHOUT_RETURN"):
            env_rules["time_budget_without_return"] = int(os.getenv("TIME_BUDGET_WITHOUT_RETURN"))
        if os.getenv("TIME_BUDGET_WITH_RETURN"):
            env_rules["time_budget_with_return"] = int(os.getenv("TIME_BUDGET_WITH_RETURN"))
        if os.getenv("SERVICE_TIME_PER_STOP"):
            env_rules["service_time_per_stop"] = float(os.getenv("SERVICE_TIME_PER_STOP"))
        if os.getenv("SPEED_KMH"):
            env_rules["speed_kmh"] = float(os.getenv("SPEED_KMH"))
        if os.getenv("SAFETY_FACTOR"):
            env_rules["safety_factor"] = float(os.getenv("SAFETY_FACTOR"))
        if os.getenv("DEPOT_LAT"):
            env_rules["depot_lat"] = float(os.getenv("DEPOT_LAT"))
        if os.getenv("DEPOT_LON"):
            env_rules["depot_lon"] = float(os.getenv("DEPOT_LON"))
        
        if not env_rules:
            return None
        
        # Merge mit Defaults
        default_dict = DEFAULT_RULES.copy()
        default_dict.update(env_rules)
        
        rules = SystemRules(**default_dict, source="env")
        logger.debug("Systemregeln geladen aus Environment-Variablen")
        return rules
        
    except Exception as e:
        logger.warning(f"Fehler beim Laden der Systemregeln aus Env: {e}")
        return None


def get_effective_system_rules() -> SystemRules:
    """
    Lädt effektive Systemregeln mit klarer Priorität:
    1. JSON-Datei (wenn vorhanden und gültig)
    2. Environment-Variablen (wenn gesetzt)
    3. Standardwerte
    
    Returns:
        SystemRules: Die effektiven Systemregeln
    """
    # 1. Versuche JSON-Datei
    rules = load_rules_from_file()
    if rules:
        logger.info(f"Systemregeln geladen aus Datei: {SYSTEM_RULES_FILE}")
        return rules
    
    # 2. Versuche Environment-Variablen
    rules = load_rules_from_env()
    if rules:
        logger.info("Systemregeln geladen aus Environment-Variablen")
        return rules
    
    # 3. Fallback auf Standardwerte
    logger.info("Systemregeln verwenden Standardwerte")
    return get_default_rules()


def save_system_rules(rules: SystemRulesUpdate) -> SystemRules:
    """
    Speichert Systemregeln in JSON-Datei (atomar via temp-Datei).
    
    Args:
        rules: Die zu speichernden Systemregeln
        
    Returns:
        SystemRules: Die gespeicherten Regeln (inkl. Metadaten)
        
    Raises:
        PermissionError: Wenn keine Schreibrechte vorhanden sind
        OSError: Bei anderen I/O-Fehlern
    """
    # Stelle sicher, dass Verzeichnis existiert
    SYSTEM_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Konvertiere Update zu vollständigen Rules
    rules_dict = rules.model_dump()
    rules_dict["rules_version"] = DEFAULT_RULES.get("rules_version", "1.0")
    
    # Validiere vor dem Schreiben
    validated_rules = SystemRules(**rules_dict, source="file")
    
    # Atomares Schreiben: temp-Datei → dann os.replace()
    temp_file = SYSTEM_RULES_FILE.with_suffix('.json.tmp')
    
    try:
        # Schreibe in temp-Datei
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(rules_dict, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        # Atomare Operation: temp → final
        temp_file.replace(SYSTEM_RULES_FILE)
        
        logger.info(f"Systemregeln gespeichert: {SYSTEM_RULES_FILE}")
        return validated_rules
        
    except PermissionError as perm_err:
        logger.error(
            f"Keine Schreibrechte für {SYSTEM_RULES_FILE}: {perm_err}",
            exc_info=True
        )
        raise
    except OSError as os_err:
        logger.error(
            f"OS-Fehler beim Speichern von {SYSTEM_RULES_FILE}: {os_err}",
            exc_info=True
        )
        raise
    except Exception as write_error:
        logger.error(
            f"Unerwarteter Fehler beim Speichern von {SYSTEM_RULES_FILE}: {write_error}",
            exc_info=True
        )
        raise
    finally:
        # Cleanup: Lösche temp-Datei bei Fehler
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


def get_rules_diff(old_rules: SystemRules, new_rules: SystemRules) -> Dict[str, Dict[str, Any]]:
    """
    Berechnet Diff zwischen alten und neuen Systemregeln.
    
    Returns:
        Dict mit geänderten Feldern: {"field_name": {"old": ..., "new": ...}}
    """
    diff = {}
    
    for field_name in SystemRules.model_fields.keys():
        if field_name in ["source", "rules_version"]:
            continue
        
        old_value = getattr(old_rules, field_name, None)
        new_value = getattr(new_rules, field_name, None)
        
        if old_value != new_value:
            diff[field_name] = {
                "old": old_value,
                "new": new_value
            }
    
    return diff

