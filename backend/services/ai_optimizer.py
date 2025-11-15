"""
KI-basierte Routenoptimierung für FAMO TrafficApp
Unterstützt lokale (Ollama) und Cloud-APIs
"""

from __future__ import annotations
import json
import httpx
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .ai_config import ai_config
from openai import OpenAI

from .optimization_rules import (
    OptimizationRules,
    OptimizationResult as RulesOptimizationResult,
    create_optimization_prompt,
    default_rules,
)


@dataclass
class Stop:
    id: str
    name: str
    address: str
    lat: float
    lon: float
    sequence: int


# Verwende die OptimizationResult aus optimization_rules.py
# Diese Klasse wurde entfernt um Konflikte zu vermeiden


class AIOptimizer:
    def __init__(self, use_local: bool = True, api_key: Optional[str] = None):
        self.use_local = use_local
        self.api_key = api_key
        self.config = ai_config
        self.ollama_url = self.config.ollama_url
        self.openai_client = None
        if self.api_key:
            self.openai_client = OpenAI(api_key=self.api_key)

    async def optimize_route(
        self,
        stops: List[Stop],
        depot_lat: float,
        depot_lon: float,
        rules: OptimizationRules = None,
    ) -> RulesOptimizationResult:
        """Optimiert eine Route mit KI basierend auf definierten Regeln"""

        if rules is None:
            rules = default_rules

        # Prüfe Constraints (nur Zeit-Constraint, kein Stop-Limit mehr)
        # Das Zeit-Constraint wird im Prompt und in der Validierung geprüft

        # Konvertiere Stopps für Prompt
        stops_data = [
            {"name": s.name, "address": s.address, "lat": s.lat, "lon": s.lon}
            for s in stops
        ]
        current_sequence = [s.sequence for s in stops]

        # Regelbasierter Prompt erstellen
        prompt = create_optimization_prompt(rules, stops_data, current_sequence)

        if self.use_local:
            response = await self._call_ollama(prompt, require_json=True)
        else:
            response = await self._call_cloud_api(prompt)

        return self._parse_ai_response(response, stops, rules)

    async def cluster_stops_into_tours(
        self, stops: List[Stop], rules: OptimizationRules
    ) -> Dict[str, Any]:
        """Lässt die KI mehrere Touren vorschlagen, die alle Constraints einhalten.
        Erwartetes JSON-Format:
        {
          "tours": [
            {"name": "A", "customer_ids": [1,2,3]},
            {"name": "B", "customer_ids": [4,5]}
          ],
          "reasoning": "..."
        }
        """
        stops_payload = [
            {
                "id": s.id,
                "name": s.name,
                "address": s.address,
                "lat": s.lat,
                "lon": s.lon,
            }
            for s in stops
        ]
        max_minutes = (
            rules.max_driving_time_to_last_customer
            + (rules.return_trip_buffer_minutes if rules.include_return_trip else 0)
        )
        prompt = f"""
Du arbeitest an der KI-basierten Routenoptimierung der FAMO TrafficApp. Teile die folgenden Kunden in optimale Touren auf, basierend auf geografischer Nähe und Zeit-Constraints.

VERBINDLICHE REGELN (KRITISCH - KEINE AUSNAHMEN):

Zeit-Constraints (HÖCHSTE PRIORITÄT):
- KRITISCH: Jede Tour muss ≤ 65 Minuten (OHNE Rückfahrt) sein!
- Berechnung: Fahrzeit + Servicezeit ≤ 65 Minuten
- Servicezeit = {rules.service_time_per_customer_minutes} Minuten × Anzahl Kunden
- Beispiel: Wenn Tour 7 Kunden hat → Servicezeit = 14 Minuten → Fahrzeit muss ≤ 51 Minuten sein
- Rückfahrt zum Depot kommt DANACH und zählt NICHT in die 65 Minuten!
- Wenn eine Gruppe zu groß wäre → ERSTELLE MEHRERE SEPARATE TOUREN (A, B, C, D, E), NICHT Unterrouten!

Geografische Optimierung:
- Gruppiere Kunden nach geografischer Nähe zueinander
- Berücksichtige die Distanz zum Depot (FAMO Dresden)
- Optimiere die Reihenfolge der Kunden innerhalb jeder Tour
- KEIN Limit für Anzahl Kunden pro Tour - nur Zeit-Constraint (≤ 65 Min ohne Rückfahrt) ist relevant!
- Wenn Zeit-Constraint nicht erfüllt → weniger Kunden pro Tour, mehr Touren erstellen!

Priorität:
1. Zeit-Constraint ≤ 65 Min (ohne Rückfahrt) - MUSS erfüllt sein
2. Geografische Nähe
3. Kein Stop-Limit - so viele Kunden wie möglich, solange Zeit-Constraint erfüllt ist

Service-Gebiet:
- Nur Kunden in Sachsen, Brandenburg, Sachsen-Anhalt, Thüringen
- Koordinaten: {rules.depot_lat}, {rules.depot_lon} (Dresden)

Depot:
- Jede Tour startet und endet an FAMO Dresden (Stuttgarter Str. 33, 01189 Dresden).
- Depot wird automatisch als erster und letzter RoutePoint eingefügt.

STOPPS (JSON): {json.dumps(stops_payload, ensure_ascii=False)}

ANTWORTIERE AUSSCHLIESSLICH MIT VALIDESEM JSON OHNE ERLÄUTERUNGEN in diesem Format:
{{
  "tours": [
    {{"name": "A", "customer_ids": [1,2,3]}},
    {{"name": "B", "customer_ids": [4,5]}}
  ],
  "reasoning": "kurze Begründung"
}}
"""
        if self.use_local:
            raw = await self._call_ollama(prompt, require_json=True)
        else:
            raw = await self._call_cloud_api(prompt)
        try:
            return self._parse_json_strict(raw)
        except Exception:
            # Fallback: Versuche JSON zwischen Klammern zu extrahieren
            try:
                return json.loads(self._extract_json(raw))
            except Exception:
                return {"tours": [], "reasoning": "KI-Parse-Fehler"}

    async def _call_ollama(self, prompt: str, require_json: bool = False) -> str:
        """Ruft lokale Ollama-API auf. Wenn require_json=True, erzwinge JSON-Ausgabe."""
        models_to_try = [self.config.preferred_model] + self.config.fallback_models

        payload_base: Dict[str, Any] = {
            "prompt": prompt,
            "stream": False,
            "options": self.config.optimization_settings,
        }
        if require_json:
            # Viele Ollama-Modelle unterstützen format: json → garantiert valides JSON
            payload_base["format"] = "json"

        for model in models_to_try:
            try:
                print(f"🔍 Versuche Modell: {model}")
                async with httpx.AsyncClient(timeout=self.config.config["model_timeout"]) as client:
                    payload = dict(payload_base)
                    payload["model"] = model
                    response = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json=payload,
                    )
                    print(f"📊 {model} Status: {response.status_code}")
                    if response.status_code == 200:
                        ai_response = response.json().get("response", "")
                        print(f"✅ {model} Antwort (Roh): {ai_response[:500]}...") # Logge die rohe KI-Antwort
                        return ai_response
                    else:
                        print(f"❌ {model} Fehler: {response.status_code}")
                        continue
            except Exception as e:
                print(f"💥 {model} Exception: {e}")
                continue

        print("❌ Alle Modelle fehlgeschlagen, verwende Fallback")
        return self._fallback_optimization(prompt)

    async def _call_cloud_api(self, prompt: str) -> str:
        """Ruft Cloud-API (OpenAI) auf."""
        if not self.openai_client:
            print("❌ OpenAI Client nicht initialisiert. Verwende Fallback.")
            return self._fallback_optimization(prompt)

        try:
            print("🔍 Versuche OpenAI (gpt-4o-mini)...")
            # System-Prompt mit Route-Rules laden
            system_prompt = self._get_route_rules_system_prompt()
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"}, # Erzwinge JSON
                temperature=0.7,
                max_tokens=self.config.config["num_predict"], # Verwende num_predict als max_tokens
            )
            ai_response = response.choices[0].message.content
            print(f"✅ OpenAI Antwort (Roh): {ai_response[:500]}...") # Logge die rohe KI-Antwort
            return ai_response
        except Exception as e:
            print(f"💥 OpenAI Exception: {e}")
            return self._fallback_optimization(prompt)

    def _extract_time_minutes(self, data: dict) -> int:
        """Extrahiert Zeit in Minuten aus verschiedenen KI-Antwort-Formaten"""
        # Versuche verschiedene Felder
        time_fields = ["estimated_time_minutes", "driving_time_minutes", "total_time_minutes"]
        
        for field in time_fields:
            if field in data:
                value = data[field]
                if isinstance(value, int):
                    return value
                elif isinstance(value, str):
                    # Extrahiere Zahl aus String wie "driving + service + return = 100"
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        return int(numbers[-1])  # Nimm die letzte Zahl
        
        return 60  # Fallback

    def _get_route_rules_system_prompt(self) -> str:
        """
        Lädt System-Prompt mit Route-Rules aus docs/LLM_ROUTE_RULES.md
        
        Dies stellt sicher, dass das LLM die verbindlichen Regeln kennt:
        - 65 Minuten OHNE Rückfahrt (Hauptregel)
        - 90 Minuten INKL. Rückfahrt (Zeitbox)
        - Service-Zeit: 2 Minuten pro Kunde
        - Straßenbasierte Clustering
        - etc.
        """
        import os
        rules_file = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "LLM_ROUTE_RULES.md")
        
        try:
            if os.path.exists(rules_file):
                with open(rules_file, "r", encoding="utf-8") as f:
                    rules_content = f.read()
                # Extrahiere nur die verbindlichen Regeln (nicht die ganze Dokumentation)
                # Vereinfachte Version für System-Prompt
                return """Du bist ein Routenplanungs-Experte für die FAMO TrafficApp.

VERBINDLICHE REGELN:
1. Zeit-Constraints (HÖCHSTE PRIORITÄT):
   - KRITISCH: Jede Tour muss ≤ 65 Minuten (OHNE Rückfahrt) sein!
   - Fahrzeit + Servicezeit ≤ 65 Minuten
   - Servicezeit = 2 Minuten × Anzahl Kunden
   - Rückfahrt zählt NICHT in die 65 Minuten!

2. Geografische Optimierung:
   - Priorität: Zeit-Constraint → Geografische Nähe → Max. Stopps
   - Straßenbasierte Clustering (gleiche Straße zuerst)
   - Max. 15 Kunden pro Tour (nur wenn Zeit erfüllt)

3. Depot:
   - Start/Ende: FAMO Dresden (51.0111988, 13.7016485)
   - Rückfahrt wird separat berechnet

4. Tour-Aufteilung:
   - Bei Überschreitung: Separate Touren (A, B, C) erstellen, NICHT Sub-Routen

Antworte IMMER mit gültigem JSON gemäß dem angeforderten Format."""
            else:
                # Fallback wenn Datei nicht gefunden
                return """Du bist ein Routenplanungs-Experte. Folge diesen Regeln:
- Jede Tour ≤ 65 Minuten (OHNE Rückfahrt)
- Service-Zeit: 2 Minuten pro Kunde
- Depot: FAMO Dresden (51.0111988, 13.7016485)
- Antworte mit gültigem JSON."""
        except Exception as e:
            print(f"[WARNUNG] Konnte Route-Rules nicht laden: {e}")
            return "Du bist ein Routenplanungs-Experte. Antworte nur mit gültigem JSON."

    def _fallback_optimization(self, prompt: str) -> str:
        """Fallback wenn KI nicht verfügbar ist"""
        return json.dumps(
            {
                "optimized_sequence": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                "total_distance_km": 50.0,
                "estimated_time_minutes": 150,
                "improvements": "Fallback: Reihenfolge beibehalten",
                "reasoning": "KI nicht verfügbar, verwende ursprüngliche Reihenfolge",
            }
        )

    def _parse_ai_response(
        self, response: str, stops: List[Stop], rules: OptimizationRules
    ) -> RulesOptimizationResult:
        """Parst die KI-Antwort robust auf JSON."""
        try:
            data = self._parse_json_strict(response)
        except Exception:
            try:
                data = json.loads(self._extract_json(response))
            except Exception as e:
                return RulesOptimizationResult(
                    original_distance_km=0.0,
                    optimized_distance_km=0.0,
                    distance_saved_km=0.0,
                    distance_saved_percent=0.0,
                    original_time_minutes=0,
                    optimized_time_minutes=0,
                    time_saved_minutes=0,
                    original_fuel_cost=0.0,
                    optimized_fuel_cost=0.0,
                    fuel_cost_saved=0.0,
                    total_cost_original=0.0,
                    total_cost_optimized=0.0,
                    total_savings=0.0,
                    optimized_sequence=list(range(len(stops))),
                    warnings=[f"Parse-Fehler: {str(e)}"],
                    live_traffic_considered=False,
                )

        return RulesOptimizationResult(
            original_distance_km=0.0,
            optimized_distance_km=data.get("total_distance_km", data.get("distance_km", 0.0)),
            distance_saved_km=0.0,
            distance_saved_percent=0.0,
            original_time_minutes=0,
            optimized_time_minutes=self._extract_time_minutes(data),
            time_saved_minutes=0,
            original_fuel_cost=0.0,
            optimized_fuel_cost=0.0,
            fuel_cost_saved=0.0,
            total_cost_original=0.0,
            total_cost_optimized=0.0,
            total_savings=0.0,
            optimized_sequence=data.get("optimized_sequence", []),
            warnings=[],
            live_traffic_considered=False,
        )

    def _parse_json_strict(self, text: str) -> Dict[str, Any]:
        """Parst JSON ohne Heuristik – wir erwarten valides JSON (Ollama format=json)."""
        return json.loads(text)

    def _extract_json(self, text: str) -> str:
        """Extrahiert JSON anhand erster/letzter Klammer – nur Fallback."""
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return text[start:end]
        raise ValueError("Kein JSON in Antwort gefunden")


# Utility-Funktionen
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet Luftlinie-Distanz zwischen zwei Punkten in km"""
    import math

    R = 6371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
