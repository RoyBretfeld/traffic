"""
API-Endpoints für KI-CodeChecker.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Optional
from backend.services.ai_code_checker import get_ai_code_checker
from backend.services.safety_manager import SafetyManager
from backend.services.code_analyzer import analyze_code_file

router = APIRouter()

@router.post("/api/code-checker/analyze")
async def analyze_code(
    file_path: str = Query(..., description="Pfad zur Python-Datei")
):
    """
    Analysiert eine Code-Datei.
    """
    file = Path(file_path)
    
    if not file.exists():
        raise HTTPException(status_code=404, detail=f"Datei nicht gefunden: {file_path}")
    
    if file.suffix != '.py':
        raise HTTPException(status_code=400, detail="Nur Python-Dateien werden unterstützt")
    
    # Lokale Analyse
    local_issues = analyze_code_file(file)
    
    # Konvertiere CodeIssue zu Dict
    local_issues_dict = [
        {
            "type": issue.type,
            "severity": issue.severity.value,
            "message": issue.message,
            "line": issue.line,
            "column": issue.column,
            "file_path": issue.file_path,
            "code_snippet": issue.code_snippet,
            "suggestion": issue.suggestion
        }
        for issue in local_issues
    ]
    
    # KI-Analyse (falls verfügbar)
    ai_checker = get_ai_code_checker()
    if ai_checker:
        try:
            ai_result = ai_checker.analyze_and_improve(file)
            return JSONResponse({
                "file": str(file),
                "local_issues": local_issues_dict,
                "ai_analysis": ai_result.get("ai_analysis", {}),
                "total_issues": len(local_issues) + len(ai_result.get("ai_analysis", {}).get("issues", [])),
                "improvement_score": ai_result.get("improvement_score", 0)
            })
        except Exception as e:
            return JSONResponse({
                "file": str(file),
                "local_issues": local_issues_dict,
                "ai_analysis": {"error": str(e)},
                "total_issues": len(local_issues),
                "improvement_score": 0
            })
    else:
        # Nur lokale Analyse
        return JSONResponse({
            "file": str(file),
            "local_issues": local_issues_dict,
            "ai_analysis": {"error": "KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)"},
            "total_issues": len(local_issues),
            "improvement_score": 0
        })

@router.get("/api/code-checker/learned-patterns")
async def get_learned_patterns():
    """
    Gibt die gelernten Fehlermuster zurück (aus ERROR_CATALOG + LESSONS_LOG).
    """
    ai_checker = get_ai_code_checker()
    
    if not ai_checker:
        return JSONResponse({
            "error": "KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)",
            "patterns": {}
        })
    
    patterns = ai_checker.learned_patterns
    
    return JSONResponse({
        "loaded": patterns.get("loaded", False),
        "last_reload": ai_checker.last_reload.isoformat() if hasattr(ai_checker, 'last_reload') else None,
        "error_catalog_length": len(patterns.get("error_catalog", "")),
        "lessons_log_length": len(patterns.get("lessons_log", "")),
        "lessons_preview": patterns.get("lessons_log", "")[:500] + "..." if len(patterns.get("lessons_log", "")) > 500 else patterns.get("lessons_log", ""),
        "patterns_summary": {
            "schema_drift": "DB-Spalten prüfen, Migration-Scripts",
            "syntax_errors": "String-Quotes, Klammern",
            "defensive_programming": "Null-Checks, Type-Checks, Array-Checks",
            "memory_leaks": "Event Listener entfernen",
            "api_contract_breaks": "Backend ↔ Frontend Kontrakt",
            "osrm_timeout": "Fallback auf Haversine",
            "browser_compat": "Feature Detection"
        }
    })

@router.post("/api/code-checker/reload-patterns")
async def reload_patterns():
    """
    Lädt Fehlerhistorie manuell neu (ohne auf 6h-Timer zu warten).
    """
    ai_checker = get_ai_code_checker()
    
    if not ai_checker:
        raise HTTPException(status_code=503, detail="KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
    
    result = await ai_checker.reload_patterns()
    
    if result.get("success"):
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Reload fehlgeschlagen"))

@router.post("/api/code-checker/add-lesson")
async def add_lesson(
    title: str = Query(..., description="Kurzbeschreibung des Fehlers"),
    category: str = Query(..., description="Backend/Frontend/DB/Infrastruktur"),
    severity: str = Query(..., description="🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW / 🟣 ENHANCEMENT"),
    symptom: str = Query(..., description="Was wurde beobachtet?"),
    cause: str = Query(..., description="Root Cause"),
    fix: str = Query(..., description="Wie wurde es behoben?"),
    lessons: str = Query(..., description="Lektionen (komma-separiert)"),
    files: Optional[str] = Query(None, description="Betroffene Dateien (komma-separiert)")
):
    """
    Trägt einen neuen Fehler automatisch in LESSONS_LOG.md ein (Self-Learning).
    """
    ai_checker = get_ai_code_checker()
    
    if not ai_checker:
        raise HTTPException(status_code=503, detail="KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
    
    # Parse lessons und files
    lessons_list = [l.strip() for l in lessons.split(',') if l.strip()]
    files_list = [f.strip() for f in files.split(',') if f.strip()] if files else None
    
    if not lessons_list:
        raise HTTPException(status_code=400, detail="Mindestens eine Lektion erforderlich")
    
    result = ai_checker.add_lesson_to_log(
        title=title,
        category=category,
        severity=severity,
        symptom=symptom,
        cause=cause,
        fix=fix,
        lessons=lessons_list,
        files=files_list
    )
    
    if result.get("success"):
        return JSONResponse({
            **result,
            "message": f"Lektion '{title}' erfolgreich in LESSONS_LOG.md eingetragen und Fehlerhistorie neu geladen"
        })
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Eintrag fehlgeschlagen"))

@router.get("/api/code-checker/status")
async def get_checker_status():
    """
    Gibt Status-Informationen zurück (letztes Reload, nächstes Reload, etc.).
    """
    ai_checker = get_ai_code_checker()
    
    if not ai_checker:
        return JSONResponse({
            "available": False,
            "error": "KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)"
        })
    
    from datetime import datetime, timedelta
    
    last_reload = ai_checker.last_reload if hasattr(ai_checker, 'last_reload') else None
    next_reload = last_reload + timedelta(hours=6) if last_reload else None
    
    return JSONResponse({
        "available": True,
        "last_reload": last_reload.isoformat() if last_reload else None,
        "next_reload": next_reload.isoformat() if next_reload else None,
        "patterns_loaded": ai_checker.learned_patterns.get("loaded", False),
        "auto_reload_enabled": True,
        "reload_interval_hours": 6,
        "patterns_count": {
            "error_catalog_chars": len(ai_checker.learned_patterns.get("error_catalog", "")),
            "lessons_log_chars": len(ai_checker.learned_patterns.get("lessons_log", ""))
        }
    })

@router.post("/api/code-checker/improve")
async def improve_code(
    file_path: str = Query(..., description="Pfad zur Python-Datei"),
    auto_apply: bool = Query(False, description="Verbesserung automatisch anwenden")
):
    """
    Verbessert Code mit KI.
    """
    file = Path(file_path)
    
    if not file.exists():
        raise HTTPException(status_code=404, detail=f"Datei nicht gefunden: {file_path}")
    
    if file.suffix != '.py':
        raise HTTPException(status_code=400, detail="Nur Python-Dateien werden unterstützt")
    
    ai_checker = get_ai_code_checker()
    if not ai_checker:
        raise HTTPException(status_code=503, detail="KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
    
    # 1. Analysiere Code
    analysis_result = ai_checker.analyze_and_improve(file)
    ai_analysis = analysis_result.get("ai_analysis", {})
    
    if "error" in ai_analysis:
        raise HTTPException(status_code=500, detail=ai_analysis["error"])
    
    issues = ai_analysis.get("issues", [])
    if not issues:
        return JSONResponse({
            "success": True,
            "message": "Keine Probleme gefunden",
            "improved_code": None,
            "diff": None
        })
    
    # 2. Generiere verbesserten Code
    improvement_result = ai_checker.generate_improved_code(file, issues)
    
    if "error" in improvement_result:
        raise HTTPException(status_code=500, detail=improvement_result["error"])
    
    improved_code = improvement_result.get("improved_code")
    if not improved_code:
        raise HTTPException(status_code=500, detail="Kein verbesserter Code generiert")
    
    # 3. Optional: Automatisch anwenden
    if auto_apply:
        safety_manager = SafetyManager()
        apply_result = safety_manager.apply_with_safety_check(
            file,
            improved_code,
            issues_fixed=len(issues)
        )
        
        return JSONResponse({
            "success": apply_result.get("success", False),
            "applied": True,
            "backup": apply_result.get("backup"),
            "tests_passed": apply_result.get("tests_passed", False),
            "issues_fixed": len(issues),
            "improved_code": improved_code,
            "diff": improvement_result.get("diff"),
            "error": apply_result.get("error")
        })
    else:
        # Nur Vorschau
        return JSONResponse({
            "success": True,
            "applied": False,
            "issues_fixed": len(issues),
            "improved_code": improved_code,
            "diff": improvement_result.get("diff"),
            "changes": improvement_result.get("changes", []),
            "summary": improvement_result.get("summary", "")
        })

@router.get("/api/code-checker/status")
async def get_checker_status():
    """
    Gibt Status des Code-Checkers zurück.
    """
    ai_checker = get_ai_code_checker()
    
    return JSONResponse({
        "available": ai_checker is not None,
        "model": ai_checker.model if ai_checker else None,
        "message": "KI-Checker verfügbar" if ai_checker else "KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)"
    })

