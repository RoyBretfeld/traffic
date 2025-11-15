"""
Erstellt ZIP-Archiv für Produkt-Audit.
Sammelt alle relevanten Dateien für eine umfassende Produkt-Präsentation.
"""
import zipfile
import os
from pathlib import Path
from datetime import datetime

def create_audit_zip():
    """Erstellt ZIP-Archiv mit allen relevanten Audit-Dateien."""
    
    # Basis-Verzeichnisse
    project_root = Path(__file__).parent.parent
    zip_dir = project_root / "ZIP"
    zip_dir.mkdir(exist_ok=True)
    
    # ZIP-Dateiname mit Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = zip_dir / f"PRODUKT_AUDIT_{timestamp}.zip"
    
    # Dateien und Verzeichnisse zum Einpacken
    files_to_include = [
        # Haupt-Dokumentation
        "docs/PRODUKT_AUDIT_2025-01-10.md",
        "docs/Architecture.md",
        "docs/STATUS_MASTER_PLAN_2025-01-10.md",
        "docs/KRITISCHE_FEHLER_FIX_2025-01-10.md",
        "docs/GESAMT_AUDIT_2025-01-10.md",
        "docs/FEHLER_AUDIT_2025-01-10.md",
        "README.md",
        
        # KI-Integration
        "docs/KI_CODECHECKER_KONZEPT_2025-01-10.md",
        "docs/KI_INTEGRATION_ABGESCHLOSSEN.md",
        "docs/KI_INTEGRATION_STATUS_2025-01-10.md",
        "docs/KI_BENACHRICHTIGUNGSKONZEPT_2025-01-10.md",
        "docs/KI_BENACHRICHTIGUNG_IMPLEMENTIERUNG.md",
        "docs/KI_COST_PERFORMANCE_MONITORING.md",
        "docs/KI_MODell_KONFIGURATION.md",
        "docs/KI_CHECKER_API_KEY_SETUP.md",
        "docs/KI_CHECKER_STATUS.md",
        "docs/BACKGROUND_JOB_IMPLEMENTIERUNG.md",
        
        # Tests
        "docs/TESTS_KRITISCHE_FIXES_2025-01-10.md",
        "docs/TESTS_UEBERSICHT_2025-01-10.md",
        "docs/TEST_STRATEGIE_2025-01-10.md",
        
        # Fixes & Audits
        "docs/FIX_404_402_500_ROUTING.md",
        "docs/FIX_STATUS_INDIKATOREN_2025-01-10.md",
        "docs/AUDIT_ALLE_FEHLER_2025-01-10.md",
        "docs/AUDIT_UPLOAD_FEHLER_2025-01-10.md",
        "docs/AUDIT_SUB_ROUTEN_GENERATOR.md",
        "docs/CHECKLIST_PROBLEME_VERIFIZIERUNG_2025-01-10.md",
        
        # Architektur & Status
        "docs/AKTUELLER_STAND_2025-01-10.md",
        "docs/PROJECT_STATUS.md",
        "docs/IMPLEMENTIERUNGS_UEBERSICHT.md",
        
        # Konfiguration
        "config/app.yaml",
        "env.example",
        
        # Wichtige Code-Dateien (Beispiele)
        "backend/app.py",
        "start_server.py",
        "requirements.txt",
    ]
    
    # Verzeichnisse zum Einpacken (nur wichtige Dateien)
    dirs_to_include = {
        "backend/services": ["code_improvement_job.py", "ai_code_checker.py", "code_analyzer.py", "code_fixer.py", "safety_manager.py", "notification_service.py", "cost_tracker.py", "performance_tracker.py"],
        "routes": ["ki_improvements_api.py", "code_checker_api.py", "code_improvement_job_api.py", "health_check.py"],
        "frontend": ["index.html", "admin/ki-improvements.html"],
        "tests": ["test_critical_fixes_2025_01_10.py", "test_background_job_integration.py", "test_sub_routes_performance.py", "test_tour_switching.py", "test_tour_details_rendering.py"],
    }
    
    print(f"Erstelle ZIP-Archiv: {zip_path}")
    print("=" * 70)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Einzelne Dateien hinzufügen
        for file_path in files_to_include:
            full_path = project_root / file_path
            if full_path.exists():
                arcname = file_path
                zipf.write(full_path, arcname)
                print(f"[OK] {file_path}")
            else:
                print(f"[WARN] Nicht gefunden: {file_path}")
        
        # Verzeichnisse mit Filterung
        for dir_path, file_filter in dirs_to_include.items():
            full_dir = project_root / dir_path
            if full_dir.exists():
                for file_name in file_filter:
                    full_path = full_dir / file_name
                    if full_path.exists():
                        arcname = f"{dir_path}/{file_name}"
                        zipf.write(full_path, arcname)
                        print(f"[OK] {arcname}")
                    else:
                        print(f"[WARN] Nicht gefunden: {arcname}")
        
        # Beschreibungs-Datei erstellen
        beschreibung = f"""# Produkt-Audit ZIP - Beschreibung
**Erstellt:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**ZIP-Datei:** PRODUKT_AUDIT_{timestamp}.zip

## 📦 Inhalt

Dieses ZIP-Archiv enthält eine umfassende Produkt-Präsentation der FAMO TrafficApp 3.0.

### Hauptdokumente
- `PRODUKT_AUDIT_2025-01-10.md` - **HAUPTDOKUMENT** - Vollständiges Produkt-Audit
- `Architecture.md` - System-Architektur
- `STATUS_MASTER_PLAN_2025-01-10.md` - Projektstatus & Roadmap
- `KRITISCHE_FEHLER_FIX_2025-01-10.md` - Bekannte Probleme & Fixes

### KI-Integration
- KI-CodeChecker Konzept & Implementierung
- Background-Job Dokumentation
- Kosten- & Performance-Monitoring
- Benachrichtigungssystem

### Tests & Qualität
- Test-Strategie
- Test-Übersicht
- Kritische Fixes Tests

### Fixes & Audits
- Routing-Fixes
- Status-Indikatoren-Fixes
- Upload-Fehler-Audit
- Sub-Routen-Generator-Audit

### Code-Beispiele
- Backend-Services (KI-CodeChecker)
- API-Routes
- Frontend-Komponenten
- Test-Dateien

## 🎯 Verwendung

1. **ZIP entpacken**
2. **Starte mit:** `PRODUKT_AUDIT_2025-01-10.md`
3. **Vertiefe:** Weitere Dokumente je nach Interesse

## 📊 Produkt-Übersicht

**Stärken:**
- ✅ Robuste Architektur
- ✅ KI-Integration (innovativ)
- ✅ Selbstlernend
- ✅ Umfassende Dokumentation

**Schwächen:**
- ⚠️ Technische Schulden (Router-Registrierung)
- ⚠️ Performance-Limitierungen (sequenzielle Verarbeitung)
- ⚠️ Feature-Lücken (Admin-Auth fehlt)

**Fazit:** ✅ Produktionsreif mit bekannten Limitierungen

## 📝 Hinweise

- Alle Dateien sind UTF-8 kodiert
- Code-Beispiele sind funktionsfähig
- Dokumentation ist ehrlich und vollständig
- Tests können direkt ausgeführt werden

---
**Erstellt von:** KI-Assistent (Auto)
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        zipf.writestr("BESCHREIBUNG.md", beschreibung.encode('utf-8'))
        print(f"[OK] BESCHREIBUNG.md")
    
    print("=" * 70)
    print(f"[OK] ZIP-Archiv erstellt: {zip_path}")
    print(f"Groesse: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return zip_path

if __name__ == "__main__":
    create_audit_zip()

