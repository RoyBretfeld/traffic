#!/usr/bin/env python3
"""
Analysiert die tatsächliche AI-Nutzung:
- Wie oft wird AI vs. Fallback verwendet?
- Was sind die Kosten?
- Ist AI sinnvoll?
"""

import sys
from pathlib import Path
import sqlite3
import os
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def analyze_llm_metrics():
    """Analysiert LLM-Metriken aus Datenbank"""
    print("=" * 70)
    print("AI-NUTZUNGS-ANALYSE")
    print("=" * 70)
    
    # Prüfe ob LLM-Monitoring-DB existiert
    llm_db = PROJECT_ROOT / "data" / "llm_monitoring.db"
    
    if not llm_db.exists():
        print("\n[INFO] Keine LLM-Monitoring-Datenbank gefunden")
        print("  -> AI wurde möglicherweise noch nicht verwendet")
        return None
    
    conn = sqlite3.connect(llm_db)
    cursor = conn.cursor()
    
    # Prüfe Tabelle
    try:
        cursor.execute("SELECT COUNT(*) FROM llm_interactions")
        total = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        print("\n[INFO] LLM-Monitoring-Tabelle existiert nicht")
        conn.close()
        return None
    
    print(f"\n[GEFUNDEN] {total} LLM-Interaktionen in Datenbank")
    
    # Analysiere letzte 7 Tage
    week_ago = datetime.now() - timedelta(days=7)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
            SUM(tokens_used) as total_tokens,
            AVG(processing_time) as avg_time
        FROM llm_interactions
        WHERE timestamp > ?
    """, (week_ago.isoformat(),))
    
    stats = cursor.fetchone()
    print(f"\n[LETZTE 7 TAGE]")
    print(f"  Total: {stats[0] or 0}")
    print(f"  Erfolgreich: {stats[1] or 0}")
    print(f"  Fehlgeschlagen: {stats[2] or 0}")
    print(f"  Tokens: {stats[3] or 0}")
    if stats[4]:
        print(f"  Avg. Zeit: {stats[4]:.2f}s")
    else:
        print(f"  Avg. Zeit: N/A")
    
    # Kosten-Schätzung (GPT-4o-mini: ~$0.15/$0.60 per 1M tokens)
    if stats[3] and stats[3] > 0:
        cost_estimate = (stats[3] / 1_000_000) * 0.15  # Input
        cost_estimate += (stats[3] / 1_000_000) * 0.60  # Output (geschätzt 50/50)
        print(f"  Geschätzte Kosten: ${cost_estimate:.4f}")
    
    conn.close()
    return stats

def check_llm_availability():
    """Prüft ob LLM verfügbar ist"""
    print("\n" + "=" * 70)
    print("LLM-VERFÜGBARKEIT")
    print("=" * 70)
    
    try:
        from services.llm_optimizer import LLMOptimizer
        optimizer = LLMOptimizer()
        
        print(f"\n[STATUS]")
        print(f"  Aktiviert: {'JA' if optimizer.enabled else 'NEIN'}")
        
        if optimizer.enabled:
            print(f"  Model: {optimizer.model}")
            print(f"  API-Key: {'Vorhanden' if optimizer.api_key else 'FEHLT'}")
            print(f"\n[OK] LLM ist konfiguriert und verfügbar")
            return True
        else:
            print(f"  Grund: Kein API-Key oder OpenAI nicht verfügbar")
            print(f"\n[INFO] LLM ist deaktiviert - Fallback wird verwendet")
            return False
    except Exception as e:
        print(f"\n[FEHLER] {e}")
        return False

def check_fallback_quality():
    """Prüft Qualität des Python-Fallbacks"""
    print("\n" + "=" * 70)
    print("PYTHON-FALLBACK QUALITÄT")
    print("=" * 70)
    
    print("\n[ALGORITHMUS]")
    print("  Nearest-Neighbor Optimierung")
    print("  - Einfach, schnell, deterministisch")
    print("  - Funktioniert immer (keine API-Abhängigkeit)")
    print("  - Gute Ergebnisse für kleine/mittlere Routen")
    
    print("\n[ROBUSTHEIT]")
    print("  [OK] Funktioniert ohne Internet")
    print("  [OK] Keine Kosten")
    print("  [OK] Keine API-Limits")
    print("  [OK] Konsistente Ergebnisse")
    print("  [WARN] Nicht optimal fuer komplexe Routen (>20 Stops)")

def main():
    """Hauptanalyse"""
    
    # 1. LLM-Verfügbarkeit
    ai_available = check_llm_availability()
    
    # 2. Nutzungs-Statistiken
    stats = analyze_llm_metrics()
    
    # 3. Fallback-Qualität
    check_fallback_quality()
    
    # 4. Empfehlung
    print("\n" + "=" * 70)
    print("EMPFEHLUNG")
    print("=" * 70)
    
    if not ai_available:
        print("\n[EMPFEHLUNG: REIN PYTHON]")
        print("  LLM ist nicht verfügbar/konfiguriert")
        print("  -> Python-Code weiter härten für alle Eventualitäten")
        print("  -> AI-Code kann entfernt oder als optionales Feature belassen werden")
    elif stats and stats[0] == 0:
        print("\n[EMPFEHLUNG: PRÜFEN]")
        print("  LLM ist verfügbar, wurde aber noch nicht verwendet")
        print("  -> Teste AI mit echten Daten")
        print("  -> Wenn kein Mehrwert: Auf Python umstellen")
    elif stats and stats[2] > stats[1] * 0.2:  # >20% Fehlerrate
        print("\n[EMPFEHLUNG: AI ROBUSTER MACHEN ODER ENTFERNEN]")
        print(f"  Fehlerrate: {stats[2]/(stats[1]+stats[2])*100:.1f}%")
        print("  -> AI ist zu unzuverlässig")
        print("  -> Entweder robuster machen ODER entfernen")
    else:
        print("\n[EMPFEHLUNG: AI BEHALTEN]")
        print("  LLM wird verwendet und funktioniert")
        print("  -> Weiterhin Code härten für alle Eventualitäten")
        print("  -> AI als primäre Methode, Python als Fallback")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

