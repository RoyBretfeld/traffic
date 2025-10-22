#!/usr/bin/env python3
"""
Tourplan-Analyse-Test: Testet 5 Tourpläne und zeigt grafische Ergebnisse
"""

import asyncio
import json
import requests
from pathlib import Path
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Konfiguration
API_BASE = "http://localhost:8000"
TOURPLAN_DIR = Path("./tourplaene")

def get_tourplan_files():
    """Holt die ersten 5 CSV-Dateien aus dem Tourplan-Verzeichnis."""
    csv_files = list(TOURPLAN_DIR.glob("*.csv"))
    return sorted(csv_files)[:5]

async def analyze_tourplan(file_path: Path):
    """Analysiert einen einzelnen Tourplan."""
    print(f"\n🔍 Analysiere: {file_path.name}")
    
    # 1) Match-Endpoint aufrufen
    try:
        match_response = requests.get(
            f"{API_BASE}/api/tourplan/match",
            params={"file": str(file_path)}
        )
        match_data = match_response.json()
    except Exception as e:
        print(f"❌ Fehler beim Match: {e}")
        return None
    
    # 2) Audit-Status für diesen Plan
    try:
        audit_response = requests.get(f"{API_BASE}/api/audit/status")
        audit_data = audit_response.json()
    except Exception as e:
        print(f"❌ Fehler beim Audit: {e}")
        audit_data = {}
    
    # 3) Daten zusammenfassen
    analysis = {
        "file": file_path.name,
        "total_rows": match_data.get("rows", 0),
        "ok_count": match_data.get("ok", 0),
        "warn_count": match_data.get("warn", 0),
        "bad_count": match_data.get("bad", 0),
        "coverage_pct": 0,
        "items": match_data.get("items", []),
        "audit_coverage": audit_data.get("coverage_pct", 0),
        "audit_missing": audit_data.get("missing_count", 0)
    }
    
    # Coverage berechnen
    if analysis["total_rows"] > 0:
        analysis["coverage_pct"] = round(
            (analysis["ok_count"] / analysis["total_rows"]) * 100, 2
        )
    
    print(f"   📊 {analysis['total_rows']} Zeilen, {analysis['ok_count']} OK, {analysis['warn_count']} Warn")
    print(f"   📈 Coverage: {analysis['coverage_pct']}%")
    
    return analysis

def categorize_addresses(analyses):
    """Kategorisiert Adressen nach Problemen."""
    categories = {
        "ok": [],
        "missing_geo": [],
        "mojibake": [],
        "incomplete": [],
        "out_of_region": [],
        "special_cases": []
    }
    
    for analysis in analyses:
        for item in analysis["items"]:
            address = item.get("address", "")
            status = item.get("status", "")
            has_geo = item.get("has_geo", False)
            
            if status == "ok" and has_geo:
                categories["ok"].append(address)
            elif status == "warn" and not has_geo:
                # Analysiere warum keine Geo-Daten
                if "??" in address:
                    categories["mojibake"].append(address)
                elif len(address.split(",")) < 2:
                    categories["incomplete"].append(address)
                elif any(city in address for city in ["Wetzlar", "Hamburg", "München"]):
                    categories["out_of_region"].append(address)
                else:
                    categories["missing_geo"].append(address)
            elif status == "bad":
                categories["mojibake"].append(address)
            else:
                categories["special_cases"].append(address)
    
    return categories

