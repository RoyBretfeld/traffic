"""Domain models for the TrafficApp quick-start pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import List, Optional


@dataclass(frozen=True)
class Location:
    """Geographic position represented by latitude and longitude."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class TimeWindow:
    """Represents a service time window for a customer."""

    start: time
    end: time

    @property
    def duration(self) -> timedelta:
        """Return the width of the time window as a ``timedelta``."""

        start_dt = datetime.combine(datetime.today(), self.start)
        end_dt = datetime.combine(datetime.today(), self.end)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        return end_dt - start_dt


@dataclass(frozen=True)
class Customer:
    """Customer stop information."""

    customer_id: str
    name: str
    address: str
    location: Optional[Location]
    service_minutes: int
    time_window: Optional[TimeWindow] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Tour:
    """A planned tour containing a list of customers."""

    identifier: str
    customers: List[Customer] = field(default_factory=list)
    total_service_minutes: float = 0.0
    total_travel_minutes: float = 0.0

    def add_customer(
        self,
        customer: Customer,
        additional_service_minutes: float,
        additional_travel_minutes: float,
    ) -> None:
        """Append a customer and update statistics."""

        self.customers.append(customer)
        self.total_service_minutes += additional_service_minutes
        self.total_travel_minutes += additional_travel_minutes

    @property
    def total_minutes(self) -> float:
        """Return total minutes spent on the tour (travel + service)."""

        return self.total_service_minutes + self.total_travel_minutes

    @property
    def num_stops(self) -> int:
        """Number of customers within the tour."""

        return len(self.customers)

    def to_dict(self) -> dict:
        """Return a JSON serialisable representation of the tour."""

        return {
            "tour_id": self.identifier,
            "num_stops": self.num_stops,
            "total_minutes": round(self.total_minutes, 2),
            "total_service_minutes": round(self.total_service_minutes, 2),
            "total_travel_minutes": round(self.total_travel_minutes, 2),
            "stops": [
                {
                    "customer_id": c.customer_id,
                    "name": c.name,
                    "address": c.address,
                    "latitude": c.location.latitude if c.location else None,
                    "longitude": c.location.longitude if c.location else None,
                    "service_minutes": c.service_minutes,
                    "time_window": (
                        {
                            "start": c.time_window.start.isoformat(),
                            "end": c.time_window.end.isoformat(),
                        }
                        if c.time_window
                        else None
                    ),
                    "metadata": c.metadata,
                }
                for c in self.customers
            ],
        }
