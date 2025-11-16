# -*- coding: utf-8 -*-
"""
LLM-Optimizer Service für FAMO TrafficApp

Integriert OpenAI API für intelligente Routenoptimierung und Clustering.
Optimiert für GPT-4o-mini für kosteneffiziente Nutzung.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. LLM features will be disabled.")

@dataclass
class OptimizationResult:
    """Ergebnis einer LLM-basierten Optimierung"""
    optimized_route: List[int]
    confidence_score: float
    reasoning: str
    tokens_used: int
    processing_time: float
    model_used: str

@dataclass
class ClusteringResult:
    """Ergebnis einer LLM-basierten Clustering-Analyse"""
    clusters: List[List[int]]
    cluster_centers: List[Tuple[float, float]]
    reasoning: str
    tokens_used: int
    processing_time: float

class LLMOptimizer:
    """LLM-basierter Optimierer für Routenplanung - optimiert für GPT-4o-mini"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Versuche verschlüsselten Key zu laden
        if not api_key:
            try:
                from services.secure_key_manager import get_secure_key
                api_key = get_secure_key("openai")
            except ImportError:
                pass
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # GPT-4o-mini für kosteneffiziente Nutzung
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_cost_usd": 0.0
        }
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                self.enabled = True
                self.logger.info(f"LLM-Optimizer initialized successfully with {self.model}")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            self.enabled = False
            self.logger.warning("LLM-Optimizer disabled - OpenAI not available or no API key")
    
    def optimize_route(self, stops: List[Dict], region: str = "Dresden") -> OptimizationResult:
        """
        Optimiert eine Route mit LLM-basierter Heuristik
        
        WICHTIGE REGEL: Nur Touren mit >6 Kunden werden KI-optimiert!
        Touren mit ≤6 Kunden ergibt sich die Route von alleine.
        
        Args:
            stops: Liste von Stopps mit Koordinaten
            region: Region für Kontext (z.B. "Dresden")
            
        Returns:
            OptimizationResult mit optimierter Route
        """
        # KI-Regel: Nur Touren mit >6 Kunden optimieren
        if len(stops) <= 6:
            self.logger.info(f"Tour mit {len(stops)} Kunden - keine KI-Optimierung nötig (≤6 Kunden)")
            return self._simple_route(stops)
        
        if not self.enabled:
            return self._fallback_optimization(stops)
        
        start_time = time.time()
        
        try:
            # Bereite Prompt vor (kompakt für GPT-4o-mini)
            prompt = self._build_route_optimization_prompt(stops, region)
            
            # LLM-Call mit GPT-4o-mini
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("route_optimization")},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            
            # Berechne Kosten für GPT-4o-mini
            cost_usd = self._calculate_cost(tokens_used)
            
            # Parse Response
            optimized_route = self._parse_route_response(response.choices[0].message.content, len(stops))
            confidence_score = self._calculate_confidence_score(stops, optimized_route)
            
            # Update Metrics
            self._update_metrics(tokens_used, processing_time, True, cost_usd)
            
            return OptimizationResult(
                optimized_route=optimized_route,
                confidence_score=confidence_score,
                reasoning=response.choices[0].message.content,
                tokens_used=tokens_used,
                processing_time=processing_time,
                model_used=self.model
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"LLM optimization failed: {e}")
            self._update_metrics(0, processing_time, False, 0.0)
            
            # Fallback zu Nearest-Neighbor
            return self._fallback_optimization(stops)
    
    def generate_subroutes(self, stops: List[Dict], max_driving_time: int = 60) -> ClusteringResult:
        """
        Generiert KI-Unterrouten basierend auf maximaler Fahrzeit
        
        Args:
            stops: Liste von Stopps
            max_driving_time: Maximale Fahrzeit pro Route in Minuten
            
        Returns:
            ClusteringResult mit Unterrouten
        """
        if not self.enabled:
            return self._fallback_clustering(stops, max_driving_time)
        
        start_time = time.time()
        
        try:
            prompt = self._build_subroute_prompt(stops, max_driving_time)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("subroutes")},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            cost_usd = self._calculate_cost(tokens_used)
            
            # Parse Subroute Response
            clusters, centers = self._parse_subroute_response(response.choices[0].message.content, stops)
            
            self._update_metrics(tokens_used, processing_time, True, cost_usd)
            
            return ClusteringResult(
                clusters=clusters,
                cluster_centers=centers,
                reasoning=response.choices[0].message.content,
                tokens_used=tokens_used,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"LLM subroute generation failed: {e}")
            self._update_metrics(0, processing_time, False, 0.0)
            
            return self._fallback_clustering(stops, max_driving_time)
    
    def _build_route_optimization_prompt(self, stops: List[Dict], region: str) -> str:
        """Baut kompakten Prompt für Routenoptimierung (GPT-4o-mini optimiert)"""
        # Kompakte Darstellung für Token-Effizienz
        stops_info = []
        for i, stop in enumerate(stops[:10]):  # Max 10 Stopps für Token-Effizienz
            name = stop.get('name', 'Unbekannt')[:20]  # Kürze Namen
            address = stop.get('address', 'Keine Adresse')[:30]  # Kürze Adressen
            stops_info.append(f"{i}: {name} - {address}")
        
        if len(stops) > 10:
            stops_info.append(f"... und {len(stops) - 10} weitere Stopps")
        
        return f"""Optimiere Route für {len(stops)} Stopps in {region}.

Stopps:
{chr(10).join(stops_info)}

Kriterien:
- Minimale Gesamtfahrzeit
- Geografische Nähe
- Logische Reihenfolge

Gib optimale Reihenfolge als Zahlenliste zurück: [0,3,1,2,...]"""
    
    def _build_subroute_prompt(self, stops: List[Dict], max_driving_time: int) -> str:
        """Baut Prompt für Unterrouten-Generierung"""
        return f"""Teile {len(stops)} Stopps in optimale Unterrouten auf.

Maximale Fahrzeit pro Route: {max_driving_time} Minuten

Stopps:
{chr(10).join([f"{i}: {s.get('name', 'Unbekannt')[:20]} - {s.get('address', 'Keine Adresse')[:30]}" for i, s in enumerate(stops[:15])])}

Erstelle Unterrouten basierend auf:
- Geografische Nähe
- Maximale Fahrzeit von {max_driving_time} Min
- Ausgewogene Kundenverteilung

Gib Cluster als Listen zurück: [[0,1,2], [3,4,5], ...]"""
    
    def _get_system_prompt(self, task_type: str) -> str:
        """Gibt kompakte System-Prompts zurück (GPT-4o-mini optimiert)"""
        prompts = {
            "route_optimization": """Du bist ein Routenoptimierungs-Experte. 
Optimiere Stopps für minimale Fahrzeit. Antworte nur mit Zahlenliste: [0,3,1,2,...]""",
            
            "subroutes": """Du bist ein Tourenplanungs-Experte.
Teile Stopps in Unterrouten auf. Antworte nur mit Cluster-Listen: [[0,1,2], [3,4,5], ...]""",
            
            "clustering": """Du bist ein Clustering-Experte.
Erstelle geografische Cluster. Antworte mit Cluster-Zuordnungen."""
        }
        return prompts.get(task_type, "Du bist ein hilfreicher Logistik-Assistent.")
    
    def _parse_route_response(self, response: str, num_stops: int) -> List[int]:
        """Parst LLM-Response für Routenoptimierung"""
        try:
            import re
            # Suche nach Zahlenliste im Response
            numbers = re.findall(r'\d+', response)
            route = [int(n) for n in numbers if int(n) < num_stops]
            
            # Validiere Route
            if len(set(route)) == num_stops and max(route) < num_stops:
                return route
            else:
                # Fallback: Standard-Reihenfolge
                return list(range(num_stops))
                
        except Exception:
            return list(range(num_stops))
    
    def _parse_subroute_response(self, response: str, stops: List[Dict]) -> Tuple[List[List[int]], List[Tuple[float, float]]]:
        """Parst LLM-Response für Unterrouten"""
        try:
            import re
            import json
            
            # Suche nach JSON-ähnlichen Listen
            pattern = r'\[\[[\d,\s]+\]\]'
            matches = re.findall(pattern, response)
            
            if matches:
                clusters = json.loads(matches[0])
                # Validiere Cluster
                all_indices = set()
                for cluster in clusters:
                    for idx in cluster:
                        if idx < len(stops):
                            all_indices.add(idx)
                
                # Wenn alle Stopps abgedeckt sind, verwende die Cluster
                if len(all_indices) == len(stops):
                    # Berechne Cluster-Zentren
                    centers = []
                    for cluster in clusters:
                        if cluster:
                            lats = [stops[i].get('lat', 0) for i in cluster if stops[i].get('lat')]
                            lons = [stops[i].get('lon', 0) for i in cluster if stops[i].get('lon')]
                            if lats and lons:
                                centers.append((sum(lats)/len(lats), sum(lons)/len(lons)))
                            else:
                                centers.append((0.0, 0.0))
                        else:
                            centers.append((0.0, 0.0))
                    
                    return clusters, centers
            
            # Fallback: Ein Cluster mit allen Stopps
            return [list(range(len(stops)))], [(0.0, 0.0)]
            
        except Exception:
            return [list(range(len(stops)))], [(0.0, 0.0)]
    
    def _calculate_confidence_score(self, stops: List[Dict], route: List[int]) -> float:
        """Berechnet Confidence-Score für optimierte Route"""
        if len(route) != len(stops):
            return 0.0
        
        # Base score für GPT-4o-mini (etwas konservativer)
        score = 0.75
        
        # Prüfe auf logische Reihenfolge
        if len(set(route)) == len(route):  # Keine Duplikate
            score += 0.1
        
        # Prüfe auf vollständige Abdeckung
        if set(route) == set(range(len(stops))):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_cost(self, tokens: int) -> float:
        """Berechnet Kosten für GPT-4o-mini"""
        # GPT-4o-mini Preise (Stand 2024)
        # Input: $0.15 per 1M tokens
        # Output: $0.60 per 1M tokens
        # Vereinfacht: Durchschnittspreis von $0.375 per 1M tokens
        return (tokens / 1_000_000) * 0.375
    
    def _simple_route(self, stops: List[Dict]) -> OptimizationResult:
        """Einfache Route für Touren mit ≤6 Kunden (keine KI-Optimierung nötig)"""
        return OptimizationResult(
            optimized_route=list(range(len(stops))),
            confidence_score=0.9,
            reasoning=f"Einfache Route für {len(stops)} Kunden - ergibt sich von alleine",
            tokens_used=0,
            processing_time=0.0,
            model_used="simple"
        )
    
    def _fallback_optimization(self, stops: List[Dict]) -> OptimizationResult:
        """Fallback-Optimierung ohne LLM"""
        import math
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371000.0
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            return 2 * R * math.asin(math.sqrt(a))
        
        # Nearest-Neighbor Fallback
        if not stops or len(stops) <= 1:
            return OptimizationResult(
                optimized_route=list(range(len(stops))),
                confidence_score=1.0,
                reasoning="Fallback: Keine Optimierung nötig",
                tokens_used=0,
                processing_time=0.0,
                model_used="fallback"
            )
        
        # Filtere Stopps mit Koordinaten
        valid_stops = [(i, stop) for i, stop in enumerate(stops) 
                      if stop.get('lat') and stop.get('lon')]
        
        if len(valid_stops) <= 1:
            return OptimizationResult(
                optimized_route=list(range(len(stops))),
                confidence_score=0.5,
                reasoning="Fallback: Zu wenige gültige Koordinaten",
                tokens_used=0,
                processing_time=0.0,
                model_used="fallback"
            )
        
        # Nearest-Neighbor Algorithmus
        optimized = [valid_stops[0][0]]
        remaining = valid_stops[1:]
        
        while remaining:
            last_stop = stops[optimized[-1]]
            nearest_idx = min(range(len(remaining)), 
                            key=lambda i: haversine_distance(
                                last_stop['lat'], last_stop['lon'],
                                remaining[i][1]['lat'], remaining[i][1]['lon']
                            ))
            optimized.append(remaining.pop(nearest_idx)[0])
        
        return OptimizationResult(
            optimized_route=optimized,
            confidence_score=0.7,
            reasoning="Fallback: Nearest-Neighbor Optimierung",
            tokens_used=0,
            processing_time=0.0,
            model_used="fallback"
        )
    
    def _fallback_clustering(self, stops: List[Dict], max_driving_time: int) -> ClusteringResult:
        """Fallback-Clustering ohne LLM"""
        # Einfache geografische Clustering
        clusters = []
        centers = []
        
        if len(stops) <= 5:
            # Kleine Touren: Ein Cluster
            clusters = [list(range(len(stops)))]
            centers = [(0.0, 0.0)]
        else:
            # Größere Touren: Aufteilen nach geografischen Bereichen
            # Vereinfachte Implementierung
            mid = len(stops) // 2
            clusters = [list(range(mid)), list(range(mid, len(stops)))]
            centers = [(0.0, 0.0), (0.0, 0.0)]
        
        return ClusteringResult(
            clusters=clusters,
            cluster_centers=centers,
            reasoning=f"Fallback: Geografische Aufteilung (max {max_driving_time} Min)",
            tokens_used=0,
            processing_time=0.0
        )
    
    def _update_metrics(self, tokens: int, processing_time: float, success: bool, cost_usd: float):
        """Aktualisiert Performance-Metriken"""
        self.metrics["total_calls"] += 1
        self.metrics["total_tokens"] += tokens
        self.metrics["total_time"] += processing_time
        self.metrics["total_cost_usd"] += cost_usd
        
        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gibt Performance-Report zurück"""
        # Wenn LLM aktiviert ist, gebe immer "enabled" zurück (auch wenn noch keine Calls gemacht wurden)
        if not self.enabled:
            return {"status": "disabled", "model": "N/A"}
        
        if self.metrics["total_calls"] == 0:
            return {
                "status": "enabled",  # Wichtig: auch ohne Calls als "enabled" markieren
                "model": self.model,
                "total_calls": 0,
                "note": "No calls made yet"
            }
        
        avg_time = self.metrics["total_time"] / self.metrics["total_calls"]
        success_rate = self.metrics["successful_calls"] / self.metrics["total_calls"]
        
        return {
            "status": "enabled" if self.enabled else "disabled",
            "model": self.model,
            "total_calls": self.metrics["total_calls"],
            "successful_calls": self.metrics["successful_calls"],
            "failed_calls": self.metrics["failed_calls"],
            "success_rate": success_rate,
            "total_tokens": self.metrics["total_tokens"],
            "total_cost_usd": round(self.metrics["total_cost_usd"], 6),
            "avg_processing_time": round(avg_time, 3),
            "total_processing_time": round(self.metrics["total_time"], 3)
        }
    
    def reset_metrics(self):
        """Setzt Metriken zurück"""
        self.metrics = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_cost_usd": 0.0
        }
