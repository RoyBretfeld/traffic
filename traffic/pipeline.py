"""High level CSV → tour pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from . import constants
from .csv_importer import load_customers_from_csv
from .geocoding import SQLiteGeocoder
from .map_renderer import MapRenderer
from .models import Customer, Location, Tour
from .tour_planner import PlanningConfig, TourPlanner


@dataclass
class PipelineResult:
    """Artifacts produced by the pipeline run."""

    tours: List[Tour]
    map_file: Path
    summary_file: Path
    json_file: Path


def _ensure_customer_locations(customers: Iterable[Customer], geocoder: SQLiteGeocoder) -> None:
    for customer in customers:
        if customer.location is not None:
            continue
        location = geocoder.geocode(customer.address)
        if location is None:
            raise ValueError(
                f"No coordinates available for '{customer.address}'. Provide latitude/longitude in the CSV "
                "or configure an online geocoder."
            )
        customer.metadata.setdefault("geocoded", True)
        # dataclasses are frozen -> replace via object.__setattr__
        object.__setattr__(customer, "location", location)


def _calculate_estimated_end_time(tour: Tour, start_time: Optional[datetime]) -> Optional[datetime]:
    if start_time is None:
        return None
    return start_time + timedelta(minutes=tour.total_minutes)


def _build_summary(tours: Iterable[Tour]) -> pd.DataFrame:
    records = []
    for tour in tours:
        if tour.customers and tour.customers[0].time_window:
            start_time = datetime.combine(
                datetime.today(),
                tour.customers[0].time_window.start,
            )
        else:
            start_time = None
        end_time = _calculate_estimated_end_time(tour, start_time)
        records.append(
            {
                "tour_id": tour.identifier,
                "num_stops": tour.num_stops,
                "travel_minutes": round(tour.total_travel_minutes, 2),
                "service_minutes": round(tour.total_service_minutes, 2),
                "total_minutes": round(tour.total_minutes, 2),
                "est_start": start_time.strftime("%H:%M") if start_time else "-",
                "est_end": end_time.strftime("%H:%M") if end_time else "-",
            }
        )
    return pd.DataFrame.from_records(records)


def build_tours_from_csv(
    csv_path: Path,
    output_dir: Path,
    geocoder: Optional[SQLiteGeocoder] = None,
    planning_config: Optional[PlanningConfig] = None,
) -> PipelineResult:
    """Run the full CSV → tours pipeline."""

    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    customers = load_customers_from_csv(csv_path)
    if not customers:
        raise ValueError("CSV contains no customers.")

    geocoder = geocoder or SQLiteGeocoder(output_dir / "geocache.sqlite")
    _ensure_customer_locations(customers, geocoder)

    depot = Location(latitude=constants.DEPOT_LATITUDE, longitude=constants.DEPOT_LONGITUDE)
    planner = TourPlanner(depot=depot, config=planning_config)
    tours = planner.plan(customers)

    json_file = output_dir / "tours.json"
    with json_file.open("w", encoding="utf-8") as fh:
        json.dump([tour.to_dict() for tour in tours], fh, ensure_ascii=False, indent=2)

    summary_df = _build_summary(tours)
    summary_file = output_dir / "tour_summary.csv"
    summary_df.to_csv(summary_file, index=False)

    map_renderer = MapRenderer(constants.DEPOT_LATITUDE, constants.DEPOT_LONGITUDE)
    map_file = output_dir / "tours_map.html"
    map_renderer.render(tours, map_file)

    return PipelineResult(tours=tours, map_file=map_file, summary_file=summary_file, json_file=json_file)
