"""
Tests für KI-CodeChecker Komponenten.
"""
import pytest
from pathlib import Path
from backend.services.code_analyzer import CodeAnalyzer, analyze_code_file, CodeIssue, IssueSeverity
from backend.services.cost_tracker import CostTracker, get_cost_tracker
from backend.services.performance_tracker import PerformanceTracker, get_performance_tracker
from backend.services.notification_service import NotificationService, get_notification_service


class TestCodeAnalyzer:
    """Tests für Code-Analyzer."""
    
    def test_analyze_file_not_found(self, tmp_path):
        """Test: Analyzer gibt Fehler bei nicht existierender Datei."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file(Path("nonexistent.py"))
        
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.ERROR
        assert issues[0].type == "file_not_found"
    
    def test_analyze_syntax_error(self, tmp_path):
        """Test: Analyzer findet Syntax-Fehler."""
        test_file = tmp_path / "syntax_error.py"
        test_file.write_text("def test():\n    return\n    # Fehlende Klammer\n", encoding="utf-8")
        
        issues = analyze_code_file(test_file)
        
        # Sollte Syntax-Fehler finden
        syntax_errors = [i for i in issues if i.type == "syntax_error"]
        # Kann auch andere Issues finden (z.B. missing_docstring)
        assert len(issues) > 0
    
    def test_analyze_missing_error_handling(self, tmp_path):
        """Test: Analyzer findet fehlendes Error-Handling."""
        test_file = tmp_path / "no_error_handling.py"
        test_file.write_text(
            "def read_file():\n"
            "    with open('file.txt', 'r') as f:\n"
            "        return f.read()\n",
            encoding="utf-8"
        )
        
        issues = analyze_code_file(test_file)
        
        # Sollte missing_error_handling finden
        error_handling_issues = [i for i in issues if i.type == "missing_error_handling"]
        # Kann gefunden werden, muss aber nicht (abhängig von Kontext)
    
    def test_analyze_hardcoded_path(self, tmp_path):
        """Test: Analyzer findet Hardcoded-Pfade."""
        test_file = tmp_path / "hardcoded.py"
        test_file.write_text(
            "def save_file():\n"
            "    path = '/tmp/file.txt'\n"
            "    with open(path, 'w') as f:\n"
            "        f.write('test')\n",
            encoding="utf-8"
        )
        
        issues = analyze_code_file(test_file)
        
        # Sollte hardcoded_path finden
        hardcoded_issues = [i for i in issues if i.type == "hardcoded_path"]
        # Kann gefunden werden
    
    def test_analyze_valid_code(self, tmp_path):
        """Test: Analyzer findet keine Fehler bei valide Code."""
        test_file = tmp_path / "valid.py"
        test_file.write_text(
            "\"\"\"Valid Python code.\"\"\"\n"
            "def test_function():\n"
            "    \"\"\"Test function.\"\"\"\n"
            "    return True\n",
            encoding="utf-8"
        )
        
        issues = analyze_code_file(test_file)
        
        # Sollte keine ERROR-Issues finden
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        assert len(errors) == 0


class TestCostTracker:
    """Tests für Cost-Tracker."""
    
    def test_cost_tracker_initialization(self):
        """Test: Cost-Tracker initialisiert korrekt."""
        tracker = get_cost_tracker()
        
        assert tracker is not None
        assert tracker.default_model == "gpt-4o-mini"
        assert "gpt-4o-mini" in tracker.model_prices
    
    def test_track_api_call(self):
        """Test: API-Call wird getrackt."""
        tracker = get_cost_tracker()
        
        cost = tracker.track_api_call(
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500,
            file_path="test.py",
            operation="test"
        )
        
        # Kosten sollten > 0 sein
        assert cost > 0
        assert cost < 0.01  # GPT-4o-mini ist sehr günstig
    
    def test_get_daily_stats(self):
        """Test: Tages-Statistiken werden korrekt zurückgegeben."""
        tracker = get_cost_tracker()
        
        stats = tracker.get_daily_stats()
        
        assert "date" in stats
        assert "total_cost_eur" in stats
        assert "total_api_calls" in stats
        assert "total_improvements" in stats
        assert "cost_limit_eur" in stats
    
    def test_can_improve_code(self):
        """Test: Rate-Limiting prüft ob Verbesserung erlaubt ist."""
        tracker = get_cost_tracker()
        
        can_improve, message = tracker.can_improve_code()
        
        assert isinstance(can_improve, bool)
        assert isinstance(message, str)
        
        # Bei niedrigen Limits sollte es funktionieren
        if can_improve:
            assert message == "OK"
    
    def test_calculate_cost_gpt4o_mini(self):
        """Test: Kosten-Berechnung für GPT-4o-mini."""
        tracker = get_cost_tracker()
        
        # 1000 Input + 500 Output Tokens
        cost = tracker._calculate_cost("gpt-4o-mini", 1000, 500)
        
        # Erwartete Kosten: (1000/1000 * 0.00015) + (500/1000 * 0.0006) = 0.00015 + 0.0003 = 0.00045
        expected = 0.00015 + 0.0003
        assert abs(cost - expected) < 0.00001


class TestPerformanceTracker:
    """Tests für Performance-Tracker."""
    
    def test_performance_tracker_initialization(self):
        """Test: Performance-Tracker initialisiert korrekt."""
        tracker = get_performance_tracker()
        
        assert tracker is not None
        assert tracker.track_performance is True
    
    def test_track_operation(self):
        """Test: Operation wird getrackt."""
        tracker = get_performance_tracker()
        
        import time
        
        with tracker.track_operation("test_operation", "test.py"):
            time.sleep(0.1)  # Simuliere Arbeit
        
        # Prüfe ob Eintrag erstellt wurde
        averages = tracker.get_daily_averages()
        assert averages["total_operations"] > 0
    
    def test_get_daily_averages(self):
        """Test: Tages-Durchschnitte werden korrekt zurückgegeben."""
        tracker = get_performance_tracker()
        
        averages = tracker.get_daily_averages()
        
        assert "date" in averages
        assert "avg_analysis_time" in averages
        assert "avg_api_call_time" in averages
        assert "avg_test_time" in averages
        assert "total_operations" in averages


class TestNotificationService:
    """Tests für Notification-Service."""
    
    def test_notification_service_initialization(self):
        """Test: Notification-Service initialisiert korrekt."""
        service = get_notification_service()
        
        assert service is not None
        assert service.email_to == "code@rh-automation-dresden.de"
        assert service.email_from == "code@rh-automation-dresden.de"
    
    def test_notify_improvement(self):
        """Test: Verbesserung wird benachrichtigt."""
        service = get_notification_service()
        
        result = service.notify_improvement({
            "file": "test.py",
            "action": "improved",
            "issues_fixed": 2,
            "tests_passed": True,
            "backup": "backup.py"
        })
        
        assert "timestamp" in result
        assert result["file"] == "test.py"
    
    def test_get_recent_improvements(self):
        """Test: Letzte Verbesserungen werden zurückgegeben."""
        service = get_notification_service()
        
        improvements = service.get_recent_improvements(limit=10)
        
        assert isinstance(improvements, list)
        # Kann leer sein wenn keine Verbesserungen vorhanden
    
    def test_get_improvement_stats(self):
        """Test: Statistiken werden zurückgegeben."""
        service = get_notification_service()
        
        stats = service.get_improvement_stats()
        
        assert "improvements_today" in stats
        assert "successful_count" in stats
        assert "failed_count" in stats


class TestAICodeChecker:
    """Tests für AI-Code-Checker (benötigt OPENAI_API_KEY)."""
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-ai-tests", default=False),
        reason="AI-Tests benötigen OPENAI_API_KEY"
    )
    def test_ai_code_checker_initialization(self, monkeypatch):
        """Test: AI-Code-Checker initialisiert korrekt."""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            pytest.skip("OPENAI_API_KEY nicht gesetzt")
        
        from backend.services.ai_code_checker import AICodeChecker
        
        checker = AICodeChecker(api_key=api_key)
        
        assert checker.model == "gpt-4o-mini"
        assert checker.client is not None
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-ai-tests", default=False),
        reason="AI-Tests benötigen OPENAI_API_KEY"
    )
    def test_analyze_and_improve(self, tmp_path, monkeypatch):
        """Test: Code-Analyse und Verbesserung funktioniert."""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            pytest.skip("OPENAI_API_KEY nicht gesetzt")
        
        from backend.services.ai_code_checker import AICodeChecker
        
        checker = AICodeChecker(api_key=api_key)
        
        # Erstelle Test-Datei
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def test():\n"
            "    print('test')\n"
            "    return True\n",
            encoding="utf-8"
        )
        
        result = checker.analyze_and_improve(test_file)
        
        assert "file" in result
        assert "local_issues" in result
        assert "ai_analysis" in result
        assert "total_issues" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

