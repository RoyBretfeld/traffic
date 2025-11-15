"""
Workflow Orchestrator - Modul 6
Aufgabe: Alle Module koordinieren
Verantwortlichkeit: Nur Orchestrierung, keine Geschäftslogik
"""

from __future__ import annotations
from typing import Dict, List, Any, Union, Optional
from pathlib import Path
from io import BytesIO
import tempfile

from backend.parsers import parse_tour_plan, parse_tour_plan_to_dict, TourPlan, TourInfo

from .file_parser import FileParserService
from .ai_optimizer import AIOptimizer, Stop
from .optimization_rules import default_rules


class WorkflowOrchestrator:
    """Orchestriert den kompletten Workflow von CSV zu Untertouren"""
    
    def __init__(self):
        self.file_parser = FileParserService()
        self.ai_optimizer = AIOptimizer(use_local=True)
    
    async def process_csv_to_subtours(self, file_input: Union[str, Path, BytesIO], 
                                    filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Hauptmethode: Verarbeitet CSV-Datei zu Untertouren
        
        Args:
            file_input: Datei (Pfad, String oder BytesIO)
            filename: Dateiname (bei BytesIO erforderlich)
            
        Returns:
            Vollständige Verarbeitungsergebnisse
        """
        try:
            plan, plan_dict = self._parse_input_to_plan(file_input, filename)

            file_info = {
                "parsing_method": "tour_plan_parser",
                "tours_found": plan.total_tours,
                "total_customers": plan.total_customers,
                "total_bar_customers": plan.total_bar_customers,
                "delivery_date": plan.delivery_date,
            }

            optimization_results = await self._optimize_plan(plan)

            return {
                "success": True,
                "workflow_steps": {
                    "file_parsing": {"status": "completed", "info": file_info},
                    "ai_optimization": {"status": "completed", "results": optimization_results},
                },
                "final_results": {
                    "routes": {
                        "total_routes": plan.total_tours,
                        "route_headers": [tour.name for tour in plan.tours],
                        "categories": self._categorize_tours(plan.tours),
                    },
                    "customers": plan_dict.get("stats", {}),
                    "subtours": optimization_results.get("subtours", {}),
                    "tour_plan": plan_dict,
                    "total_processing_time": "N/A",
                },
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflow_steps": self._get_failed_workflow_state(str(e))
            }
    
    def _get_failed_workflow_state(self, error_message: str) -> Dict[str, Any]:
        """Gibt den Status der Workflow-Schritte bei Fehlern zurück"""
        return {
            "file_parsing": {"status": "unknown"},
            "ai_optimization": {"status": "unknown"},
            "error": error_message
        }
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung des Workflows zurück"""
        return {
            "total_modules": 6,
            "modules": [
                "File Parser Service",
                "AI Optimization Service",
                "Database Service",
                "Workflow Orchestrator"
            ],
            "workflow_flow": [
                "CSV → TourPlan",
                "Touren → KI-Optimierung",
                "KI-Ergebnisse → Datenbank",
                "Vollständige Tourenstruktur"
            ]
        }

    def _parse_input_to_plan(self, file_input: Union[str, Path, BytesIO], filename: Optional[str]) -> tuple[TourPlan, Dict[str, Any]]:
        if isinstance(file_input, BytesIO):
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
                file_input.seek(0)
                tmp.write(file_input.read())
                tmp_path = Path(tmp.name)
            try:
                plan = parse_tour_plan(tmp_path)
                plan_dict = parse_tour_plan_to_dict(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            plan = parse_tour_plan(file_input)
            plan_dict = parse_tour_plan_to_dict(file_input)
        return plan, plan_dict

    async def _optimize_plan(self, plan: TourPlan) -> Dict[str, Any]:
        subtours = {}
        for tour in plan.tours:
            if not tour.base_name.upper().startswith('W-'):
                continue
            # Kein Stop-Limit mehr - alle Touren werden optimiert (Zeit-Constraint wird im AI-Optimizer geprüft)
            # if len(tour.customers) <= default_rules.max_stops_per_tour:
            #     subtours[tour.name] = {
            #         "status": "no_optimization_needed",
            #         "original_customer_count": len(tour.customers),
            #     }
            #     continue
            stops = self._tour_to_stops(plan, tour)
            try:
                ai_result = await self.ai_optimizer.cluster_stops_into_tours(stops, default_rules)
                subtours[tour.name] = {
                    "status": "optimized",
                    "original_customer_count": len(tour.customers),
                    "ai_result": ai_result,
                    "subtours": ai_result.get("tours", []),
                }
            except Exception as exc:
                subtours[tour.name] = {
                    "status": "failed",
                    "error": str(exc),
                    "original_customer_count": len(tour.customers),
                }
        return {"subtours": subtours}

    def _tour_to_stops(self, plan: TourPlan, tour: TourInfo) -> List[Stop]:
        stops: List[Stop] = []
        for idx, stop in enumerate(tour.customers, start=1):
            lat = stop.get("lat") or default_rules.depot_lat
            lon = stop.get("lon") or default_rules.depot_lon
            stops.append(
                Stop(
                    id=f"{tour.name}_{idx}",
                    name=stop.get("name", "Unbekannter Kunde"),
                    address=f"{stop.get('street', '')}, {stop.get('postal_code', '')} {stop.get('city', '')}",
                    lat=lat,
                    lon=lon,
                )
            )
        return stops

    def _categorize_tours(self, tours: List[TourInfo]) -> Dict[str, List[str]]:
        categories = {"w_routes": [], "pir_routes": [], "t_routes": [], "other_routes": []}
        for tour in tours:
            route_type = tour.category.lower()
            if route_type.startswith("w"):
                categories["w_routes"].append(tour.name)
            elif route_type.startswith("pir"):
                categories["pir_routes"].append(tour.name)
            elif route_type in {"t", "anlief", "cb", "ta"}:
                categories["t_routes"].append(tour.name)
            else:
                categories["other_routes"].append(tour.name)
        return categories
