#!/usr/bin/env python3
"""
Script zur Analyse von Error-Patterns für KI-Feeds.

Verwendung:
    python scripts/analyze_error_pattern.py <pattern_id>
    python scripts/analyze_error_pattern.py --all
    python scripts/analyze_error_pattern.py --open
"""

import sys
import json
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.services.error_learning_service import get_error_patterns, get_error_events
from sqlalchemy import text
from db.core import ENGINE


def analyze_pattern(pattern_id: int):
    """Analysiert ein einzelnes Error-Pattern."""
    with ENGINE.begin() as conn:
        # Hole Pattern
        pattern = conn.execute(
            text("SELECT * FROM error_patterns WHERE id = :id"),
            {"id": pattern_id}
        ).fetchone()
        
        if not pattern:
            print(f"❌ Pattern {pattern_id} nicht gefunden")
            return
        
        # Hole Events
        events = get_error_events(pattern_id=pattern_id, limit=5)
        
        # Hole Feedback
        feedback = conn.execute(
            text("SELECT * FROM error_feedback WHERE pattern_id = :id ORDER BY created_at DESC"),
            {"id": pattern_id}
        ).fetchall()
        
        print(f"\n{'='*70}")
        print(f"📊 Error-Pattern #{pattern_id}")
        print(f"{'='*70}\n")
        
        print(f"Signatur: {pattern[2]}")
        print(f"Component: {pattern[8]}")
        print(f"Status: {pattern[9]}")
        print(f"Occurrences: {pattern[5]}")
        print(f"First Seen: {pattern[3]}")
        print(f"Last Seen: {pattern[4]}")
        print(f"Primary Endpoint: {pattern[7]}")
        print(f"Last Status Code: {pattern[6]}")
        
        if pattern[10]:  # root_cause_hint
            print(f"\nRoot Cause Hint: {pattern[10]}")
        
        print(f"\n📝 Events ({len(events)} repräsentative):")
        for i, event in enumerate(events[:3], 1):
            print(f"  {i}. {event['timestamp']} - {event['error_type']}: {event['message_short'][:80]}")
        
        if feedback:
            print(f"\n💬 Feedback ({len(feedback)} Einträge):")
            for fb in feedback:
                print(f"  - [{fb[2]}] {fb[4]}: {fb[3][:80]}")
        
        print(f"\n{'='*70}\n")
        
        # Erstelle Cursor-Prompt
        print("🤖 Cursor-Prompt:")
        print("-" * 70)
        print(f"""
Analysiere Error-Pattern #{pattern_id}:

- Pattern: {pattern[2]}
- Component: {pattern[8]}
- Occurrences: {pattern[5]}
- Primary Endpoint: {pattern[7]}
- Status: {pattern[9]}

Bitte:
1. Analysiere die repräsentativen Events
2. Identifiziere die Root Cause
3. Erstelle Fix-Vorschlag
4. Dokumentiere in LESSONS_LOG
""")
        print("-" * 70)


def list_patterns(status: str = None):
    """Listet alle Patterns (optional gefiltert nach Status)."""
    patterns = get_error_patterns(status=status, limit=50)
    
    if not patterns:
        print("Keine Patterns gefunden.")
        return
    
    print(f"\n{'='*70}")
    print(f"📋 Error-Patterns ({len(patterns)} gefunden)")
    if status:
        print(f"Filter: status = {status}")
    print(f"{'='*70}\n")
    
    for p in patterns:
        print(f"#{p['id']:3d} | {p['status']:12s} | {p['occurrences']:4d}x | {p['signature'][:60]}")


def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python scripts/analyze_error_pattern.py <pattern_id>")
        print("  python scripts/analyze_error_pattern.py --all")
        print("  python scripts/analyze_error_pattern.py --open")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "--all":
        list_patterns()
    elif arg == "--open":
        list_patterns(status="open")
    else:
        try:
            pattern_id = int(arg)
            analyze_pattern(pattern_id)
        except ValueError:
            print(f"❌ Ungültige Pattern-ID: {arg}")
            sys.exit(1)


if __name__ == "__main__":
    main()

