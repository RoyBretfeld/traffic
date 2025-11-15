"""
Startet den Code-Improvement Background-Job als eigenständiges Script.
Kann auch als Service/Systemd-Unit laufen.
"""
import asyncio
import os
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.services.code_improvement_job import get_background_job

async def main():
    """Hauptfunktion für Background-Job."""
    print("=" * 70)
    print("Code-Improvement Background-Job")
    print("=" * 70)
    print(f"Projekt-Root: {project_root}")
    print(f"OPENAI_API_KEY: {'Gesetzt' if os.getenv('OPENAI_API_KEY') else 'NICHT GESETZT'}")
    print("=" * 70)
    
    job = get_background_job()
    
    if not job.enabled:
        print("⚠️  Background-Job ist deaktiviert (ki_codechecker:background_job:enabled = false)")
        return
    
    if not job.ai_checker:
        print("❌ KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
        print("   Setze OPENAI_API_KEY Umgebungsvariable")
        return
    
    print(f"✅ Background-Job wird gestartet...")
    print(f"   Intervall: {job.interval_seconds}s ({job.interval_seconds/60:.1f} Minuten)")
    print(f"   Max. Verbesserungen pro Runde: {job.max_improvements_per_run}")
    print(f"   Beende mit: Ctrl+C")
    print("=" * 70)
    
    try:
        await job.run_continuously()
    except KeyboardInterrupt:
        print("\n⚠️  Beende Background-Job...")
        job.stop()
        print("✅ Background-Job beendet")

if __name__ == "__main__":
    asyncio.run(main())

