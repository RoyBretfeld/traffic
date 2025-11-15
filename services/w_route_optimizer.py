"""
W-Route Optimizer für FAMO TrafficApp
Optimiert W-Routen mit KI-basiertem Geocoding-Clustering und detailliertem Reasoning
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from services.llm_optimizer import LLMOptimizer
import math
import json
import logging
import asyncio

# FAMO Depot
FAMO_DEPOT = {
    "name": "FAMO Depot",
    "address": "Stuttgarter Str. 33, 01189 Dresden",
    "lat": 51.0111988,
    "lon": 13.7016485
}

@dataclass
class WRouteOptimizationResult:
    """Ergebnis der W-Route-Optimierung"""
    tours: List[Dict[str, Any]]  # Liste von optimierten Touren (A, B, C...)
    total_customers: int
    total_driving_time_minutes: float
    total_service_time_minutes: float
    warnings: List[str]
    optimization_method: str  # "llm" oder "fallback"
    reasoning: Dict[str, Any]  # Detailliertes Reasoning von der AI


class WRouteOptimizer:
    """Optimiert W-Routen mit KI und Geocoding-Clustering"""
    
    def __init__(self, llm_optimizer: Optional[LLMOptimizer] = None):
        self.llm_optimizer = llm_optimizer or LLMOptimizer()
        self.logger = logging.getLogger(__name__)
        
        # W-Route spezifische Regeln
        self.max_total_time_minutes = 65  # Max. 65 Minuten (inkl. Servicezeit)
        self.service_time_per_customer_minutes = 2  # 2 Min pro Kunde
    
    async def optimize_w_route_with_ai(
        self, 
        tour_id: str, 
        customers: List[Dict[str, Any]],
        osrm_distances: Optional[Dict[str, float]] = None
    ) -> WRouteOptimizationResult:
        """
        Optimiert eine W-Route mit AI und detailliertem Reasoning
        
        Args:
            tour_id: Tour-ID (z.B. "W-07.00")
            customers: Liste von Kunden (mit Koordinaten)
            osrm_distances: Optional: OSRM-Distanzmatrix
            
        Returns:
            WRouteOptimizationResult mit optimierten Sub-Touren und Reasoning
        """
        # 1. Filtere Kunden mit Koordinaten
        valid_customers = [
            c for c in customers 
            if c.get('lat') and c.get('lon')
        ]
        
        if not valid_customers:
            return WRouteOptimizationResult(
                tours=[],
                total_customers=0,
                total_driving_time_minutes=0,
                total_service_time_minutes=0,
                warnings=["Keine Kunden mit Koordinaten"],
                optimization_method="none",
                reasoning={"error": "Keine Kunden mit Koordinaten"}
            )
        
        # 2. Prüfe ob AI verfügbar
        if not self.llm_optimizer.enabled:
            return self._optimize_fallback(tour_id, valid_customers)
        
        # 3. AI-Optimierung mit Reasoning
        try:
            result = await self._optimize_with_ai_reasoning(
                tour_id=tour_id,
                customers=valid_customers,
                osrm_distances=osrm_distances
            )
            return result
        except Exception as e:
            self.logger.error(f"AI-Optimierung fehlgeschlagen: {e}, verwende Fallback")
            return self._optimize_fallback(tour_id, valid_customers)
    
    async def _optimize_with_ai_reasoning(
        self,
        tour_id: str,
        customers: List[Dict],
        osrm_distances: Optional[Dict[str, float]] = None
    ) -> WRouteOptimizationResult:
        """Optimiert Route mit AI und detailliertem Reasoning"""
        
        # 1. System-Prompt laden
        system_prompt = self.llm_optimizer._get_system_prompt("multi_tour_generation")
        
        # 2. User-Prompt erstellen
        user_prompt = self._build_multi_tour_prompt(tour_id, customers, osrm_distances)
        
        # 3. LLM-Call
        response = self.llm_optimizer.client.chat.completions.create(
            model=self.llm_optimizer.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Niedrig für konsistente Ergebnisse
            max_tokens=2000,  # Mehr Tokens für detailliertes Reasoning
            response_format={"type": "json_object"}  # Strukturierte Antwort
        )
        
        # 4. Parse Response
        response_text = response.choices[0].message.content
        result_data = json.loads(response_text)
        
        # 5. Konvertiere zu WRouteOptimizationResult
        tours = []
        total_driving_time = 0
        total_service_time = len(customers) * self.service_time_per_customer_minutes
        
        for tour_data in result_data.get("tours", []):
            customer_ids = tour_data.get("customer_ids", [])
            tour_customers = [customers[i-1] for i in customer_ids if 1 <= i <= len(customers)]
            
            # Depot hinzufügen
            route_with_depot = self._add_depot_points(tour_customers)
            
            # Zeitberechnung
            driving_time = tour_data.get("estimated_driving_time_minutes", 0)
            service_time = len(tour_customers) * self.service_time_per_customer_minutes
            
            tours.append({
                "tour_id": tour_data.get("tour_id", f"{tour_id} {chr(65 + len(tours))}"),
                "stops": route_with_depot,
                "driving_time_minutes": driving_time,
                "service_time_minutes": service_time,
                "customer_count": len(tour_customers),
                "reasoning": tour_data.get("reasoning", "")
            })
            
            total_driving_time += driving_time
        
        return WRouteOptimizationResult(
            tours=tours,
            total_customers=len(customers),
            total_driving_time_minutes=total_driving_time,
            total_service_time_minutes=total_service_time,
            warnings=[],
            optimization_method="llm",
            reasoning={
                "overall_reasoning": result_data.get("overall_reasoning", ""),
                "tours": [t.get("reasoning", "") for t in result_data.get("tours", [])],
                "raw_response": response_text
            }
        )
    
    def _build_multi_tour_prompt(
        self, 
        tour_id: str,
        customers: List[Dict],
        osrm_distances: Optional[Dict[str, float]] = None
    ) -> str:
        """Erstellt User-Prompt für Multi-Tour-Generierung"""
        
        # Kunden-Liste formatieren
        customers_list = []
        for i, customer in enumerate(customers):
            customers_list.append({
                "id": i + 1,
                "name": customer.get('name', 'Unbekannt'),
                "address": customer.get('address', ''),
                "lat": customer.get('lat'),
                "lon": customer.get('lon'),
                "postal_code": customer.get('postal_code', ''),
                "city": customer.get('city', '')
            })
        
        # OSRM-Distanzmatrix (optional)
        distance_matrix_text = ""
        if osrm_distances:
            distance_matrix_text = f"""
