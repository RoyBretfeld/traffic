#!/usr/bin/env python3
"""
Generiert einen detaillierten Verbesserungsreport basierend auf Codecheck-Ergebnissen.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parents[1]


def load_report(report_path: Path) -> Dict[str, Any]:
    """Lädt Codecheck-Report."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_improvements_report(report: Dict[str, Any]) -> str:
    """Generiert Markdown-Report mit Verbesserungsvorschlägen."""
    lines = []
    lines.append("# Code-Qualitäts-Report & Verbesserungsvorschläge\n")
    lines.append(f"**Erstellt:** {report.get('timestamp', 'N/A')}\n")
    lines.append(f"**Geprüfte Dateien:** {report.get('files_checked', 0)}\n")
    lines.append(f"**Gesamt-Probleme:** {report.get('total_issues', 0)}\n")
    lines.append(f"**Durchschnittlicher Score:** {report.get('average_score', 0):.1f}/100\n")
    lines.append("\n---\n")
    
    # Priorisierte Probleme
    lines.append("## 🔴 Kritische Probleme (Priorität 1)\n")
    critical = []
    for result in report.get("results", []):
        if "error" in result:
            continue
        
        file = result["file"]
        local_issues = result.get("local_analysis", {}).get("issues", [])
        quality_issues = result.get("quality_monitor", {}).get("issues", [])
        
        # Kritische Probleme sammeln
        for issue in local_issues:
            if issue.get("severity") == "error":
                critical.append({
                    "file": file,
                    "issue": issue
                })
        
        for issue in quality_issues:
            if issue.get("type") == "function_too_long" and issue.get("severity") == "error":
                critical.append({
                    "file": file,
                    "issue": issue
                })
    
    if critical:
        for item in critical[:10]:  # Max. 10 kritische Probleme
            lines.append(f"### {item['file']}\n")
            issue = item["issue"]
            lines.append(f"- **Zeile {issue.get('line', '?')}**: {issue.get('message', '')}")
            if issue.get("suggestion"):
                lines.append(f"  - 💡 **Vorschlag**: {issue['suggestion']}")
            lines.append("")
    else:
        lines.append("Keine kritischen Probleme gefunden.\n")
    
    # Warnungen
    lines.append("## ⚠️ Warnungen (Priorität 2)\n")
    warnings = []
    for result in report.get("results", []):
        if "error" in result:
            continue
        
        file = result["file"]
        local_issues = result.get("local_analysis", {}).get("issues", [])
        quality_issues = result.get("quality_monitor", {}).get("issues", [])
        
        for issue in local_issues:
            if issue.get("severity") == "warning":
                warnings.append({
                    "file": file,
                    "issue": issue
                })
        
        for issue in quality_issues:
            if issue.get("severity") == "warning":
                warnings.append({
                    "file": file,
                    "issue": issue
                })
    
    if warnings:
        for item in warnings[:15]:  # Max. 15 Warnungen
            lines.append(f"### {item['file']}\n")
            issue = item["issue"]
            lines.append(f"- **Zeile {issue.get('line', '?')}**: {issue.get('message', '')}")
            if issue.get("suggestion"):
                lines.append(f"  - 💡 **Vorschlag**: {issue['suggestion']}")
            lines.append("")
    else:
        lines.append("Keine Warnungen gefunden.\n")
    
    # Datei-spezifische Empfehlungen
    lines.append("## 📋 Datei-spezifische Empfehlungen\n")
    for result in report.get("results", []):
        if "error" in result:
            continue
        
        file = result["file"]
        summary = result.get("summary", {})
        recommendation = summary.get("recommendation", "")
        
        lines.append(f"### {file}\n")
        lines.append(f"- **Empfehlung**: {recommendation}")
        lines.append(f"- **Probleme**: {summary.get('total_issues', 0)}")
        lines.append(f"- **Qualitäts-Score**: {summary.get('quality_score', 0):.1f}/100")
        lines.append("")
    
    # Top-Verbesserungen
    lines.append("## 🎯 Top 10 Verbesserungsvorschläge\n")
    all_suggestions = []
    for result in report.get("results", []):
        if "error" in result:
            continue
        
        file = result["file"]
        local_issues = result.get("local_analysis", {}).get("issues", [])
        
        for issue in local_issues:
            if issue.get("suggestion"):
                all_suggestions.append({
                    "file": file,
                    "line": issue.get("line"),
                    "suggestion": issue["suggestion"],
                    "type": issue.get("type")
                })
    
    for i, suggestion in enumerate(all_suggestions[:10], 1):
        lines.append(f"{i}. **{suggestion['file']}** (Zeile {suggestion.get('line', '?')})")
        lines.append(f"   - {suggestion['suggestion']}")
        lines.append("")
    
    # Nächste Schritte
    lines.append("## 🚀 Nächste Schritte\n")
    lines.append("1. **Kritische Probleme beheben** (Priorität 1)")
    lines.append("2. **Warnungen adressieren** (Priorität 2)")
    lines.append("3. **Refactoring für große Funktionen** (z.B. `create_app` in `backend/app.py`)")
    lines.append("4. **Error-Handling verbessern** (try-except für Datei-Operationen)")
    lines.append("5. **Hardcoded-Pfade durch Konfiguration ersetzen**")
    lines.append("6. **Zeilenlängen reduzieren** (max. 120 Zeichen)")
    lines.append("")
    lines.append("---\n")
    lines.append("**Verwendung:** `python scripts/run_code_checks.py --ai` für KI-Analyse")
    
    return "\n".join(lines)


def main():
    """Hauptfunktion."""
    report_path = ROOT / "reports" / "code_check_report.json"
    
    if not report_path.exists():
        print(f"Report nicht gefunden: {report_path}")
        print("Führe zuerst aus: python scripts/run_code_checks.py --output reports/code_check_report.json")
        return 1
    
    report = load_report(report_path)
    markdown = generate_improvements_report(report)
    
    output_path = ROOT / "reports" / "code_improvements.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Verbesserungsreport erstellt: {output_path}")
    print(f"\nZusammenfassung:")
    print(f"  - Geprüfte Dateien: {report.get('files_checked', 0)}")
    print(f"  - Gesamt-Probleme: {report.get('total_issues', 0)}")
    print(f"  - Durchschnittlicher Score: {report.get('average_score', 0):.1f}/100")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

