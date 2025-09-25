"""Geocoding helpers with SQLite caching."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator, Optional, Protocol, Tuple

from .models import Location

try:  # pragma: no cover - optional dependency during runtime
    from geopy.geocoders import Nominatim
except Exception:  # pragma: no cover - geopy may be unavailable in tests
    Nominatim = None


class GeocodeProvider(Protocol):
    """Protocol describing a geocode provider."""

    def geocode(self, query: str) -> Optional[Tuple[float, float]]:
        ...


@dataclass
class NominatimProvider:
    """Thin wrapper around :class:`geopy.geocoders.Nominatim`."""

    user_agent: str = "traffic-app"

    def __post_init__(self) -> None:  # pragma: no cover - simple wiring
        if Nominatim is None:
            raise RuntimeError("geopy is not available. Install it to use NominatimProvider.")
        self._client = Nominatim(user_agent=self.user_agent, timeout=10)

    def geocode(self, query: str) -> Optional[Tuple[float, float]]:
        location = self._client.geocode(query)
        if location is None:
            return None
        return float(location.latitude), float(location.longitude)


@dataclass
class StaticProvider:
    """Simple provider that reads coordinates from a supplied mapping."""

    mapping: dict

    def geocode(self, query: str) -> Optional[Tuple[float, float]]:
        return self.mapping.get(query)


class SQLiteGeocoder:
    """SQLite-backed geocoder cache."""

    def __init__(self, db_path: Path, provider: Optional[GeocodeProvider] = None) -> None:
        self.db_path = Path(db_path)
        self.provider = provider
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS geocodes (
                    address TEXT PRIMARY KEY,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _lookup_cache(self, address: str) -> Optional[Location]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT latitude, longitude FROM geocodes WHERE address = ?",
                (address,),
            ).fetchone()
        if row:
            return Location(latitude=row[0], longitude=row[1])
        return None

    def _store_cache(self, address: str, location: Location) -> None:
        with self._connection() as conn:
            conn.execute(
                "REPLACE INTO geocodes(address, latitude, longitude, updated_at) VALUES (?, ?, ?, ?)",
                (
                    address,
                    location.latitude,
                    location.longitude,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()

    def geocode(self, address: str) -> Optional[Location]:
        """Return the coordinates for an address using cache + provider."""

        cached = self._lookup_cache(address)
        if cached:
            return cached
        if self.provider is None:
            return None
        result = self.provider.geocode(address)
        if result is None:
            return None
        location = Location(latitude=result[0], longitude=result[1])
        self._store_cache(address, location)
        return location
