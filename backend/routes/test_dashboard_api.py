"""API für Test-Dashboard mit Modularitäts-Übersicht."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
from backend.routes.auth_api import require_admin

router = APIRouter(prefix="/api/tests", tags=["tests"], dependencies=[Depends(require_admin)])


def run_pytest_collect_only() -> List[Dict[str, Any]]:
    """Sammelt alle verfügbaren Tests ohne sie auszuführen."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        tests = []
        for line in result.stdout.split("\n"):
            if "::test_" in line or "::Test" in line:
                test_name = line.strip().split("::")[-1]
                module = line.strip().split("::")[0] if "::" in line else "unknown"
                tests.append({
                    "name": test_name,
                    "module": module.replace("tests/", "").replace(".py", ""),
                    "full_path": line.strip()
                })
        return tests
    except Exception as e:
        return [{"error": str(e)}]


def get_test_modules() -> Dict[str, Any]:
    """Ermittelt Test-Module und deren Status."""
    modules = {
        "admin": {
            "name": "Admin-UI",
            "tests": ["test_admin_app"],
            "status": "unknown",
            "dependencies": ["backend.services.address_corrections", "migrations"]
        },
        "address_corrections": {
            "name": "Address Corrections",
            "tests": ["test_address_corrections"],
            "status": "unknown",
            "dependencies": ["backend.services.address_corrections", "migrations"]
        },
        "normalize": {
            "name": "Address Normalization",
            "tests": ["test_normalize_address"],
            "status": "unknown",
            "dependencies": ["common.normalize", "common.text_cleaner"]
        },
        "geocoding": {
            "name": "Geocoding",
            "tests": ["test_manual_geo", "test_match_enforce_and_manual"],
            "status": "unknown",
            "dependencies": ["services.geocode_fill", "repositories.geo_repo", "backend.services.geocode", "services.geocode_fill"]
        },
        "workflow": {
            "name": "Workflow Engine",
            "tests": ["test_workflow"],
            "status": "unknown",
            "dependencies": ["services.workflow_engine", "routes.workflow_api", "backend.services.address_corrections"]
        },
        "database": {
            "name": "Database & Migrations",
            "tests": ["test_db_migration"],
            "status": "unknown",
            "dependencies": ["db.schema", "db.core", "db.migrations", "db.schema_alias", "db.schema_manual"]
        },
        "backup": {
            "name": "Database Backup System",
            "tests": ["test_db_backup", "test_backup_api"],
            "status": "unknown",
            "dependencies": ["scripts.db_backup", "routes.backup_api"]
        },
        "bulk_process": {
            "name": "Bulk CSV Processing",
            "tests": ["test_bulk_process"],
            "status": "unknown",
            "dependencies": ["routes.tourplan_bulk_process", "backend.parsers.tour_plan_parser"]
        },
        "w_route_optimization": {
            "name": "W-Route Optimization",
            "tests": [],
            "status": "unknown",
            "dependencies": ["services.w_route_optimizer", "services.llm_optimizer"]
        }
    }
    return modules


@router.get("/status")
async def test_status() -> JSONResponse:
    """Liefert Gesamtstatus aller Tests."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_admin_app.py", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        passed = result.stdout.count("PASSED")
        failed = result.stdout.count("FAILED")
        total = passed + failed
        
        status = "green" if failed == 0 and total > 0 else "red" if failed > 0 else "unknown"
        
        return JSONResponse({
            "status": status,
            "total": total,
            "passed": passed,
            "failed": failed,
            "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
        })
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


@router.get("/modules")
async def test_modules() -> JSONResponse:
    """Liefert Modularitäts-Übersicht."""
    modules = get_test_modules()
    
    # Versuche Test-Status für jedes Modul zu ermitteln
    for mod_key, mod_info in modules.items():
        test_files = mod_info.get("tests", [])
        if test_files:
            try:
                test_paths = [f"tests/test_{t}.py" if not t.startswith("test_") else f"tests/{t}.py" for t in test_files]
                test_paths = [p for p in test_paths if Path(p).exists()]
                
                if test_paths:
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", *test_paths, "-v", "--tb=no", "-q"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=str(Path(__file__).parent.parent)  # Stelle sicher, dass wir im Projekt-Root sind
                    )
                    failed = result.returncode != 0 or "FAILED" in result.stdout or "FAILED" in result.stderr
                    mod_info["status"] = "red" if failed else "green"
                else:
                    mod_info["status"] = "unknown"
            except Exception:
                mod_info["status"] = "unknown"
        else:
            mod_info["status"] = "unknown"
    
    return JSONResponse({"modules": modules})


@router.get("/list")
async def test_list() -> JSONResponse:
    """Listet alle verfügbaren Tests auf."""
    tests = run_pytest_collect_only()
    return JSONResponse({"tests": tests, "count": len(tests)})


@router.post("/run")
async def run_tests(request: Request) -> JSONResponse:
    """Führt Tests für spezifische Dateien aus."""
    try:
        body = await request.json()
        test_files = body.get("test_files", [])
        
        if not test_files:
            return JSONResponse({
                "success": False,
                "message": "Keine Test-Dateien angegeben"
            }, status_code=400)
        
        # Filtere nur existierende Dateien
        existing_files = [f for f in test_files if Path(f).exists()]
        
        if not existing_files:
            return JSONResponse({
                "success": False,
                "message": "Keine gültigen Test-Dateien gefunden"
            }, status_code=400)
        
        # Führe Tests aus
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *existing_files, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        passed = result.stdout.count("PASSED")
        failed = result.stdout.count("FAILED")
        success = result.returncode == 0
        
        return JSONResponse({
            "success": success,
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "output": result.stdout,
            "returncode": result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return JSONResponse({
            "success": False,
            "message": "Tests haben Zeitüberschreitung (120s)",
            "output": "Timeout: Tests dauern zu lange"
        }, status_code=408)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Fehler beim Ausführen: {str(e)}"
        }, status_code=500)

