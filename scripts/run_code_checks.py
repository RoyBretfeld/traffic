#!/usr/bin/env python3
"""
Code-Check-Script: Führt interne Codechecks durch und zeigt Verbesserungen.
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Projekt-Root hinzufügen
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from backend.services.ai_code_checker import get_ai_code_checker
    from backend.services.code_analyzer import analyze_code_file
    from services.code_quality_monitor import CodeQualityMonitor
    from backend.services.cost_tracker import get_cost_tracker
    from backend.services.performance_tracker import get_performance_tracker
except ImportError as e:
    print(f"Fehler beim Import: {e}")
    print("Stelle sicher, dass alle Dependencies installiert sind.")
    sys.exit(1)


def check_file(file_path: Path, use_ai: bool = False) -> Dict[str, Any]:
    """Führt Codecheck für eine Datei durch."""
    print(f"\n{'='*60}")
    print(f"Prüfe: {file_path.relative_to(ROOT)}")
    print(f"{'='*60}")
    
    results = {
        "file": str(file_path.relative_to(ROOT)),
        "local_analysis": {},
        "quality_monitor": {},
        "ai_analysis": {},
        "summary": {}
    }
    
    # 1. Lokale Code-Analyse (kostenlos)
    try:
        print("\n[1/3] Lokale Code-Analyse...")
        local_issues = analyze_code_file(file_path)
        results["local_analysis"] = {
            "issues_count": len(local_issues),
            "issues": [
                {
                    "type": issue.type,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "line": issue.line,
                    "suggestion": issue.suggestion
                }
                for issue in local_issues[:10]  # Max. 10 Issues
            ]
        }
        print(f"  -> {len(local_issues)} Probleme gefunden")
    except Exception as e:
        print(f"  [FEHLER] {e}")
        results["local_analysis"] = {"error": str(e)}
    
    # 2. Code-Quality-Monitor
    try:
        print("\n[2/3] Code-Quality-Monitor...")
        monitor = CodeQualityMonitor(project_root=str(ROOT))
        quality_report = monitor.analyze_file(str(file_path))
        results["quality_monitor"] = {
            "lines_of_code": quality_report.lines_of_code,
            "complexity_score": quality_report.complexity_score,
            "quality_score": quality_report.quality_score,
            "issues_count": len(quality_report.issues),
            "ai_indicators": quality_report.ai_indicators,
            "issues": quality_report.issues[:10]  # Max. 10 Issues
        }
        print(f"  -> Qualitäts-Score: {quality_report.quality_score:.1f}/100")
        print(f"  -> Komplexität: {quality_report.complexity_score:.1f}")
        print(f"  -> Zeilen: {quality_report.lines_of_code}")
        if quality_report.ai_indicators:
            print(f"  -> AI-Indikatoren: {', '.join(quality_report.ai_indicators)}")
    except Exception as e:
        print(f"  [FEHLER] {e}")
        results["quality_monitor"] = {"error": str(e)}
    
    # 3. KI-Analyse (optional, kostenpflichtig)
    if use_ai:
        try:
            print("\n[3/3] KI-Analyse (OpenAI)...")
            ai_checker = get_ai_code_checker()
            if ai_checker:
                ai_result = ai_checker.analyze_and_improve(file_path)
                ai_analysis = ai_result.get("ai_analysis", {})
                results["ai_analysis"] = {
                    "issues_count": len(ai_analysis.get("issues", [])),
                    "score": ai_analysis.get("score", 0),
                    "summary": ai_analysis.get("summary", ""),
                    "suggestions": ai_analysis.get("suggestions", [])[:5],  # Max. 5
                    "cost_eur": ai_analysis.get("cost_eur", 0),
                    "tokens_used": ai_analysis.get("tokens_used", 0)
                }
                print(f"  -> Score: {ai_analysis.get('score', 0)}/100")
                print(f"  -> Probleme: {len(ai_analysis.get('issues', []))}")
                print(f"  -> Kosten: €{ai_analysis.get('cost_eur', 0):.4f}")
                print(f"  -> Tokens: {ai_analysis.get('tokens_used', 0)}")
            else:
                print("  [INFO] KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
                results["ai_analysis"] = {"error": "KI-Checker nicht verfügbar"}
        except Exception as e:
            print(f"  [FEHLER] {e}")
            results["ai_analysis"] = {"error": str(e)}
    else:
        print("\n[3/3] KI-Analyse übersprungen (--ai für KI-Analyse)")
    
    # Zusammenfassung
    local_count = results["local_analysis"].get("issues_count", 0)
    quality_count = results["quality_monitor"].get("issues_count", 0)
    ai_count = results["ai_analysis"].get("issues_count", 0)
    total_issues = local_count + quality_count + ai_count
    
    quality_score = results["quality_monitor"].get("quality_score", 0)
    ai_score = results["ai_analysis"].get("score", 0)
    
    results["summary"] = {
        "total_issues": total_issues,
        "quality_score": quality_score,
        "ai_score": ai_score,
        "recommendation": _get_recommendation(total_issues, quality_score)
    }
    
    print(f"\n{'='*60}")
    print(f"ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"Gesamt-Probleme: {total_issues}")
    print(f"Qualitäts-Score: {quality_score:.1f}/100")
    if ai_score > 0:
        print(f"AI-Score: {ai_score}/100")
    print(f"Empfehlung: {results['summary']['recommendation']}")
    
    return results


def _get_recommendation(issues: int, score: float) -> str:
    """Gibt Empfehlung basierend auf Ergebnissen."""
    if issues == 0 and score >= 90:
        return "[OK] Code ist in ausgezeichnetem Zustand"
    elif issues < 5 and score >= 80:
        return "[OK] Code ist gut, kleine Verbesserungen moeglich"
    elif issues < 10 and score >= 70:
        return "[WARN] Code ist akzeptabel, aber Verbesserungen empfohlen"
    elif issues < 20:
        return "[WARN] Code benoetigt Refactoring"
    else:
        return "[ERROR] Code benoetigt umfangreiche Ueberarbeitung"


def main():
    """Hauptfunktion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Führt Codechecks durch")
    parser.add_argument(
        "files",
        nargs="*",
        help="Dateien zum Prüfen (leer = wichtige Dateien automatisch)"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="KI-Analyse aktivieren (kostenpflichtig)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="JSON-Output-Datei"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Nur Zusammenfassung anzeigen"
    )
    
    args = parser.parse_args()
    
    # Dateien bestimmen
    if args.files:
        files_to_check = [Path(ROOT / f) for f in args.files]
    else:
        # Wichtige Dateien automatisch
        files_to_check = [
            ROOT / "backend" / "app.py",
            ROOT / "backend" / "services" / "osrm_client.py",
            ROOT / "backend" / "services" / "llm_optimizer.py",
            ROOT / "services" / "code_quality_monitor.py",
            ROOT / "tools" / "make_audit_zip.py",
        ]
        # Nur existierende Dateien
        files_to_check = [f for f in files_to_check if f.exists()]
    
    if not files_to_check:
        print("Keine Dateien zum Prüfen gefunden.")
        return
    
    print(f"\n{'='*60}")
    print(f"CODE-CHECK REPORT")
    print(f"{'='*60}")
    print(f"Dateien: {len(files_to_check)}")
    print(f"KI-Analyse: {'Ja' if args.ai else 'Nein'}")
    print(f"{'='*60}\n")
    
    all_results = []
    total_issues = 0
    total_score = 0
    files_with_issues = 0
    
    for file_path in files_to_check:
        try:
            result = check_file(file_path, use_ai=args.ai)
            all_results.append(result)
            
            total_issues += result["summary"]["total_issues"]
            total_score += result["summary"]["quality_score"]
            if result["summary"]["total_issues"] > 0:
                files_with_issues += 1
        except Exception as e:
            print(f"\n[FEHLER] {file_path}: {e}")
            all_results.append({
                "file": str(file_path.relative_to(ROOT)),
                "error": str(e)
            })
    
    # Gesamt-Zusammenfassung
    avg_score = total_score / len(files_to_check) if files_to_check else 0
    
    print(f"\n\n{'='*60}")
    print(f"GESAMT-ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"Geprüfte Dateien: {len(files_to_check)}")
    print(f"Dateien mit Problemen: {files_with_issues}")
    print(f"Gesamt-Probleme: {total_issues}")
    print(f"Durchschnittlicher Qualitäts-Score: {avg_score:.1f}/100")
    
    if avg_score >= 90:
        print(f"\n[OK] EXZELLENT: Code-Qualitaet ist sehr gut")
    elif avg_score >= 80:
        print(f"\n[OK] GUT: Code-Qualitaet ist gut")
    elif avg_score >= 70:
        print(f"\n[WARN] AKZEPTABEL: Code-Qualitaet ist akzeptabel, Verbesserungen empfohlen")
    else:
        print(f"\n[ERROR] VERBESSERUNGSBEDARF: Code-Qualitaet benoetigt Aufmerksamkeit")
    
    # JSON-Output
    if args.output:
        output_data = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "files_checked": len(files_to_check),
            "total_issues": total_issues,
            "average_score": avg_score,
            "results": all_results
        }
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Report gespeichert: {args.output}")
    
    # Nur Zusammenfassung
    if args.summary:
        print("\n" + "="*60)
        for result in all_results:
            if "error" not in result:
                file = result["file"]
                issues = result["summary"]["total_issues"]
                score = result["summary"]["quality_score"]
                print(f"{file:50} | Issues: {issues:3} | Score: {score:5.1f}")


if __name__ == "__main__":
    main()

