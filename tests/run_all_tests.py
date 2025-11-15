"""
Test-Runner für alle Tests.
Führt alle Tests aus und gibt eine Zusammenfassung.
"""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Führt alle Tests aus."""
    test_files = [
        "tests/test_routing_health_fixes.py",
        "tests/test_ki_codechecker.py",
        "tests/test_code_checker_api.py",
        "tests/test_ki_improvements_api.py",
        "tests/test_all_fixes_integration.py",
        "tests/test_upload_match_flow.py",
        "tests/test_api_health.py",
        # Neue Tests für kritische Fixes vom 2025-01-10
        "tests/test_critical_fixes_2025_01_10.py",
        "tests/test_background_job_integration.py",
        "tests/test_sub_routes_performance.py",
        "tests/test_tour_switching.py",
        "tests/test_tour_details_rendering.py",
        "tests/test_route_details.py", # Neuer Test für Routendetails
    ]
    
    print("=" * 70)
    print("Führe alle Tests aus...")
    print("=" * 70)
    
    results = []
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"⚠️  Datei nicht gefunden: {test_file}")
            continue
        
        print(f"\n📋 Teste: {test_file}")
        print("-" * 70)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file}: Alle Tests bestanden")
                results.append((test_file, True, result.stdout))
            else:
                print(f"❌ {test_file}: Einige Tests fehlgeschlagen")
                print(result.stdout)
                print(result.stderr)
                results.append((test_file, False, result.stdout + result.stderr))
        except subprocess.TimeoutExpired:
            print(f"⏱️  {test_file}: Timeout (>5 Minuten)")
            results.append((test_file, False, "Timeout"))
        except Exception as e:
            print(f"❌ {test_file}: Fehler beim Ausführen: {e}")
            results.append((test_file, False, str(e)))
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_file, success, output in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_file}")
    
    print(f"\nErgebnis: {passed}/{total} Test-Dateien bestanden")
    
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

