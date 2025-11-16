"""
Venv Health Check - Prüft venv-Status und repariert bei Bedarf.
Wird beim Server-Start automatisch ausgeführt.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)


class VenvHealthCheck:
    """Prüft venv-Status und repariert bei Bedarf."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.venv_path = self.project_root / "venv"
        self.venv_python = self.venv_path / "Scripts" / "python.exe"
        self.site_packages = self.venv_path / "Lib" / "site-packages"
        
    def check_venv_exists(self) -> bool:
        """Prüft ob venv existiert."""
        return self.venv_path.exists() and self.venv_python.exists()
    
    def check_python_path(self) -> Tuple[bool, str]:
        """Prüft welches Python verwendet wird."""
        current_python = sys.executable
        is_venv = "venv" in current_python or "venv" in str(current_python).lower()
        return is_venv, current_python
    
    def check_critical_packages(self) -> Dict[str, bool]:
        """Prüft ob kritische Packages importierbar sind."""
        critical_packages = {
            "sqlalchemy": "from sqlalchemy import text",
            "fastapi": "import fastapi",
            "uvicorn": "import uvicorn",
            "pandas": "import pandas",
        }
        
        results = {}
        for package, import_stmt in critical_packages.items():
            try:
                exec(import_stmt)
                results[package] = True
            except (ImportError, ModuleNotFoundError) as e:
                results[package] = False
                logger.warning(f"Package {package} kann nicht importiert werden: {e}")
        
        return results
    
    def check_metadata_files(self) -> Tuple[bool, List[str]]:
        """Prüft ob METADATA-Dateien fehlen."""
        if not self.site_packages.exists():
            return True, []  # Kein site-packages = kein Problem
        
        missing_metadata = []
        dist_info_dirs = list(self.site_packages.glob("*.dist-info"))
        
        for dist_info in dist_info_dirs:
            metadata_file = dist_info / "METADATA"
            if not metadata_file.exists():
                package_name = dist_info.name.replace(".dist-info", "")
                missing_metadata.append(package_name)
                logger.warning(f"METADATA fehlt für: {package_name}")
        
        return len(missing_metadata) == 0, missing_metadata
    
    def check_pip_works(self) -> bool:
        """Prüft ob pip funktioniert."""
        try:
            result = subprocess.run(
                [str(self.venv_python), "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Pip-Check fehlgeschlagen: {e}")
            return False
    
    def run_full_check(self) -> Dict:
        """Führt vollständigen Health-Check durch."""
        results = {
            "venv_exists": False,
            "python_path_ok": False,
            "python_path": "",
            "critical_packages_ok": False,
            "critical_packages": {},
            "metadata_ok": False,
            "missing_metadata": [],
            "pip_works": False,
            "overall_status": "unknown",
            "recommendation": ""
        }
        
        # 1. Venv existiert?
        results["venv_exists"] = self.check_venv_exists()
        if not results["venv_exists"]:
            results["overall_status"] = "error"
            results["recommendation"] = "Venv nicht gefunden. Bitte erstellen: python -m venv venv"
            return results
        
        # 2. Python-Pfad prüfen
        is_venv, python_path = self.check_python_path()
        results["python_path_ok"] = is_venv
        results["python_path"] = python_path
        
        # 3. Kritische Packages prüfen
        critical_results = self.check_critical_packages()
        results["critical_packages"] = critical_results
        results["critical_packages_ok"] = all(critical_results.values())
        
        # 4. METADATA-Dateien prüfen
        metadata_ok, missing = self.check_metadata_files()
        results["metadata_ok"] = metadata_ok
        results["missing_metadata"] = missing
        
        # 5. Pip funktioniert?
        results["pip_works"] = self.check_pip_works()
        
        # Gesamt-Status bestimmen
        if not results["python_path_ok"]:
            results["overall_status"] = "warning"
            results["recommendation"] = "Venv nicht aktiviert. Bitte aktivieren: .\\venv\\Scripts\\Activate.ps1"
        elif not results["critical_packages_ok"]:
            results["overall_status"] = "error"
            failed = [pkg for pkg, ok in critical_results.items() if not ok]
            results["recommendation"] = f"Kritische Packages fehlen: {', '.join(failed)}. Bitte installieren: pip install -r requirements.txt"
        elif not results["metadata_ok"]:
            results["overall_status"] = "error"
            results["recommendation"] = f"Venv beschädigt ({len(missing)} Packages). Bitte venv neu erstellen: .\\recreate_venv.ps1"
        elif not results["pip_works"]:
            results["overall_status"] = "error"
            results["recommendation"] = "Pip funktioniert nicht. Bitte venv neu erstellen: .\\recreate_venv.ps1"
        else:
            results["overall_status"] = "ok"
            results["recommendation"] = "Alles OK - Server kann gestartet werden"
        
        return results
    
    def auto_fix(self, results: Dict) -> bool:
        """Versucht automatische Reparatur."""
        if results["overall_status"] == "ok":
            return True
        
        logger.info("Versuche automatische Reparatur...")
        
        # Fall 1: Venv nicht aktiviert - kann nicht automatisch gefixt werden
        if not results["python_path_ok"]:
            logger.warning("Venv nicht aktiviert - bitte manuell aktivieren")
            return False
        
        # Fall 2: Kritische Packages fehlen - versuche Installation
        if not results["critical_packages_ok"]:
            failed = [pkg for pkg, ok in results["critical_packages"].items() if not ok]
            logger.info(f"Installiere fehlende Packages: {', '.join(failed)}")
            try:
                subprocess.run(
                    [str(self.venv_python), "-m", "pip", "install", "-r", str(self.project_root / "requirements.txt")],
                    check=True,
                    timeout=300
                )
                logger.info("Packages erfolgreich installiert")
                return True
            except Exception as e:
                logger.error(f"Automatische Installation fehlgeschlagen: {e}")
                return False
        
        # Fall 3: METADATA fehlt - zu viele betroffen → venv neu erstellen empfohlen
        if not results["metadata_ok"]:
            missing_count = len(results["missing_metadata"])
            if missing_count > 3:
                logger.warning(f"Zu viele beschädigte Packages ({missing_count}) - venv sollte neu erstellt werden")
                logger.info("Führe recreate_venv.ps1 aus...")
                return False  # Keine automatische Neu-Erstellung (zu riskant)
            else:
                # Versuche beschädigte Packages neu zu installieren
                logger.info(f"Repariere {missing_count} beschädigte Package(s)...")
                for package in results["missing_metadata"]:
                    try:
                        subprocess.run(
                            [str(self.venv_python), "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", package],
                            check=True,
                            timeout=60
                        )
                    except Exception as e:
                        logger.warning(f"Reparatur von {package} fehlgeschlagen: {e}")
                return True
        
        return False


def run_venv_health_check(auto_fix: bool = True) -> bool:
    """
    Führt venv Health-Check durch.
    
    Args:
        auto_fix: Wenn True, versucht automatische Reparatur
        
    Returns:
        True wenn alles OK, False wenn Probleme bestehen
    """
    checker = VenvHealthCheck()
    results = checker.run_full_check()
    
    logger.info("=" * 70)
    logger.info("VENV HEALTH CHECK")
    logger.info("=" * 70)
    logger.info(f"Venv existiert: {results['venv_exists']}")
    logger.info(f"Python-Pfad OK: {results['python_path_ok']} ({results['python_path']})")
    logger.info(f"Kritische Packages OK: {results['critical_packages_ok']}")
    logger.info(f"  - SQLAlchemy: {results['critical_packages'].get('sqlalchemy', False)}")
    logger.info(f"  - FastAPI: {results['critical_packages'].get('fastapi', False)}")
    logger.info(f"  - Uvicorn: {results['critical_packages'].get('uvicorn', False)}")
    logger.info(f"  - Pandas: {results['critical_packages'].get('pandas', False)}")
    logger.info(f"METADATA OK: {results['metadata_ok']}")
    if results['missing_metadata']:
        logger.warning(f"  Fehlende METADATA: {', '.join(results['missing_metadata'][:5])}")
    logger.info(f"Pip funktioniert: {results['pip_works']}")
    logger.info(f"Status: {results['overall_status'].upper()}")
    logger.info(f"Empfehlung: {results['recommendation']}")
    logger.info("=" * 70)
    
    if results["overall_status"] == "ok":
        logger.info("[OK] Venv Health Check: OK - Server kann gestartet werden")
        return True
    
    if results["overall_status"] == "warning":
        logger.warning("[WARNUNG] Venv Health Check: WARNUNG")
        logger.warning(f"   {results['recommendation']}")
        if auto_fix:
            if checker.auto_fix(results):
                logger.info("[OK] Automatische Reparatur erfolgreich")
                return True
        return False
    
    if results["overall_status"] == "error":
        logger.error("[FEHLER] Venv Health Check: FEHLER")
        logger.error(f"   {results['recommendation']}")
        if auto_fix:
            if checker.auto_fix(results):
                logger.info("[OK] Automatische Reparatur erfolgreich - erneuter Check...")
                # Erneuter Check nach Reparatur
                results = checker.run_full_check()
                if results["overall_status"] == "ok":
                    return True
        logger.error("[FEHLER] Venv-Problem konnte nicht automatisch behoben werden")
        logger.error("   Bitte manuell beheben oder recreate_venv.ps1 ausführen")
        return False
    
    return False

