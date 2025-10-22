#!/usr/bin/env python3
"""
OPENAI API INTEGRATION FÜR FAMO TRAFFICAPP
Netzwerkunabhängige LLM-Integration für Proxmox-Umgebung
"""
import os
import json
from typing import Dict, List, Any, Optional
import httpx
import asyncio

class OpenAIConfig:
    """OpenAI API Konfiguration für FAMO TrafficApp"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # Kostengünstig und schnell
        self.fallback_model = "gpt-3.5-turbo"
        self.timeout = 30
        self.max_tokens = 1000
        self.temperature = 0.1  # Niedrig für konsistente Ergebnisse
        
    def is_configured(self) -> bool:
        """Prüft ob API-Key gesetzt ist"""
        return bool(self.api_key)
    
    def get_headers(self) -> Dict[str, str]:
        """Gibt HTTP-Headers für OpenAI API zurück"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

class OpenAIOptimizer:
    """OpenAI-basierter Optimizer für Tourenplanung"""
    
    def __init__(self):
        self.config = OpenAIConfig()
        
    async def cluster_stops_into_tours(
        self, 
        stops: List[Dict], 
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Teilt Stops in optimale Touren auf"""
        
        if not self.config.is_configured():
            return {
                "tours": [],
                "reasoning": "OpenAI API-Key nicht konfiguriert",
                "error": "missing_api_key"
            }
        
        prompt = self._create_optimization_prompt(stops, rules)
        
        try:
            response = await self._call_openai_api(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {
                "tours": [],
                "reasoning": f"OpenAI API Fehler: {str(e)}",
                "error": "api_error"
            }
    
    def _create_optimization_prompt(self, stops: List[Dict], rules: Dict[str, Any]) -> str:
        """Erstellt Optimierungs-Prompt für OpenAI"""
        
        stops_json = json.dumps(stops, ensure_ascii=False, indent=2)
        
        return f"""Du bist ein Experte für Tourenplanung und Routenoptimierung. Teile die folgenden Kunden in optimale Touren auf.

VERBINDLICHE REGELN:
- Max. {rules.get('max_driving_time', 60)} Minuten Fahrzeit bis zum letzten Kunden
- {rules.get('service_time', 2)} Minuten Verweilzeit pro Kunde
- Max. {rules.get('max_stops', 7)} Kunden pro Tour
- Depot: {rules.get('depot', 'FAMO Dresden')}

OPTIMIERUNGSKRITERIEN:
1. Geografische Nähe der Kunden zueinander
2. Minimale Gesamtfahrzeit
3. Ausgewogene Touren (nicht zu wenige/zu viele Stops)
4. Berücksichtigung der Zeit-Constraints

KUNDEN (JSON):
{stops_json}

ANTWORTE AUSSCHLIESSLICH MIT VALIDEM JSON in diesem Format:
{{
  "tours": [
    {{"name": "Tour A", "customer_ids": [1, 2, 3], "estimated_time": 45}},
    {{"name": "Tour B", "customer_ids": [4, 5], "estimated_time": 30}}
  ],
  "reasoning": "Kurze Begründung der Optimierung",
  "total_customers": {len(stops)},
  "total_tours": 2
}}

WICHTIG: Verwende nur die customer_ids aus der JSON-Liste. Antworte nur mit dem JSON, keine zusätzlichen Erklärungen."""

    async def _call_openai_api(self, prompt: str) -> str:
        """Ruft OpenAI API auf"""
        
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Tourenplanung und Routenoptimierung. Antworte immer mit validem JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"}  # Erzwingt JSON-Ausgabe
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers=self.config.get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"OpenAI API Fehler: {response.status_code} - {response.text}")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parst OpenAI Response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: Versuche JSON zu extrahieren
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            return {
                "tours": [],
                "reasoning": "JSON-Parse-Fehler",
                "error": "parse_error"
            }

async def test_openai_integration():
    """Testet die OpenAI Integration"""
    print('🧪 TESTE OPENAI INTEGRATION:')
    print('=' * 50)
    
    optimizer = OpenAIOptimizer()
    
    if not optimizer.config.is_configured():
        print('❌ OPENAI_API_KEY nicht gesetzt!')
        print('   Setze Umgebungsvariable: OPENAI_API_KEY=your_key_here')
        return False
    
    print('✅ OpenAI API-Key konfiguriert')
    
    # Test mit Beispieldaten
    test_stops = [
        {"customer_id": 1, "name": "Kunde A", "lat": 51.0504, "lon": 13.7373, "address": "Dresden Zentrum"},
        {"customer_id": 2, "name": "Kunde B", "lat": 51.0600, "lon": 13.7400, "address": "Dresden Nord"},
        {"customer_id": 3, "name": "Kunde C", "lat": 51.0400, "lon": 13.7300, "address": "Dresden Süd"},
    ]
    
    test_rules = {
        "max_driving_time": 60,
        "service_time": 2,
        "max_stops": 7,
        "depot": "FAMO Dresden"
    }
    
    print('🔄 Teste Tourenoptimierung...')
    result = await optimizer.cluster_stops_into_tours(test_stops, test_rules)
    
    print('📊 ERGEBNIS:')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return "error" not in result

if __name__ == '__main__':
    asyncio.run(test_openai_integration())