def create_visualizations(analyses, categories):
    """Erstellt grafische Darstellungen."""
    
    # 1) Coverage-Vergleich
    plt.figure(figsize=(15, 10))
    
    # Subplot 1: Coverage pro Datei
    plt.subplot(2, 3, 1)
    files = [a["file"] for a in analyses]
    coverages = [a["coverage_pct"] for a in analyses]
    
    bars = plt.bar(range(len(files)), coverages, color='skyblue', alpha=0.7)
    plt.title("Coverage pro Tourplan", fontsize=12, fontweight='bold')
    plt.xlabel("Tourplan")
    plt.ylabel("Coverage (%)")
    plt.xticks(range(len(files)), [f.split(".")[0][:8] for f in files], rotation=45)
    
    # Werte auf Balken anzeigen
    for i, (bar, coverage) in enumerate(zip(bars, coverages)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{coverage}%', ha='center', va='bottom', fontsize=10)
    
    # Subplot 2: Problem-Kategorien
    plt.subplot(2, 3, 2)
    category_counts = {k: len(v) for k, v in categories.items()}
    colors = ['green', 'orange', 'red', 'purple', 'brown', 'gray']
    
    wedges, texts, autotexts = plt.pie(
        category_counts.values(),
        labels=category_counts.keys(),
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )
    plt.title("Problem-Kategorien", fontsize=12, fontweight='bold')
    
    # Subplot 3: Gesamtstatistiken
    plt.subplot(2, 3, 3)
    total_rows = sum(a["total_rows"] for a in analyses)
    total_ok = sum(a["ok_count"] for a in analyses)
    total_warn = sum(a["warn_count"] for a in analyses)
    total_bad = sum(a["bad_count"] for a in analyses)
    
    stats = ["OK", "Warn", "Bad"]
    counts = [total_ok, total_warn, total_bad]
    colors_stats = ['green', 'orange', 'red']
    
    bars = plt.bar(stats, counts, color=colors_stats, alpha=0.7)
    plt.title(f"Gesamtstatistiken\n({total_rows} Zeilen)", fontsize=12, fontweight='bold')
    plt.ylabel("Anzahl")
    
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                str(count), ha='center', va='bottom', fontsize=10)
    
    # Subplot 4: Mojibake-Beispiele
    plt.subplot(2, 3, 4)
    mojibake_examples = categories["mojibake"][:5]  # Erste 5 Beispiele
    if mojibake_examples:
        y_pos = range(len(mojibake_examples))
        plt.barh(y_pos, [1] * len(mojibake_examples), color='red', alpha=0.7)
        plt.yticks(y_pos, [addr[:30] + "..." if len(addr) > 30 else addr for addr in mojibake_examples])
        plt.title("Mojibake-Beispiele", fontsize=12, fontweight='bold')
        plt.xlabel("Problematisch")
    else:
        plt.text(0.5, 0.5, "Keine Mojibake-Probleme!", ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=12, color='green')
        plt.title("Mojibake-Beispiele", fontsize=12, fontweight='bold')
    
    # Subplot 5: Fehlende Geo-Daten
    plt.subplot(2, 3, 5)
    missing_examples = categories["missing_geo"][:5]
    if missing_examples:
        y_pos = range(len(missing_examples))
        plt.barh(y_pos, [1] * len(missing_examples), color='orange', alpha=0.7)
        plt.yticks(y_pos, [addr[:30] + "..." if len(addr) > 30 else addr for addr in missing_examples])
        plt.title("Fehlende Geo-Daten", fontsize=12, fontweight='bold')
        plt.xlabel("Nicht geocodiert")
    else:
        plt.text(0.5, 0.5, "Alle Adressen geocodiert!", ha='center', va='center',
                transform=plt.gca().transAxes, fontsize=12, color='green')
        plt.title("Fehlende Geo-Daten", fontsize=12, fontweight='bold')
    
    # Subplot 6: Zeitstempel
    plt.subplot(2, 3, 6)
    plt.text(0.5, 0.5, f"Analyse erstellt:\n{datetime.now().strftime('%d.%m.%Y %H:%M')}", 
            ha='center', va='center', transform=plt.gca().transAxes, fontsize=10)
    plt.title("Analyse-Info", fontsize=12, fontweight='bold')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig("tourplan_analysis.png", dpi=300, bbox_inches='tight')
    plt.show()

