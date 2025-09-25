from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from traffic.geocoding import SQLiteGeocoder, StaticProvider
from traffic.pipeline import build_tours_from_csv


SAMPLE_ROWS = [
    {
        "customer_id": "C1",
        "name": "Autohaus Mitte",
        "address": "Löbtauer Str. 25",
        "latitude": 51.0471,
        "longitude": 13.7124,
        "service_minutes": 15,
        "time_window_start": "08:00",
        "time_window_end": "08:30",
    },
    {
        "customer_id": "C2",
        "name": "Kundenservice Süd",
        "address": "Stadtgutstr. 9",
        "latitude": 51.0115,
        "longitude": 13.7177,
        "service_minutes": 20,
        "time_window_start": "09:00",
        "time_window_end": "09:45",
    },
    {
        "customer_id": "C3",
        "name": "Baustelle West",
        "address": "Kesselsdorfer Str. 312",
        "latitude": 51.0389,
        "longitude": 13.6675,
        "service_minutes": 15,
        "time_window_start": "10:00",
        "time_window_end": "10:45",
    },
]


def test_pipeline_creates_expected_artifacts(tmp_path: Path) -> None:
    csv_path = tmp_path / "customers.csv"
    pd.DataFrame(SAMPLE_ROWS).to_csv(csv_path, index=False)

    result = build_tours_from_csv(csv_path, tmp_path)

    assert result.json_file.exists()
    assert result.map_file.exists()
    assert result.summary_file.exists()

    with result.json_file.open("r", encoding="utf-8") as fh:
        tours = json.load(fh)
    assert len(tours) >= 1
    for tour in tours:
        assert tour["total_minutes"] <= 61  # planner enforces 60 min limit with small buffer
        assert tour["num_stops"] == len(tour["stops"]) if "num_stops" in tour else True

    summary_df = pd.read_csv(result.summary_file)
    assert not summary_df.empty
    assert {"tour_id", "total_minutes"}.issubset(summary_df.columns)


def test_sqlite_geocoder_uses_cache(tmp_path: Path) -> None:
    db_path = tmp_path / "geo.sqlite"
    provider = StaticProvider({"Teststraße 1": (51.0, 13.0)})
    geocoder = SQLiteGeocoder(db_path, provider=provider)

    location = geocoder.geocode("Teststraße 1")
    assert location is not None
    assert location.latitude == 51.0
    assert location.longitude == 13.0

    # Remove provider and fetch again to ensure caching works
    cached_only = SQLiteGeocoder(db_path, provider=None)
    cached_location = cached_only.geocode("Teststraße 1")
    assert cached_location is not None
    assert cached_location.latitude == 51.0
    assert cached_location.longitude == 13.0
