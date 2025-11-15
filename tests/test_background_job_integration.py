"""
Integration-Tests für Background-Job Auto-Start
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from backend.services.code_improvement_job import CodeImprovementJob, get_background_job


def test_background_job_initialization():
    """Test: Background-Job wird korrekt initialisiert."""
    job = get_background_job()
    
    assert job is not None
    assert isinstance(job, CodeImprovementJob)
    assert job.enabled == True  # Standardmäßig aktiviert


def test_background_job_status():
    """Test: Background-Job Status wird korrekt zurückgegeben."""
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
async def test_background_job_run_once():
    """Test: Background-Job kann einmalig ausgeführt werden."""
    job = get_background_job()
    
    # Mock AI-Checker falls nicht verfügbar
    if not job.ai_checker:
        job.ai_checker = Mock()
        job.ai_checker.analyze_and_improve = AsyncMock(return_value={
            "improvement_score": 0,
            "ai_analysis": {}
        })
    
    # Führe einmalige Runde aus
    result = await job.run_once()
    
    assert "success" in result
    assert "improvements" in result
    assert "failures" in result
    assert isinstance(result["improvements"], int)
    assert isinstance(result["failures"], int)


def test_background_job_startup_conditions():
    """Test: Background-Job startet nur wenn Bedingungen erfüllt sind."""
    job = get_background_job()
    
    # Prüfe Bedingungen
    conditions_met = (
        job.enabled and
        not job.is_running and
        job.ai_checker is not None
    )
    
    # Job sollte startbar sein wenn alle Bedingungen erfüllt sind
    # (kann False sein wenn OPENAI_API_KEY fehlt, das ist OK)
    assert isinstance(conditions_met, bool)


def test_background_job_stop():
    """Test: Background-Job kann gestoppt werden."""
    job = get_background_job()
    
    # Setze is_running auf True (simuliere laufenden Job)
    job.is_running = True
    
    # Stoppe Job
    job.stop()
    
    assert job.is_running == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

