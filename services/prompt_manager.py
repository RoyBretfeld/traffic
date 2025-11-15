# -*- coding: utf-8 -*-
"""
Prompt-Templates und Konfiguration für LLM-Integration

Zentrale Verwaltung von Prompts und Konfigurationen für konsistente LLM-Nutzung.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PromptTemplate:
    """Dataclass für Prompt-Templates"""
    name: str
    description: str
    system_prompt: str
    user_template: str
    parameters: List[str]
    expected_output: str
    version: str = "1.0"

@dataclass
class LLMConfig:
    """Konfiguration für LLM-Integration"""
    model: str
    max_tokens: int
    temperature: float
    timeout: int
    retry_attempts: int
    cost_limit_per_day: float
    quality_threshold: float

class PromptManager:
    """Manager für Prompt-Templates und Konfigurationen"""
    
    def __init__(self, config_dir: str = "config/llm"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, PromptTemplate] = {}
        self.config: Optional[LLMConfig] = None
        
        self._load_templates()
        self._load_config()
    
    def _load_templates(self):
        """Lädt Prompt-Templates aus Dateien"""
        templates_file = self.config_dir / "prompt_templates.json"
        
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates_data = json.load(f)
                
                for template_data in templates_data.get("templates", []):
                    template = PromptTemplate(**template_data)
                    self.templates[template.name] = template
                    
            except Exception as e:
                print(f"Error loading templates: {e}")
        else:
            # Erstelle Standard-Templates
            self._create_default_templates()
    
    def _load_config(self):
        """Lädt LLM-Konfiguration"""
        config_file = self.config_dir / "llm_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self.config = LLMConfig(**config_data)
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            # Erstelle Standard-Konfiguration
            self._create_default_config()
    
    def _create_default_templates(self):
        """Erstellt Standard-Prompt-Templates"""
        default_templates = [
            PromptTemplate(
                name="route_optimization",
                description="Optimiert Routen für minimale Fahrzeit",
                system_prompt="""Du bist ein Experte für Routenoptimierung und Logistik. 
Analysiere die gegebenen Stopps und optimiere die Reihenfolge für minimale Fahrzeit.
Berücksichtige geografische Nähe, Verkehrszeiten und logische Abfolgen.
Antworte präzise mit der optimalen Reihenfolge als Zahlenliste.""",
                user_template="""Optimiere die Route für {num_stops} Stopps in {region}.

Stopps:
{stops_info}

Berücksichtige:
- Minimale Gesamtfahrzeit
- Logische geografische Reihenfolge
- Prioritäten der Kunden (falls vorhanden)
- Verkehrszeiten und Hauptverkehrszeiten

Gib die optimale Reihenfolge als Liste von Indizes zurück (z.B. [0, 3, 1, 2]).
Begründe deine Entscheidung kurz.""",
                parameters=["num_stops", "region", "stops_info"],
                expected_output="Liste von Indizes in optimaler Reihenfolge",
                version="1.0"
            ),
            
            PromptTemplate(
                name="clustering_analysis",
                description="Analysiert optimale Clustering-Parameter",
                system_prompt="""Du bist ein Experte für geografisches Clustering und Tourenplanung.
Analysiere die Stopps und empfehle optimale Cluster für effiziente Touren.
Berücksichtige geografische Nähe, Kundenprioritäten und logistische Faktoren.
Antworte mit konkreten Cluster-Zuordnungen und Begründung.""",
                user_template="""Analysiere diese {num_stops} Stopps für optimale Clustering:

{stops_info}

Empfehle:
- Optimale Anzahl Cluster (max. {max_clusters})
- Cluster-Zuordnung für jeden Stopp
- Begründung der Clustering-Strategie

Gib die Cluster als Listen von Indizes zurück.""",
                parameters=["num_stops", "stops_info", "max_clusters"],
                expected_output="Cluster-Zuordnungen als Listen von Indizes",
                version="1.0"
            ),
            
            PromptTemplate(
                name="address_validation",
                description="Validiert und korrigiert Adressen",
                system_prompt="""Du bist ein Experte für deutsche Adressen und Postleitzahlen.
Validiere und korrigiere Adressen für bessere Geocoding-Ergebnisse.
Berücksichtige deutsche Adresskonventionen und häufige Fehler.""",
                user_template="""Validiere und korrigiere diese Adresse:

Original: {original_address}
Region: {region}

Korrigiere:
- Schreibfehler
- Fehlende Straßennamen
- Falsche Postleitzahlen
- Stadtteil-Zuordnungen

Gib die korrigierte Adresse zurück.""",
                parameters=["original_address", "region"],
                expected_output="Korrigierte Adresse",
                version="1.0"
            ),
            
            PromptTemplate(
                name="code_review",
                description="Führt Code-Review durch",
                system_prompt="""Du bist ein erfahrener Software-Architekt und Code-Reviewer. 
Bewerte den Code-Diff kritisch auf Qualität, Architekturkonformität, Bugs und Best Practices.
Berücksichtige Python-spezifische Konventionen und das bestehende Codebase-Design.""",
                user_template="""Führe eine Code-Review für diese Änderungen durch:

Datei: {file_path}
Kontext: {context}

Diff:
{diff}

Bewerte:
- Code-Qualität und Lesbarkeit
- Architekturkonformität
- Potentielle Bugs
- Performance-Impact
- Best Practices

Gib eine strukturierte Bewertung zurück.""",
                parameters=["file_path", "context", "diff"],
                expected_output="Strukturierte Code-Review mit Bewertungen",
                version="1.0"
            ),
            
            PromptTemplate(
                name="test_generation",
                description="Generiert Unit-Tests für Code",
                system_prompt="""Du bist ein Experte für Test-Driven Development und Python-Testing.
Generiere umfassende Unit-Tests für den gegebenen Code.
Berücksichtige Edge-Cases, Error-Handling und verschiedene Szenarien.""",
                user_template="""Generiere Unit-Tests für diese Funktion:

Code:
{code}

Funktion: {function_name}
Modul: {module_name}

Erstelle Tests für:
- Normale Funktionalität
- Edge-Cases
- Error-Handling
- Verschiedene Input-Typen

Verwende pytest-Syntax.""",
                parameters=["code", "function_name", "module_name"],
                expected_output="Pytest-kompatible Unit-Tests",
                version="1.0"
            )
        ]
        
        self.templates = {template.name: template for template in default_templates}
        self._save_templates()
    
    def _create_default_config(self):
        """Erstellt Standard-LLM-Konfiguration"""
        self.config = LLMConfig(
            model="gpt-4o",
            max_tokens=1000,
            temperature=0.3,
            timeout=30,
            retry_attempts=3,
            cost_limit_per_day=10.0,
            quality_threshold=0.8
        )
        self._save_config()
    
    def _save_templates(self):
        """Speichert Templates in Datei"""
        templates_file = self.config_dir / "prompt_templates.json"
        
        templates_data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "templates": [template.__dict__ for template in self.templates.values()]
        }
        
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, indent=2, ensure_ascii=False)
    
    def _save_config(self):
        """Speichert Konfiguration in Datei"""
        config_file = self.config_dir / "llm_config.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config.__dict__, f, indent=2, ensure_ascii=False)
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Gibt Template nach Namen zurück"""
        return self.templates.get(name)
    
    def format_prompt(self, template_name: str, **kwargs) -> Dict[str, str]:
        """
        Formatiert Prompt mit Template
        
        Args:
            template_name: Name des Templates
            **kwargs: Parameter für Template
            
        Returns:
            Dict mit system_prompt und user_prompt
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validiere Parameter
        missing_params = set(template.parameters) - set(kwargs.keys())
        if missing_params:
            raise ValueError(f"Missing parameters: {missing_params}")
        
        # Formatiere User-Prompt
        try:
            user_prompt = template.user_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template formatting error: {e}")
        
        return {
            "system_prompt": template.system_prompt,
            "user_prompt": user_prompt,
            "template_name": template_name,
            "version": template.version
        }
    
    def add_template(self, template: PromptTemplate):
        """Fügt neues Template hinzu"""
        self.templates[template.name] = template
        self._save_templates()
    
    def update_template(self, name: str, **updates):
        """Aktualisiert bestehendes Template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        
        template = self.templates[name]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self._save_templates()
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Gibt Liste aller Templates zurück"""
        return [
            {
                "name": template.name,
                "description": template.description,
                "version": template.version,
                "parameters": template.parameters
            }
            for template in self.templates.values()
        ]
    
    def validate_template(self, template_name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validiert Template mit Test-Daten
        
        Args:
            template_name: Name des Templates
            test_data: Test-Daten für Parameter
            
        Returns:
            Validierungs-Ergebnis
        """
        template = self.get_template(template_name)
        if not template:
            return {"valid": False, "error": f"Template '{template_name}' not found"}
        
        try:
            formatted = self.format_prompt(template_name, **test_data)
            
            return {
                "valid": True,
                "formatted_prompt": formatted,
                "template_info": {
                    "name": template.name,
                    "version": template.version,
                    "parameters": template.parameters
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "template_info": {
                    "name": template.name,
                    "version": template.version,
                    "parameters": template.parameters
                }
            }
    
    def get_config(self) -> LLMConfig:
        """Gibt aktuelle Konfiguration zurück"""
        return self.config
    
    def update_config(self, **updates):
        """Aktualisiert Konfiguration"""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._save_config()
    
    def export_templates(self, file_path: str):
        """Exportiert alle Templates"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "templates": [template.__dict__ for template in self.templates.values()],
            "config": self.config.__dict__ if self.config else None
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def import_templates(self, file_path: str):
        """Importiert Templates aus Datei"""
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # Importiere Templates
        for template_data in import_data.get("templates", []):
            template = PromptTemplate(**template_data)
            self.templates[template.name] = template
        
        # Importiere Konfiguration falls vorhanden
        if import_data.get("config"):
            self.config = LLMConfig(**import_data["config"])
        
        self._save_templates()
        self._save_config()
