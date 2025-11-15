"""
AI-Konfiguration für FAMO TrafficApp
Unterstützt lokale Modell-Ordner und verschiedene AI-Anbieter
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import json


class AIConfig:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.models_dir = self.project_root / "ai_models"
        self.config_file = self.models_dir / "config.json"
        self.load_config()

    def load_config(self) -> None:
        """Lädt AI-Konfiguration"""
        default_config = {
            "preferred_model": "qwen2.5:0.5b",
            "fallback_models": ["qwen2.5:1.5b", "llama3.2:1b"],
            "ollama_url": "http://localhost:11434",
            "model_timeout": 30,
            "use_local_models": True,
            "models_path": str(self.models_dir),
            "optimization_settings": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 300,
                "stop": ["\n\n", "```"],
            },
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception:
                pass  # Verwende default config

        self.config = default_config
        self.save_config()

    def save_config(self) -> None:
        """Speichert AI-Konfiguration"""
        self.models_dir.mkdir(exist_ok=True)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Ignoriere Schreibfehler

    @property
    def preferred_model(self) -> str:
        return self.config["preferred_model"]

    @property
    def fallback_models(self) -> List[str]:
        return self.config["fallback_models"]

    @property
    def ollama_url(self) -> str:
        return self.config["ollama_url"]

    @property
    def optimization_settings(self) -> Dict:
        return self.config["optimization_settings"]

    def get_available_models(self) -> List[str]:
        """Ermittelt verfügbare Modelle"""
        models = [self.preferred_model] + self.fallback_models
        return list(dict.fromkeys(models))  # Remove duplicates

    def set_preferred_model(self, model: str) -> None:
        """Setzt bevorzugtes Modell"""
        self.config["preferred_model"] = model
        self.save_config()

    def get_model_info(self) -> Dict:
        """Gibt Modell-Informationen zurück"""
        return {
            "preferred": self.preferred_model,
            "fallbacks": self.fallback_models,
            "models_dir": str(self.models_dir),
            "ollama_running": self._check_ollama_status(),
        }

    def _check_ollama_status(self) -> bool:
        """Prüft ob Ollama läuft"""
        try:
            import httpx
            import asyncio

            async def check():
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.ollama_url}/api/tags")
                    return response.status_code == 200

            return asyncio.run(check())
        except Exception:
            return False


# Globale Konfiguration
ai_config = AIConfig()
