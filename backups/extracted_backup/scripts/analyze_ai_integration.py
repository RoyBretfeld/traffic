#!/usr/bin/env python3
"""
Analysiert die AI/LLM-Integration im Projekt:
- Wo wird AI wirklich verwendet?
- Wo ist es nur Python-Code?
- Ist die AI-Integration sinnvoll?
"""

import re
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

# AI-bezogene Dateien
AI_FILES = [
    "services/llm_optimizer.py",
    "services/llm_address_helper.py",
]

# Workflow-Dateien
WORKFLOW_FILES = [
    "routes/workflow_api.py",
    "services/workflow_engine.py",
]

def analyze_ai_file(file_path: Path):
    """Analysiert eine AI-Datei auf echte AI-Nutzung"""
    if not file_path.exists():
        return None
    
    content = file_path.read_text(encoding='utf-8')
    
    # Prüfe auf echte AI-API-Calls
    has_openai = bool(re.search(r'OpenAI|AzureOpenAI|openai\.', content, re.I))
    has_api_calls = bool(re.search(r'client\.(chat|completions|create)', content, re.I))
    has_real_llm = has_openai and has_api_calls
    
    # Prüfe auf nur Python-Logik
    has_only_python = not has_openai and bool(re.search(r'def |class ', content))
    
    # Prüfe auf echte Prompt-Generierung
    has_prompts = bool(re.search(r'prompt|system.*message|user.*message', content, re.I))
    
    # Prüfe auf Konfiguration
    has_config = bool(re.search(r'api_key|AZURE_OPENAI|OPENAI_API', content, re.I))
    
    return {
        "file": file_path.name,
        "path": str(file_path.relative_to(PROJECT_ROOT)),
        "has_real_llm": has_real_llm,
        "has_openai": has_openai,
        "has_api_calls": has_api_calls,
        "has_prompts": has_prompts,
        "has_config": has_config,
        "has_only_python": has_only_python,
        "size": len(content),
        "lines": len(content.splitlines())
    }

def check_workflow_integration(file_path: Path):
    """Prüft ob AI wirklich in Workflow integriert ist"""
    if not file_path.exists():
        return None
    
    content = file_path.read_text(encoding='utf-8')
    
    # Prüfe auf Import
    has_import = bool(re.search(r'from.*llm|import.*llm', content, re.I))
    
    # Prüfe auf Verwendung
    has_usage = bool(re.search(r'LLM|llm_optimizer|llm_address', content, re.I))
    
    # Prüfe auf tatsächlichen Aufruf
    has_call = bool(re.search(r'\.optimize|\.suggest|\.correct', content))
    
    return {
        "file": file_path.name,
        "has_import": has_import,
        "has_usage": has_usage,
        "has_call": has_call,
        "integrated": has_import and has_usage and has_call
    }

def main():
    print("=" * 70)
    print("AI/LLM Integration Analyse")
    print("=" * 70)
    
    # Analysiere AI-Dateien
    print("\n1. AI-Dateien Analyse:")
    print("-" * 70)
    
    ai_results = []
    for rel_path in AI_FILES:
        file_path = PROJECT_ROOT / rel_path
        result = analyze_ai_file(file_path)
        if result:
            ai_results.append(result)
            print(f"\n[{result['file']}]")
            print(f"  Pfad: {result['path']}")
            print(f"  Echte LLM-API: {'JA' if result['has_real_llm'] else 'NEIN'}")
            print(f"  OpenAI/Azure: {'JA' if result['has_openai'] else 'NEIN'}")
            print(f"  API-Calls: {'JA' if result['has_api_calls'] else 'NEIN'}")
            print(f"  Prompts: {'JA' if result['has_prompts'] else 'NEIN'}")
            print(f"  Konfiguration: {'JA' if result['has_config'] else 'NEIN'}")
            print(f"  Nur Python: {'JA' if result['has_only_python'] else 'NEIN'}")
    
    # Prüfe Workflow-Integration
    print("\n2. Workflow-Integration:")
    print("-" * 70)
    
    workflow_results = []
    for rel_path in WORKFLOW_FILES:
        file_path = PROJECT_ROOT / rel_path
        result = check_workflow_integration(file_path)
        if result:
            workflow_results.append(result)
            print(f"\n[{result['file']}]")
            print(f"  Import vorhanden: {'JA' if result['has_import'] else 'NEIN'}")
            print(f"  Verwendung vorhanden: {'JA' if result['has_usage'] else 'NEIN'}")
            print(f"  Tatsächlicher Aufruf: {'JA' if result['has_call'] else 'NEIN'}")
            print(f"  Vollständig integriert: {'JA' if result['integrated'] else 'NEIN'}")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("Zusammenfassung & Empfehlung:")
    print("=" * 70)
    
    real_ai_count = sum(1 for r in ai_results if r['has_real_llm'])
    integrated_count = sum(1 for r in workflow_results if r['integrated'])
    
    print(f"\nEchte AI-Integrationen: {real_ai_count}/{len(ai_results)}")
    print(f"In Workflow integriert: {integrated_count}/{len(workflow_results)}")
    
    if real_ai_count == 0:
        print("\n[WARNUNG] Keine echte AI-API-Integration gefunden!")
        print("  -> AI-Dateien enthalten möglicherweise nur Python-Logik")
        print("  -> Empfehlung: Entweder echte AI integrieren ODER auf reinen Python-Code umstellen")
    elif integrated_count == 0:
        print("\n[WARNUNG] AI ist nicht im Workflow integriert!")
        print("  -> AI-Code existiert, wird aber nicht verwendet")
        print("  -> Empfehlung: Entweder integrieren ODER entfernen")
    else:
        print("\n[OK] AI ist integriert und wird verwendet")
        print("  -> Weiterhin: Code härten für alle Eventualitäten")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

