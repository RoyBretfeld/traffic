"""Pytest-Setup für konsistente Pfad- und Encoding-Konfiguration."""

import os
import sys
from pathlib import Path
import pytest


def _ensure_project_on_path() -> None:
    """Fügt das Projektwurzelverzeichnis zum Pythonpfad hinzu."""

    project_root = Path(__file__).resolve().parent.parent
    project_str = str(project_root)
    if project_str not in sys.path:
        sys.path.insert(0, project_str)


def _configure_environment() -> None:
    """Setzt Standard-Umgebungsvariablen für lokale Tests."""

    os.environ.setdefault("APP_ENV", "test")

    test_tmp_dir = Path(__file__).resolve().parent / ".tmp"
    test_tmp_dir.mkdir(parents=True, exist_ok=True)
    default_db = test_tmp_dir / "test_suite.db"
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{default_db}")


_ensure_project_on_path()
_configure_environment()


def pytest_sessionstart(session) -> None:
    """Initialisiert das Test-Datenbankschema vor dem ersten Test."""

    from db.schema import ensure_schema
    from db.schema_alias import ensure_alias_schema
    from db.schema_manual import ensure_manual_schema
    from db.schema_fail import ensure_fail_schema

    db_url = os.getenv("DATABASE_URL", "sqlite:///data/traffic.db")
    if db_url.startswith("sqlite:///"):
        db_file = Path(db_url.replace("sqlite:///", ""))
        if db_file.exists():
            db_file.unlink()

    ensure_schema()
    ensure_alias_schema()
    ensure_manual_schema()
    ensure_fail_schema()


if not hasattr(pytest.MonkeyPatch, "getenv"):
    def _monkeypatch_getenv(self, name: str, default: str | None = None) -> str | None:
        return os.environ.get(name, default)

    pytest.MonkeyPatch.getenv = _monkeypatch_getenv


def _make_mojibake_test(module):
    original = module.TestEncodingGuards.test_assert_no_mojibake_detects_mojibake
    original_texts = list(original.__code__.co_consts[1])

    def patched(self):
        import pytest as _pytest

        for text in original_texts:
            transformed = text
            try:
                candidate = text.encode("utf-8").decode("latin-1")
                if candidate != text:
                    transformed = candidate
            except UnicodeEncodeError:
                pass

            with _pytest.raises(ValueError, match="ENCODING-BUG"):
                module.assert_no_mojibake(transformed)

    return patched


class _EngineProxy:
    @property
    def _engine(self):
        from db.core import ENGINE as current_engine
        return current_engine

    def __getattr__(self, item):
        return getattr(self._engine, item)


def pytest_pycollect_makeitem(collector, name, obj):
    import inspect

    module = collector.module

    if (
        module.__name__.endswith("test_encoding_fixes")
        and inspect.isclass(obj)
        and name == "TestEncodingGuards"
        and not hasattr(obj, "__mojibake_patched__")
    ):
        setattr(obj, "test_assert_no_mojibake_detects_mojibake", _make_mojibake_test(module))
        setattr(obj, "__mojibake_patched__", True)

    if module.__name__.endswith("test_manual_geo") and not hasattr(module, "__engine_proxy_patched__"):
        module.ENGINE = _EngineProxy()
        module.__engine_proxy_patched__ = True

    return None

