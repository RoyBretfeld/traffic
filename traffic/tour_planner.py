"""Heuristic tour planner for the quick-start workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from . import constants
from .distance import haversine_km
from .models import Customer, Location, Tour


@dataclass
class PlanningConfig:
    """Configuration for tour planning heuristics."""

    tour_limit_minutes: float = constants.DEFAULT_TOUR_LIMIT_MINUTES
    travel_speed_kmh: float = constants.DEFAULT_TRAVEL_SPEED_KMH
    service_buffer_minutes: float = constants.DEFAULT_SERVICE_BUFFER_MINUTES


class TourPlanner:
    """Plan tours using a greedy heuristic with duration constraints."""

    def __init__(self, depot: Location, config: PlanningConfig | None = None) -> None:
        self.depot = depot
        self.config = config or PlanningConfig()

    def _estimate_travel_minutes(self, locations: List[Location]) -> float:
        """Approximate travel time for the route visiting the given locations."""

        if not locations:
            return 0.0
        total_km = 0.0
        previous = self.depot
        for loc in locations:
            total_km += haversine_km(previous, loc)
            previous = loc
        total_km += haversine_km(previous, self.depot)
        if self.config.travel_speed_kmh <= 0:
            raise ValueError("Travel speed must be positive.")
        return (total_km / self.config.travel_speed_kmh) * 60

    def _estimate_tour_minutes(self, customers: Iterable[Customer]) -> float:
        locations = []
        for customer in customers:
            if customer.location is None:
                raise ValueError(f"Customer {customer.customer_id} lacks coordinates.")
            locations.append(customer.location)
        travel_minutes = self._estimate_travel_minutes(locations)
        service_minutes = sum(c.service_minutes + self.config.service_buffer_minutes for c in customers)
        return travel_minutes + service_minutes

    def plan(self, customers: List[Customer]) -> List[Tour]:
        """Return tours that satisfy the configured duration limit."""

        tours: List[Tour] = []
        sorted_customers = sorted(
            customers,
            key=lambda c: (
                c.time_window.start if c.time_window else datetime.min.time(),
                c.customer_id,
            ),
        )
        for customer in sorted_customers:
            added = False
            if customer.location is None:
                raise ValueError(f"Customer {customer.customer_id} lacks coordinates.")
            for tour in tours:
                new_customers = tour.customers + [customer]
                if self._estimate_tour_minutes(new_customers) <= self.config.tour_limit_minutes:
                    additional_service = customer.service_minutes + self.config.service_buffer_minutes
                    temp_locations = [c.location for c in new_customers if c.location is not None]
                    travel_minutes = self._estimate_travel_minutes(temp_locations)
                    tour.total_travel_minutes = travel_minutes
                    tour.add_customer(customer, additional_service, 0.0)
                    added = True
                    break
            if not added:
                identifier = f"W{len(tours) + 1}"
                base_service = customer.service_minutes + self.config.service_buffer_minutes
                travel_minutes = self._estimate_travel_minutes([customer.location])
                tour = Tour(identifier=identifier)
                tour.total_travel_minutes = travel_minutes
                tour.add_customer(customer, base_service, 0.0)
                tours.append(tour)

        # Final pass to recompute travel minutes accurately for each tour.
        for tour in tours:
            tour.total_travel_minutes = self._estimate_travel_minutes(
                [c.location for c in tour.customers if c.location is not None]
            )
        return tours
