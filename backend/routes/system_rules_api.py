"""
API-Endpoint für Systemregeln (Routen-Aufsplittung).
Refactored: Nutzt Service-Layer für saubere Trennung.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.models.system_rules import SystemRulesUpdate
from backend.services.system_rules_service import (
    get_effective_system_rules,
    save_system_rules,
    get_rules_diff
)
import logging
from sqlalchemy import text
from db.core import ENGINE

logger = logging.getLogger(__name__)

router = APIRouter()


def log_audit_entry(
    changed_by: str,
    changed_by_ip: str,
    old_rules: dict,
    new_rules: dict,
    diff: dict
) -> None:
    """
    Speichert Audit-Eintrag in system_rules_audit Tabelle.
    """
    try:
        with ENGINE.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO system_rules_audit 
                    (changed_by, changed_by_ip, old_values, new_values, changed_fields)
                    VALUES (:changed_by, :changed_by_ip, :old_values, :new_values, :changed_fields)
                """),
                {
                    "changed_by": changed_by,
                    "changed_by_ip": changed_by_ip,
                    "old_values": str(old_rules) if old_rules else None,
                    "new_values": str(new_rules) if new_rules else None,
                    "changed_fields": str(list(diff.keys())) if diff else None
                }
            )
        logger.debug(f"Audit-Eintrag gespeichert für Session {changed_by}")
    except Exception as e:
        # Audit-Fehler sollten nicht den Hauptprozess blockieren
        logger.warning(f"Fehler beim Speichern des Audit-Eintrags: {e}")


@router.get("/api/system/rules")
async def get_system_rules():
    """
    Gibt die aktuellen Systemregeln für Routen-Aufsplittung zurück.
    Diese Werte werden vom LLM und der Optimierungs-Engine verwendet.
    """
    try:
        rules = get_effective_system_rules()
        depot_coords = f"{rules.depot_lat}, {rules.depot_lon}"
        
        # Entferne Metadaten für API-Response (source ist nur intern)
        response_data = rules.model_dump(exclude={"source"})
        response_data["depot_coords"] = depot_coords
        
        return JSONResponse(response_data)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Systemregeln: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Systemregeln: {str(e)}")


@router.put("/api/system/rules")
async def update_system_rules(rules_update: SystemRulesUpdate, request: Request):
    """
    Aktualisiert die Systemregeln (nur für authentifizierte Admins).
    Die Regeln werden in config/system_rules.json gespeichert.
    """
    try:
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            logger.warning(f"Unauthorized attempt to update system rules from {request.client.host}")
            raise HTTPException(
                status_code=401, 
                detail="Authentifizierung erforderlich. Bitte melden Sie sich an."
            )
        
        # Lade alte Werte für Audit
        old_rules = get_effective_system_rules()
        old_rules_dict = old_rules.model_dump(exclude={"source"})
        
        # Speichere neue Regeln (Service-Layer validiert bereits)
        try:
            new_rules = save_system_rules(rules_update)
        except PermissionError as perm_err:
            logger.error(
                f"Keine Schreibrechte für Systemregeln (IP: {request.client.host}): {perm_err}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Keine Schreibrechte für Systemregeln-Datei. Bitte prüfen Sie die Dateiberechtigungen."
            )
        except Exception as save_err:
            logger.error(
                f"Fehler beim Speichern der Systemregeln (IP: {request.client.host}): {save_err}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Fehler beim Speichern: {str(save_err)}"
            )
        
        # Berechne Diff für Audit
        diff = get_rules_diff(old_rules, new_rules)
        
        # Log erfolgreiches Update
        changed_fields = list(diff.keys())
        if changed_fields:
            logger.info(
                f"[SYSTEM_RULES] updated by={session_id} "
                f"changed_fields={changed_fields} "
                f"IP={request.client.host}"
            )
        else:
            logger.info(
                f"[SYSTEM_RULES] updated by={session_id} "
                f"(no changes) IP={request.client.host}"
            )
        
        # Speichere Audit-Eintrag
        new_rules_dict = new_rules.model_dump(exclude={"source"})
        log_audit_entry(
            changed_by=session_id,
            changed_by_ip=request.client.host or "unknown",
            old_rules=old_rules_dict,
            new_rules=new_rules_dict,
            diff=diff
        )
        
        # Response (ohne Metadaten)
        response_data = new_rules.model_dump(exclude={"source"})
        response_data["depot_coords"] = f"{new_rules.depot_lat}, {new_rules.depot_lon}"
        
        return JSONResponse({
            "success": True,
            "message": "Systemregeln erfolgreich aktualisiert",
            "rules": response_data,
            "changed_fields": changed_fields
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unerwarteter Fehler beim Aktualisieren der Systemregeln (IP: {request.client.host}): {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern: {str(e)}")


@router.get("/api/system/rules/self-check")
async def system_rules_self_check():
    """
    Health-Check für Systemregeln-API.
    Prüft ob die API funktioniert und die JSON-Datei lesbar ist.
    """
    try:
        rules = get_effective_system_rules()
        
        # Prüfe Schreibrechte
        from pathlib import Path
        from backend.services.system_rules_service import SYSTEM_RULES_FILE
        import os
        
        writable = False
        try:
            SYSTEM_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
            test_file = SYSTEM_RULES_FILE.with_suffix('.test')
            test_file.write_text("test")
            test_file.unlink()
            writable = True
        except Exception:
            pass
        
        status = "ok" if writable else "degraded"
        
        return JSONResponse({
            "status": status,
            "checks": {
                "service_available": True,
                "rules_loadable": True,
                "rules_valid": True,
                "writable": writable,
                "source": rules.source
            },
            "file_path": str(SYSTEM_RULES_FILE),
            "current_rules": {
                "time_budget_without_return": rules.time_budget_without_return,
                "time_budget_with_return": rules.time_budget_with_return,
                "source": rules.source
            },
            "message": f"Systemregeln-API funktioniert (Quelle: {rules.source})" if status == "ok" else "Systemregeln-API hat Probleme (keine Schreibrechte)"
        })
    except Exception as e:
        logger.error(f"Fehler beim Self-Check: {e}", exc_info=True)
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)