OSRM-Straßendistanzen (in Metern):
{json.dumps(osrm_distances, indent=2)}
"""
        
        prompt = f"""
Optimiere die Route "{tour_id}" mit {len(customers)} Kunden.

KUNDEN-LISTE:
{json.dumps(customers_list, indent=2, ensure_ascii=False)}
{distance_matrix_text}

AUFGABE:
1. Teile die Kunden in mehrere Sub-Touren auf (A, B, C, ...)
2. Jede Sub-Tour muss ≤ 65 Minuten sein (inkl. Servicezeit, exkl. Rückfahrt)
3. Gruppiere geografisch nahe Kunden
4. Optimiere die Reihenfolge innerhalb jeder Sub-Tour
5. Erkläre deine Entscheidungen ausführlich

DEPOT:
- Start/Ende: FAMO Depot (51.0111988, 13.7016485)
- Adresse: Stuttgarter Str. 33, 01189 Dresden

ANTWORTE MIT JSON im folgenden Format:
{{
  "tours": [
    {{
      "tour_id": "{tour_id} A",
      "customer_ids": [1, 2, 3, ...],
      "estimated_driving_time_minutes": 45.5,
      "estimated_service_time_minutes": 30,
      "customer_count": 15,
      "reasoning": "Diese Kunden wurden gruppiert, weil sie alle in Dresden-West liegen und ein kompaktes geografisches Cluster bilden. Die Reihenfolge wurde so gewählt, dass die Gesamtfahrzeit minimiert wird..."
    }}
  ],
  "overall_reasoning": "Die Tour wurde in 3 Sub-Touren gesplittet, weil die Gesamtzeit 105 Minuten betragen hätte. Die Kunden wurden nach geografischer Nähe gruppiert: Dresden-West (A), Dresden-Ost (B), Umland (C)..."
}}
"""
        return prompt
    
    def _add_depot_points(self, customers: List[Dict]) -> List[Dict]:
        """Fügt Depot am Start und Ende hinzu"""
        depot_start = {
            **FAMO_DEPOT,
            "type": "depot",
            "sequence": 0,
            "is_depot": True
        }
        depot_end = {
            **FAMO_DEPOT,
            "type": "depot",
            "sequence": len(customers) + 1,
            "is_depot": True
        }
        
        route = [depot_start]
        for i, customer in enumerate(customers):
            customer["sequence"] = i + 1
            customer["is_depot"] = False
            route.append(customer)
        route.append(depot_end)
        
        return route
    
    def _optimize_fallback(
        self, 
        tour_id: str, 
        customers: List[Dict]
    ) -> WRouteOptimizationResult:
        """Fallback-Optimierung ohne AI"""
        # Einfache Nearest-Neighbor Optimierung
        if len(customers) <= 1:
            route = self._add_depot_points(customers)
            return WRouteOptimizationResult(
                tours=[{
                    "tour_id": tour_id,
                    "stops": route,
                    "driving_time_minutes": 0,
                    "service_time_minutes": len(customers) * 2,
                    "customer_count": len(customers)
                }],
                total_customers=len(customers),
                total_driving_time_minutes=0,
                total_service_time_minutes=len(customers) * 2,
                warnings=[],
                optimization_method="fallback",
                reasoning={"method": "Nearest-Neighbor ohne AI"}
            )
        
        # Nearest-Neighbor
        optimized = [customers[0]]
        remaining = customers[1:]
        
        while remaining:
            last = optimized[-1]
            nearest = min(remaining, key=lambda s: self._haversine_distance(
                last.get('lat'), last.get('lon'),
                s.get('lat'), s.get('lon')
            ))
            optimized.append(nearest)
            remaining.remove(nearest)
        
        route = self._add_depot_points(optimized)
        driving_time = self._calculate_driving_time(route)
        
        return WRouteOptimizationResult(
            tours=[{
                "tour_id": tour_id,
                "stops": route,
                "driving_time_minutes": driving_time,
                "service_time_minutes": len(customers) * 2,
                "customer_count": len(customers)
            }],
            total_customers=len(customers),
            total_driving_time_minutes=driving_time,
            total_service_time_minutes=len(customers) * 2,
            warnings=[],
            optimization_method="fallback",
            reasoning={"method": "Nearest-Neighbor Fallback"}
        )
    
    def _calculate_driving_time(self, route: List[Dict]) -> float:
        """Berechnet Fahrzeit (vereinfacht)"""
        total_distance_km = 0
        for i in range(len(route) - 1):
            dist = self._haversine_distance(
                route[i].get('lat'), route[i].get('lon'),
                route[i+1].get('lat'), route[i+1].get('lon')
            )
            total_distance_km += dist * 1.3  # Faktor für Stadtverkehr
        
        # Durchschnittsgeschwindigkeit: 50 km/h
        driving_time_minutes = (total_distance_km / 50.0) * 60
        return driving_time_minutes
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechnet Luftlinie-Distanz in km"""
        R = 6371.0  # Erdradius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))

