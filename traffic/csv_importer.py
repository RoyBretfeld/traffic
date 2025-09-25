"""CSV importer for TrafficApp customers."""

from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from .models import Customer, Location, TimeWindow


REQUIRED_COLUMNS = {
    "customer_id",
    "name",
    "address",
    "service_minutes",
}
OPTIONAL_COLUMNS = {"time_window_start", "time_window_end", "latitude", "longitude"}


def _parse_time(value: object) -> Optional[time]:
    """Parse a value into a :class:`datetime.time` if possible."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # Accept ``HH:MM`` or ``HH:MM:SS``.
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
    raise ValueError(f"Unsupported time format: {value!r}")


def _require_columns(columns: Iterable[str]) -> None:
    missing = REQUIRED_COLUMNS.difference(columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")


def load_customers_from_csv(csv_path: Path) -> List[Customer]:
    """Load customers from a CSV file into :class:`Customer` instances."""

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    _require_columns(df.columns)

    customers: List[Customer] = []
    for row in df.itertuples(index=False):
        row_dict = row._asdict()
        lat = row_dict.get("latitude")
        lon = row_dict.get("longitude")
        location: Optional[Location]
        if pd.isna(lat) or pd.isna(lon):
            location = None
        else:
            location = Location(latitude=float(lat), longitude=float(lon))

        start_time = _parse_time(row_dict.get("time_window_start"))
        end_time = _parse_time(row_dict.get("time_window_end"))
        time_window = None
        if start_time and end_time:
            time_window = TimeWindow(start=start_time, end=end_time)

        customer = Customer(
            customer_id=str(row_dict["customer_id"]),
            name=str(row_dict["name"]),
            address=str(row_dict["address"]),
            location=location,
            service_minutes=int(row_dict["service_minutes"]),
            time_window=time_window,
            metadata={k: row_dict[k] for k in row_dict if k not in REQUIRED_COLUMNS | OPTIONAL_COLUMNS},
        )
        customers.append(customer)
    return customers
