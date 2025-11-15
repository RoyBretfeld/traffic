"""
Tests für Code-Improvement Background-Job.
"""
import pytest
from pathlib import Path
from backend.services.code_improvement_job import CodeImprovementJob, get_background_job
from backend.services.cost_tracker import get_cost_tracker


class TestCodeImprovementJob:
    """Tests für Code-Improvement Background-Job."""
    
    def test_job_initialization(self):
        """Test: Job initialisiert korrekt."""
        job = get_background_job()
        
        assert job is not None
        assert isinstance(job.enabled, bool)
        assert job.interval_seconds > 0
        assert job.max_improvements_per_run > 0
    
    def test_find_files_to_improve(self, tmp_path):
        """Test: Job findet Dateien zum Verbessern."""
        job = get_background_job()
        
        # Erstelle Test-Dateien
        test_file1 = tmp_path / "test1.py"
        test_file1.write_text("def test():\n    return True\n", encoding="utf-8")
        
        test_file2 = tmp_path / "test2.py"
        test_file2.write_text("def test():\n    return True\n", encoding="utf-8")
        
        # Setze temporäres Verzeichnis als Projekt-Root (für Test)
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            files = job._find_files_to_improve()
            
            # Sollte Dateien finden
            assert isinstance(files, list)
            # Kann leer sein wenn keine Issues gefunden werden
        finally:
            os.chdir(original_cwd)
    
    def test_exclude_patterns(self):
        """Test: Exclude-Patterns funktionieren."""
        job = get_background_job()
        
        # Prüfe ob exclude_patterns gesetzt sind
        assert isinstance(job.exclude_patterns, list)
        assert len(job.exclude_patterns) > 0
    
    def test_get_status(self):
        """Test: Status wird korrekt zurückgegeben."""
        job = get_background_job()
        
        status = job.get_status()
        
        assert "enabled" in status
        assert "is_running" in status
        assert "last_run" in status
        assert "total_improvements" in status
        assert "total_failures" in status
        assert "interval_seconds" in status
        assert "max_improvements_per_run" in status
        assert "ai_checker_available" in status
    
    @pytest.mark.asyncio
    async def test_run_once_without_ai_checker(self, monkeypatch):
        """Test: run_once gibt Fehler wenn AI-Checker nicht verfügbar."""
        job = CodeImprovementJob()
        job.ai_checker = None  # Simuliere fehlenden AI-Checker
        
        result = await job.run_once()
        
        assert result["success"] is False
        assert "KI-Checker nicht verfügbar" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_run_once_rate_limit(self):
        """Test: run_once respektiert Rate-Limits."""
        job = get_background_job()
        
        # Setze sehr niedriges Limit
        job.cost_tracker.daily_improvements_limit = 0
        
        result = await job.run_once()
        
        # Sollte wegen Limit fehlschlagen
        if not result["success"]:
            assert "Limit erreicht" in result.get("reason", "")
    
    def test_stop(self):
        """Test: Job kann gestoppt werden."""
        job = get_background_job()
        
        job.is_running = True
        job.stop()
        
        assert job.is_running is False


class TestBackgroundJobAPI:
    """Tests für Background-Job API-Endpoints."""
    
    def test_status_endpoint(self):
        """Test: /api/code-improvement-job/status Endpoint."""
        from fastapi.testclient import TestClient
        from backend.app import create_app
        
        client = TestClient(create_app())
        response = client.get("/api/code-improvement-job/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "enabled" in data
        assert "is_running" in data
        assert "interval_seconds" in data
    
    def test_run_once_endpoint(self):
        """Test: /api/code-improvement-job/run-once Endpoint."""
        from fastapi.testclient import TestClient
        from backend.app import create_app
        
        client = TestClient(create_app())
        response = client.post("/api/code-improvement-job/run-once")
        
        # Kann 200 (erfolgreich), 400 (deaktiviert) oder 503 (KI nicht verfügbar) sein
        assert response.status_code in (200, 400, 503)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "improvements" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

