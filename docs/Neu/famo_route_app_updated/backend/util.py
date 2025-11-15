"""
Utility functions for the FAMO traffic routing application.

This module contains functions to read and parse CSV files
containing customer data, normalise German characters to ASCII,
deduplicate entries, and compute simple route clustering and ordering
without relying on external services.

The clustering logic uses a simple sweep heuristic, grouping customers
around the depot based on polar angle until a time budget is reached.

Note: This code is designed to run offline. Geocoding is not
performed here; callers should provide latitude/longitude for each
customer if available. If not provided, a dummy coordinate can be
supplied to allow the algorithms to run, but the results will not
represent real-world distances.
"""

import csv
import math
import unicodedata
from typing import List, Dict, Tuple, Optional


def normalise_address(text: str) -> str:
    """Normalise German address strings to ASCII.

    - Replaces German umlauts (ä, ö, ü, Ä, Ö, Ü) with ae, oe, ue.
    - Replaces ß with ss.
    - Performs Unicode normalisation (NFKD) and removes diacritics.

    Args:
        text: The input string.

    Returns:
        A normalised ASCII string.
    """
    if not text:
        return text
    replacements = {
        "ä": "ae",
        "Ä": "Ae",
        "ö": "oe",
        "Ö": "Oe",
        "ü": "ue",
        "Ü": "Ue",
        "ß": "ss",
    }
    for original, repl in replacements.items():
        text = text.replace(original, repl)
    # Decompose unicode characters and remove combining marks
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def parse_csv(file_path: str) -> List[Dict[str, str]]:
    """Parse a CSV file containing customer data.

    The CSV is expected to have the following columns (in any order):
    - KdNr: customer number
    - Name: company or customer name
    - Strasse: street name and house number
    - PLZ: postal code
    - Ort: city
    - Tour: route name or time slot
    - Bar: optional flag indicating a cash customer (case-insensitive: 'BAR')

    If a row's "Bar" column contains a truthy value (e.g. 'BAR'), the row
    is marked with `bar=True`. Otherwise, it defaults to False.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A list of dictionaries representing customers.
    """
    customers: List[Dict[str, str]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalise keys to consistent names
            kdnr = row.get("KdNr") or row.get("Kdnr") or row.get("KundenNr") or row.get("Kundennummer")
            name = row.get("Name") or row.get("Firma") or row.get("Kundenname")
            street = row.get("Strasse") or row.get("Straße") or row.get("Straße ")
            plz = row.get("PLZ") or row.get("Postleitzahl")
            city = row.get("Ort") or row.get("Stadt")
            tour = row.get("Tour") or row.get("Route") or row.get("Tourname")
            bar_field = (row.get("Bar") or row.get("Beistellung") or row.get("Vorlauf") or "").strip().upper()
            bar = bar_field == "BAR"
            # Also capture latitude/longitude if provided in columns
            lat_str = (row.get("lat") or row.get("latitude") or "").strip()
            lon_str = (row.get("lon") or row.get("longitude") or "").strip()
            lat = None
            lon = None
            try:
                if lat_str:
                    lat = float(lat_str)
                if lon_str:
                    lon = float(lon_str)
            except Exception:
                lat = None
                lon = None
            customers.append(
                {
                    "kdnr": (kdnr or "").strip(),
                    "name": (name or "").strip(),
                    "street": (street or "").strip(),
                    "plz": (plz or "").strip(),
                    "city": (city or "").strip(),
                    "tour": (tour or "").strip(),
                    "bar": bar,
                    "lat": lat,
                    "lon": lon,
                }
            )
    return customers


def merge_bar_rows(customers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Merge rows marked as 'BAR' with the next non-BAR row of the same tour.

    This function assumes that the input list `customers` is ordered as in the
    original CSV. When a customer with `bar=True` is encountered, it is not
    removed; instead, it remains in the list, but its `merged` flag indicates
    that it belongs to the next customer with the same tour. This preserves
    the record for cash customers while associating them with the primary
    tour for clustering purposes.

    Args:
        customers: List of customer dictionaries with a boolean `bar` field.

    Returns:
        A new list of customer dictionaries with an added `merged` field.
    """
    result = []
    next_primary_tour: Optional[str] = None
    for cust in customers:
        cust_copy = cust.copy()
        cust_copy["merged"] = False
        if cust_copy["bar"]:
            # mark this row to be merged with the following non-BAR row
            next_primary_tour = cust_copy["tour"]
            cust_copy["merged"] = True
        else:
            # if previous BAR row existed, ensure tour names match
            if next_primary_tour and cust_copy["tour"] != next_primary_tour:
                # reset if mismatch
                next_primary_tour = None
            # attach previous bar rows to this row implicitly
            next_primary_tour = None
        result.append(cust_copy)
    return result


def deduplicate_customers(customers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate customer entries based on address and customer number.

    Customers are considered duplicates if they have the same street, postal
    code and city (case-insensitive) and identical customer numbers. When
    duplicates are found, only the first occurrence is kept.

    Args:
        customers: List of customer dictionaries.

    Returns:
        A list of unique customers.
    """
    seen_keys = set()
    unique: List[Dict[str, str]] = []
    for cust in customers:
        key = (cust["kdnr"].lower(), cust["street"].lower(), cust["plz"], cust["city"].lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(cust)
    return unique


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance between two points on the Earth.

    Uses the Haversine formula to calculate the distance in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def compute_travel_time(distance_km: float, speed_kmh: float = 50.0) -> float:
    """Estimate travel time in minutes given distance and average speed.

    Args:
        distance_km: The distance in kilometers.
        speed_kmh: Assumed average speed in km/h.

    Returns:
        Estimated travel time in minutes.
    """
    if speed_kmh <= 0:
        return 0.0
    hours = distance_km / speed_kmh
    return hours * 60.0


def build_time_matrix(locations: List[Tuple[float, float]]) -> List[List[float]]:
    """Build a symmetric time matrix (minutes) using haversine distances.

    The time matrix includes travel time between all pairs of locations. The
    diagonal entries are zero.

    Args:
        locations: A list of (lat, lon) tuples.

    Returns:
        A matrix of travel times in minutes.
    """
    n = len(locations)
    matrix: List[List[float]] = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine(locations[i][0], locations[i][1], locations[j][0], locations[j][1])
            time_min = compute_travel_time(dist)
            matrix[i][j] = time_min
            matrix[j][i] = time_min
    return matrix


def compute_angles(depot: Tuple[float, float], locs: List[Tuple[float, float]]) -> List[float]:
    """Compute the polar angle of each location relative to the depot.

    The angle is measured in radians from the east axis counterclockwise.

    Args:
        depot: (lat, lon) coordinates of the depot.
        locs: List of customer (lat, lon) pairs.

    Returns:
        List of angles in radians.
    """
    angles = []
    for lat, lon in locs:
        dx = lon - depot[1]
        dy = lat - depot[0]
        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2 * math.pi
        angles.append(angle)
    return angles


def cluster_customers(
    depot: Tuple[float, float],
    customers: List[Dict[str, any]],
    service_time_min: float = 2.0,
    max_route_time_min: float = 60.0,
) -> List[List[int]]:
    """Cluster customers into tours using a sweep heuristic with time budget.

    Args:
        depot: (lat, lon) coordinates of the starting point.
        customers: List of customer dictionaries with 'lat' and 'lon' fields.
        service_time_min: Fixed dwell time per customer in minutes.
        max_route_time_min: Maximum allowed travel time until the last customer.

    Returns:
        A list of clusters, each containing indices into the `customers` list.
    """
    # Extract coordinates
    coords = [(c["lat"], c["lon"]) for c in customers]
    angles = compute_angles(depot, coords)
    # Sort customers by angle around the depot
    sorted_indices = sorted(range(len(customers)), key=lambda i: angles[i])
    # Precompute time from depot to each customer
    times_from_depot = []
    for idx in range(len(customers)):
        dist = haversine(depot[0], depot[1], coords[idx][0], coords[idx][1])
        times_from_depot.append(compute_travel_time(dist))
    # Build clusters
    clusters: List[List[int]] = []
    current_cluster: List[int] = []
    current_time = 0.0
    for idx in sorted_indices:
        travel_time = times_from_depot[idx]
        # Starting a new cluster? Reset time to travel from depot
        if not current_cluster:
            current_time = travel_time
        else:
            # If continuing an existing cluster, estimate additional time from last customer
            last_idx = current_cluster[-1]
            dist_between = haversine(
                coords[last_idx][0], coords[last_idx][1], coords[idx][0], coords[idx][1]
            )
            travel_time = compute_travel_time(dist_between)
            current_time += travel_time
        # Add service time
        current_time += service_time_min
        # If adding this customer exceeds the time limit, start new cluster
        if current_time > max_route_time_min and current_cluster:
            clusters.append(current_cluster)
            current_cluster = [idx]
            current_time = times_from_depot[idx] + service_time_min
        else:
            current_cluster.append(idx)
    if current_cluster:
        clusters.append(current_cluster)
    return clusters


def nearest_neighbor_order(
    depot: Tuple[float, float], customers: List[Dict[str, any]], cluster_indices: List[int], service_time_min: float = 2.0
) -> List[int]:
    """Order a cluster using a nearest neighbor heuristic.

    Args:
        depot: (lat, lon) coordinates of the start.
        customers: List of customers with 'lat' and 'lon'.
        cluster_indices: List of indices representing the cluster to order.
        service_time_min: Dwell time per customer (unused in ordering but kept for extensibility).

    Returns:
        The ordered list of indices representing the visit order.
    """
    if not cluster_indices:
        return []
    unvisited = set(cluster_indices)
    order: List[int] = []
    # Start at depot: find closest customer
    current_loc = depot
    while unvisited:
        next_idx = None
        min_dist = float("inf")
        for idx in unvisited:
            dist = haversine(current_loc[0], current_loc[1], customers[idx]["lat"], customers[idx]["lon"])
            if dist < min_dist:
                min_dist = dist
                next_idx = idx
        if next_idx is None:
            break
        order.append(next_idx)
        unvisited.remove(next_idx)
        current_loc = (customers[next_idx]["lat"], customers[next_idx]["lon"])
    return order


def compute_route_stats(
    depot: Tuple[float, float], customers: List[Dict[str, any]], route_indices: List[int], speed_kmh: float = 50.0, service_time_min: float = 2.0
) -> Dict[str, float]:
    """Compute statistics for a route.

    Args:
        depot: (lat, lon) coordinates of the starting point.
        customers: List of all customer dictionaries with 'lat' and 'lon'.
        route_indices: Ordered list of indices representing a tour.
        speed_kmh: Average speed for travel time estimation.
        service_time_min: Dwell time per customer in minutes.

    Returns:
        A dictionary with keys:
            - total_distance_km: Sum of distances between successive stops and from depot to first stop.
            - travel_time_min: Total travel time in minutes (without service time).
            - service_time_min: Total service time in minutes.
            - total_time_min: Travel time + service time.
            - num_stops: Number of customers in the route.
    """
    total_distance = 0.0
    total_service_time = service_time_min * len(route_indices)
    if not route_indices:
        return {
            "total_distance_km": 0.0,
            "travel_time_min": 0.0,
            "service_time_min": 0.0,
            "total_time_min": 0.0,
            "num_stops": 0,
        }
    # Distance from depot to first stop
    first = route_indices[0]
    total_distance += haversine(depot[0], depot[1], customers[first]["lat"], customers[first]["lon"])
    # Distances between successive stops
    for i in range(len(route_indices) - 1):
        a = route_indices[i]
        b = route_indices[i + 1]
        total_distance += haversine(
            customers[a]["lat"], customers[a]["lon"], customers[b]["lat"], customers[b]["lon"]
        )
    # Optionally add distance from last stop back to depot (commented out)
    # last = route_indices[-1]
    # total_distance += haversine(customers[last]["lat"], customers[last]["lon"], depot[0], depot[1])
    travel_time = compute_travel_time(total_distance, speed_kmh)
    total_time = travel_time + total_service_time
    return {
        "total_distance_km": total_distance,
        "travel_time_min": travel_time,
        "service_time_min": total_service_time,
        "total_time_min": total_time,
        "num_stops": len(route_indices),
    }