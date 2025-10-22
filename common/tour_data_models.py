from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import re

TIME_PATTERN = re.compile(r"(\d{1,2})[.:](\d{2})")
TOUR_CODE_PATTERN = re.compile(r"T(\d+)")

# Einige Tourenplan-Dateien enthalten Windows-1250/437-Bytes, die beim Lesen
# als latin1 zu falschen Zeichen führen (z. B. "Fr\x94belstra\xe1e").
# Diese Zuordnung ersetzt die problematischen Zeichen systemweit.
BROKEN_CHAR_TRANSLATION = str.maketrans(
    {
        "\x81": "ü",
        "\x84": "ä",
        "\x94": "ö",
        "\x99": "Ö",
        "\xe1": "ß",
    }
)

def _fix_broken_chars(text: str) -> str:
    if not text:
        return ""
    return text.translate(BROKEN_CHAR_TRANSLATION)

@dataclass
class TourStop:
    customer_number: str
    name: str
    street: str
    postal_code: str
    city: str
    is_bar_stop: bool


@dataclass
class TourInfo:
    name: str
    base_name: str
    category: str
    time_label: Optional[str]
    tour_code: Optional[str]
    is_bar_tour: bool
    customers: List[TourStop]

    @staticmethod
    def get_base_name(header: str) -> str:
        """Extrahiert den Basisnamen einer Tour aus dem Header-String.
        Entfernt Zeitangaben, Tour-Codes und BAR/ANLIEF-Marker.
        """
        name = _fix_broken_chars(header)
        # Entferne Zeitangaben (z.B. W-07.00 Uhr)
        name = TIME_PATTERN.sub('', name)
        # Entferne Tour-Codes (z.B. T123)
        name = TOUR_CODE_PATTERN.sub('', name)
        # Entferne BAR, ANLIEF, TOUR
        name = re.sub(r'\b(BAR|ANLIEF|TOUR|UHR)\b', '', name, flags=re.IGNORECASE)
        return " ".join(name.split()).strip()


@dataclass
class TourPlan:
    source_file: str
    delivery_date: Optional[str]
    tours: List[TourInfo]

    @property
    def total_tours(self) -> int:
        return len(self.tours)

    @property
    def total_customers(self) -> int:
        return sum(len(tour.customers) for tour in self.tours)

    @property
    def total_bar_customers(self) -> int:
        return sum(1 for tour in self.tours for stop in tour.customers if stop.is_bar_stop)


def _parse_delivery_date(raw_text: str) -> Optional[str]:
    match = re.search(r"Lieferdatum:\s*(\d{2})\.(\d{2})\.(\d{2})", raw_text)
    if not match:
        return None
    day, month, year = match.groups()
    # Jahr zweistellig → 20xx
    return f"20{year}-{month}-{day}"


def _parse_time_label(header: str) -> Optional[str]:
    match = TIME_PATTERN.search(header)
    if not match:
        return None
    hour, minute = match.groups()
    return f"{int(hour):02d}:{minute}"


def _parse_category(header: str) -> str:
    upper = header.upper()
    if upper.startswith("W-"):
        return "W"
    if upper.startswith("PIR"):
        return "PIR"
    if upper.startswith("CB"):
        return "CB"
    if upper.startswith("TA"):
        return "TA"
    if "ANLIEF" in upper:
        return "ANLIEF"
    return "OTHER"


def _parse_tour_header(header: str) -> Tuple[str, str, Optional[str], Optional[str], bool]:
    base_name = TourInfo.get_base_name(header)
    category = _parse_category(header)
    time_label = _parse_time_label(header)
    tour_code_match = TOUR_CODE_PATTERN.search(header)
    tour_code = tour_code_match.group(1) if tour_code_match else None
    is_bar = "BAR" in header.upper()
    return base_name, category, time_label, tour_code, is_bar
