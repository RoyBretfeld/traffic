"""
FAMO TrafficApp - Optimierungsregeln und Constraints
Definiert klare Regeln für die KI-Routenoptimierung
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class OptimizationRules:
    """Konfiguration für Routenoptimierung"""

    # Hauptziele (Priorität)
    primary_goal: str = (
        "shortest_distance"  # shortest_distance, fastest_time, lowest_cost
    )
    consider_live_traffic: bool = True
    consider_fuel_costs: bool = True

    # Neue erweiterte Constraints (basierend auf Feedback)
    max_stops_per_tour: int = 7  # Realistische 7 Stopps pro Tour (5 Touren A-E)
    max_driving_time_to_last_customer: int = 60  # Minuten bis letzter Kunde (wie ursprünglich festgelegt)
    service_time_per_customer_minutes: int = 2  # Verweilzeit pro Kunde
    return_trip_buffer_minutes: int = 5  # Puffer für Rückfahrt (+/- 5min)
    include_return_trip: bool = True  # + Rückfahrt zur FAMO

    # FAMO Standort
    start_location: str = "Stuttgarter Str. 33, 01189 Dresden"
    end_location: str = "Stuttgarter Str. 33, 01189 Dresden"
    depot_lat: float = 51.0111988
    depot_lon: float = 13.7016485

    # Fahrzeug-Spezifikationen
    fuel_type: str = "diesel"  # diesel, benzin, electric
    fuel_consumption_per_100km: float = 8.5  # Liter pro 100km
    fuel_price_per_liter: float = 1.45  # Euro pro Liter

    # Live-Daten Prioritäten
    avoid_construction: bool = True
    avoid_accidents: bool = True
    prefer_highways: bool = False
    avoid_city_center_rush: bool = True

    # Zeitfenster
    allow_reordering: bool = True  # Darf Reihenfolge ändern
    respect_time_windows: bool = False  # Erstmal deaktiviert

    # Kostenberechnung
    driver_cost_per_hour: float = 25.0  # Euro pro Stunde
    vehicle_depreciation_per_km: float = 0.35  # Euro pro km


@dataclass
class OptimizationResult:
    """Ergebnis der Optimierung"""

    original_distance_km: float
    optimized_distance_km: float
    distance_saved_km: float
    distance_saved_percent: float

    original_time_minutes: int
    optimized_time_minutes: int
    time_saved_minutes: int

    original_fuel_cost: float
    optimized_fuel_cost: float
    fuel_cost_saved: float

    total_cost_original: float
    total_cost_optimized: float
    total_savings: float

    optimized_sequence: List[int]
    warnings: List[str]
    live_traffic_considered: bool

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für JSON Response"""
        return {
            "distance": {
                "original_km": self.original_distance_km,
                "optimized_km": self.optimized_distance_km,
                "saved_km": self.distance_saved_km,
                "saved_percent": round(self.distance_saved_percent, 1),
            },
            "time": {
                "original_minutes": self.original_time_minutes,
                "optimized_minutes": self.optimized_time_minutes,
                "saved_minutes": self.time_saved_minutes,
            },
            "costs": {
                "fuel_original": round(self.original_fuel_cost, 2),
                "fuel_optimized": round(self.optimized_fuel_cost, 2),
                "fuel_saved": round(self.fuel_cost_saved, 2),
                "total_original": round(self.total_cost_original, 2),
                "total_optimized": round(self.total_cost_optimized, 2),
                "total_saved": round(self.total_savings, 2),
            },
            "route": {
                "optimized_sequence": self.optimized_sequence,
                "live_traffic_used": self.live_traffic_considered,
            },
            "warnings": self.warnings,
        }