def generate_report(analyses, categories):
    """Generiert einen detaillierten Text-Report."""
    report = []
    report.append("=" * 80)
    report.append("TOURPLAN-ANALYSE-REPORT")
    report.append("=" * 80)
    report.append(f"Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    report.append(f"Analysierte Dateien: {len(analyses)}")
    report.append("")
    
    # Gesamtstatistiken
    total_rows = sum(a["total_rows"] for a in analyses)
    total_ok = sum(a["ok_count"] for a in analyses)
    total_warn = sum(a["warn_count"] for a in analyses)
    total_bad = sum(a["bad_count"] for a in analyses)
    overall_coverage = round((total_ok / total_rows) * 100, 2) if total_rows > 0 else 0
    
    report.append("GESAMTSTATISTIKEN:")
    report.append(f"  📊 Gesamtzeilen: {total_rows}")
    report.append(f"  ✅ OK: {total_ok} ({overall_coverage}%)")
    report.append(f"  ⚠️  Warn: {total_warn}")
    report.append(f"  ❌ Bad: {total_bad}")
    report.append("")
    
    # Einzelne Dateien
    report.append("EINZELNE DATEIEN:")
    for analysis in analyses:
        report.append(f"  📄 {analysis['file']}")
        report.append(f"     Zeilen: {analysis['total_rows']}")
        report.append(f"     OK: {analysis['ok_count']} ({analysis['coverage_pct']}%)")
        report.append(f"     Warn: {analysis['warn_count']}")
        report.append(f"     Bad: {analysis['bad_count']}")
        report.append("")
    
    # Problem-Kategorien
    report.append("PROBLEM-KATEGORIEN:")
    for category, addresses in categories.items():
        if addresses:
            report.append(f"  🔍 {category.upper()}: {len(addresses)} Adressen")
            # Erste 3 Beispiele zeigen
            for addr in addresses[:3]:
                report.append(f"     - {addr}")
            if len(addresses) > 3:
                report.append(f"     ... und {len(addresses) - 3} weitere")
            report.append("")
    
    # Empfehlungen
    report.append("EMPFEHLUNGEN:")
    if categories["mojibake"]:
        report.append("  🔧 Mojibake-Fixes implementieren")
    if categories["missing_geo"]:
        report.append("  🌍 Geocoding für fehlende Adressen durchführen")
    if categories["incomplete"]:
        report.append("  📝 Adress-Vervollständigung verbessern")
    if categories["out_of_region"]:
        report.append("  🗺️  Region-Filter für außerhalb Sachsen/Thüringen")
    
    return "\n".join(report)

async def main():
    """Hauptfunktion."""
    print("🚀 Starte Tourplan-Analyse...")
    
    # 1) Tourplan-Dateien holen
    tourplan_files = get_tourplan_files()
    if not tourplan_files:
        print("❌ Keine CSV-Dateien im Tourplan-Verzeichnis gefunden!")
        return
    
    print(f"📁 Gefunden: {len(tourplan_files)} Tourplan-Dateien")
    for f in tourplan_files:
        print(f"   - {f.name}")
    
    # 2) Analysen durchführen
    analyses = []
    for file_path in tourplan_files:
        analysis = await analyze_tourplan(file_path)
        if analysis:
            analyses.append(analysis)
    
    if not analyses:
        print("❌ Keine Analysen erfolgreich!")
        return
    
    # 3) Kategorisierung
    print("\n📊 Kategorisiere Adressen...")
    categories = categorize_addresses(analyses)
    
    # 4) Report generieren
    print("\n📝 Generiere Report...")
    report = generate_report(analyses, categories)
    
    # Report speichern
    with open("tourplan_analysis_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n" + report)
    
    # 5) Grafische Darstellung
    print("\n📈 Erstelle Grafiken...")
    try:
        create_visualizations(analyses, categories)
        print("✅ Grafiken gespeichert als 'tourplan_analysis.png'")
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Grafiken: {e}")
    
    print("\n🎉 Analyse abgeschlossen!")
    print("📄 Report: tourplan_analysis_report.txt")
    print("📊 Grafiken: tourplan_analysis.png")

if __name__ == "__main__":
    asyncio.run(main())
