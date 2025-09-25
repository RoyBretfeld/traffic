"""Command line interface for the TrafficApp quick-start pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .geocoding import NominatimProvider, SQLiteGeocoder
from .pipeline import build_tours_from_csv
from .tour_planner import PlanningConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TrafficApp CSV → Tour planner")
    parser.add_argument("csv", type=Path, help="Path to the input CSV file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where artifacts (JSON, map, summary) will be stored",
    )
    parser.add_argument(
        "--use-nominatim",
        action="store_true",
        help="Enable online geocoding via OpenStreetMap Nominatim (requires internet).",
    )
    parser.add_argument(
        "--tour-limit",
        type=float,
        default=None,
        help="Override the maximum duration per tour in minutes (default 60).",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="Override the assumed travel speed in km/h (default 35).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    provider = NominatimProvider() if args.use_nominatim else None
    geocoder = SQLiteGeocoder(args.output_dir / "geocache.sqlite", provider=provider)

    planning_kwargs = {}
    if args.tour_limit is not None:
        planning_kwargs["tour_limit_minutes"] = args.tour_limit
    if args.speed is not None:
        planning_kwargs["travel_speed_kmh"] = args.speed
    config = PlanningConfig(**planning_kwargs) if planning_kwargs else None

    result = build_tours_from_csv(args.csv, args.output_dir, geocoder=geocoder, planning_config=config)

    print(f"Tours written to {result.json_file}")
    print(f"Summary written to {result.summary_file}")
    print(f"Map written to {result.map_file}")


if __name__ == "__main__":
    main()