def create_optimization_prompt(
    rules: OptimizationRules, stops: List[Dict], current_sequence: List[int]
) -> str:
    """Erstellt KI-Prompt basierend auf den neuen FAMO-Routing-Regeln"""

    prompt = f"""Du arbeitest an der Routen‑Generierung der FAMO TrafficApp auf Basis von CSV/JSON‑Daten (bereits geparste Touren & Stopps).
Ziel: korrekte Straßenrouten erzeugen (OSRM/ORS), Constraints erzwingen, Waypoint-Limits beachten, keine Luftlinien.

VERBINDLICHE REGELN:

Nur echte Straßenrouten:
- Verwende OSRM oder OpenRouteService (ORS).
- Keine Luftlinien/Platzhalter rendern.
- Karte nur anzeigen, wenn Routing‑Antwort (Geometry) vorliegt.

Depot (Start/Ende):
- „{rules.start_location}" ist Start und Ende jeder Tour.
- Depot wird automatisch als erster und letzter RoutePoint eingefügt.

Zeit‑Constraints:
- Max. {rules.max_driving_time_to_last_customer} Minuten Fahrzeit bis zum letzten Kunden (Rückfahrt zum Depot kommt danach und zählt nicht in die {rules.max_driving_time_to_last_customer} Minuten).
- {rules.service_time_per_customer_minutes} Minuten Verweilzeit je Stopp addieren.
- ±{rules.return_trip_buffer_minutes} Minuten Toleranz.
- Falls Verletzung: Tour splitten (A, B, C …) oder Stopps umverteilen.

Handy-Export (Google Maps):
- Für Google Maps Export max. 23 Waypoints (Start/Ende inkl.).
- Bei >23 Zwischenstopps: Tour in 23-Waypoint-Chunks aufteilen für Handy-Navigation.
- Tour-Generierung selbst ist NICHT durch Waypoint-Limit begrenzt.

Sequenz & Clustering:
- Standard: Dokumenten-/CSV‑Reihenfolge (seq_no) beibehalten.
- Optionales Georouting/Clustering nur, wenn es die {rules.max_driving_time_to_last_customer}‑Min‑Regel erfüllt und Waypoint‑Limit einhält.
- Ergebnis: Tabs W‑07:00 A, W‑07:00 B, … mit konsistenter Farb-/Ausgraulogik.

BAR (Zahlung):
- „BAR" ist Flag, keine eigene Tour.
- In Export/Detail sichtbar halten, ändert nicht die Routing‑Metrik.

AKTUELLE STOPPS ({len(stops)}):
"""
    
    # Stopp-Details hinzufügen
    for i, stop in enumerate(stops[:15]):  # Erste 15 für besseren Überblick
        prompt += f"Stopp {i+1}: {stop.get('name', 'Unbekannt')} - {stop.get('address', 'Keine Adresse')}\n"

    if len(stops) > 15:
        prompt += f"... und {len(stops) - 15} weitere Stopps\n"

    prompt += f"""
AUFGABE:
1. Analysiere geografische Verteilung der Kunden
2. Minimiere {rules.primary_goal.replace('_', ' ')}
3. Berücksichtige Verkehrslage und regionale Besonderheiten
4. KRITISCH: Zeitberechnung = Fahrzeit + ({rules.service_time_per_customer_minutes}min × Anzahl Kunden) + Rückfahrt ≤ {rules.max_driving_time_to_last_customer + rules.return_trip_buffer_minutes}min
5. Berechne realistische Kosten-Nutzen inkl. Verweilzeiten und Rückweg

ANTWORT FORMAT (JSON):
{{
    "optimized_sequence": [0, 3, 7, 2, 1, 4, 5, 6, 8],
    "distance_km": 45.2,
    "driving_time_minutes": 55,
    "service_time_total": {rules.service_time_per_customer_minutes * len(stops) if stops else 0},
    "return_trip_time": {rules.return_trip_buffer_minutes},
    "total_time_minutes": "driving + service + return = XX",
    "fuel_cost": 28.50,
    "reasoning": "Geografisch optimiert für Mitteldeutschland, unter {rules.max_driving_time_to_last_customer}min + {rules.return_trip_buffer_minutes}min Rückweg",
    "live_traffic_impact": "Verkehrsanpassungen in der Region",
    "cost_savings": "Einsparung durch optimierte Route",
    "time_constraint_ok": true,
    "max_time_allowed": {rules.max_driving_time_to_last_customer + rules.return_trip_buffer_minutes}
}}

Antworte NUR mit JSON, keine Erklärungen.
"""

    return prompt


# Globale Regeln
default_rules = OptimizationRules()
