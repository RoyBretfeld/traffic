"""Modernisierter Tourenplan-Parser basierend auf den Skripten
`parse_w7.py` und `parse_all_tours.py` aus `docs/Neu`.

Der Parser liest eine Tourenplan-CSV (wie von TEHA exportiert), ordnet
alle Touren inklusive BAR-Sektionen korrekt zu und liefert eine
strukturierte Datendarstellung, die als Grundlage für Geocoding,
Routing und UI-Ausgabe dient.
"""

from __future__ import annotations

import csv
import io
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from common.normalize import normalize_address

def _heuristic_decode(raw: bytes) -> tuple[str, str]:
    """Heuristische Dekodierung mit Encoding-Erkennung."""
    for enc in ("cp850", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8*replace"
from typing import Dict, Iterable, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


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


def _read_csv_lines(file_path: Union[str, Path]) -> Iterable[List[str]]:
    """DEPRECATED: Verwende ingest.csv_reader.read_csv_unified() stattdessen"""
    from ingest.csv_reader import read_csv_unified
    
    # Verwende den zentralen CSV-Reader
    df = read_csv_unified(file_path, sep=';', header=None, dtype=str)
    
    # Konvertiere DataFrame zu Iterable[List[str]]
    for _, row in df.iterrows():
        yield row.tolist()


def _normalize(text: str) -> str:
    if not text:
        return ""
    text = _fix_broken_chars(text)
    text = text.strip()
    return re.sub(r"\s+", " ", text)


def _unify_route_name(name: str) -> str:
    name = _fix_broken_chars(name)
    cleaned = re.sub(r"\b(BAR|Tour|Uhr)\b", "", name, flags=re.IGNORECASE)
    return " ".join(cleaned.split()).strip()


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
    base_name = _unify_route_name(header)
    category = _parse_category(header)
    time_label = _parse_time_label(header)
    tour_code_match = TOUR_CODE_PATTERN.search(header)
    tour_code = tour_code_match.group(1) if tour_code_match else None
    is_bar = "BAR" in header.upper()
    return base_name, category, time_label, tour_code, is_bar


# ---------------------------------------------------------------------------
# Hauptlogik (portiert aus parse_w7.py)
# ---------------------------------------------------------------------------


def _extract_tours(file_path: Union[str, Path]) -> Tuple[List[str], Dict[str, List[TourStop]]]:
    tours: "OrderedDict[str, List[TourStop]]" = OrderedDict()
    pending_bar: Dict[str, List[TourStop]] = {}
    full_name_map: Dict[str, str] = {}
    order: List[str] = []

    current_base: Optional[str] = None
    current_header: Optional[str] = None
    bar_mode = False

    for row in _read_csv_lines(file_path):
        if not any(row):
            continue

        first_cell = str(row[0]).strip() if len(row) > 0 and row[0] is not None and str(row[0]) != 'nan' else ""
        header_cell = str(row[1]).strip() if len(row) > 1 and row[1] is not None and str(row[1]) != 'nan' else ""

        # Tour-Header-Zeilen beginnen mit leerem ersten Feld
        if not first_cell and header_cell:
            header = header_cell
            base = _unify_route_name(header)
            if "BAR" in header.upper():
                bar_mode = True
                current_base = base
                current_header = header
                pending_bar.setdefault(base, [])
            else:
                bar_mode = False
                current_base = base
                current_header = header
                full_name_map[base] = header
                if header not in tours:
                    tours[header] = []
                    order.append(header)
                if base in pending_bar and pending_bar[base]:
                    tours[header].extend(pending_bar.pop(base))
            continue

        if not current_base:
            continue  # außerhalb eines Tour-Blocks

        if not first_cell.isdigit():
            continue  # keine Kundenzeile

        name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        street = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        postal_code = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        city = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""

        customer = TourStop(
            customer_number=first_cell,
            name=_normalize(name),
            street=_normalize(street),
            postal_code=postal_code,
            city=_normalize(city),
            is_bar_stop=bar_mode,
        )

        if bar_mode:
            pending_bar.setdefault(current_base, []).append(customer)
        else:
            header = full_name_map.get(current_base, current_header or current_base)
            if header not in tours:
                tours[header] = []
                order.append(header)
            tours[header].append(customer)

    # Restliche BAR-Einträge anhängen, wenn keine passende Haupttour gefunden wurde
    for base, customers in pending_bar.items():
        if not customers:
            continue
        header = full_name_map.get(base, base)
        if header not in tours:
            tours[header] = []
            order.append(header)
        tours[header].extend(customers)

    return order, tours


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def parse_tour_plan(file_path: Union[str, Path]) -> TourPlan:
    path = Path(file_path)
    # Kopf der Datei mit Heuristik lesen (Umlaute sicher)
    raw = path.read_bytes()
    raw_text, _enc = _heuristic_decode(raw)
    delivery_date = _parse_delivery_date(raw_text[:4000])  # nur Kopf scannen

    order, tour_map = _extract_tours(path)

    tours: List[TourInfo] = []
    for header in order:
        stops = tour_map.get(header, [])
        if not stops:
            continue
        base_name, category, time_label, tour_code, is_bar = _parse_tour_header(header)
        tours.append(
            TourInfo(
                name=header,
                base_name=base_name,
                category=category,
                time_label=time_label,
                tour_code=tour_code,
                is_bar_tour=is_bar,
                customers=stops,
            )
        )

    return TourPlan(source_file=path.name, delivery_date=delivery_date, tours=tours)


def tour_plan_to_dict(plan: TourPlan) -> Dict[str, object]:
    tours_payload: List[Dict[str, object]] = []
    all_customers: List[Dict[str, object]] = []
    global_seen: set = set()

    for tour in plan.tours:
        seen_local: set = set()
        customers_payload: List[Dict[str, object]] = []
        for stop in tour.customers:
            key = (stop.customer_number, stop.name, stop.street, stop.postal_code, stop.city)
            if key in seen_local:
                continue
            seen_local.add(key)
            customer_dict = {
                "customer_number": stop.customer_number,
                "kdnr": stop.customer_number,
                "name": stop.name,
                "street": stop.street,
                "postal_code": stop.postal_code,
                "city": stop.city,
                "bar_flag": stop.is_bar_stop,
                "address": normalize_address(f"{stop.street}, {stop.postal_code} {stop.city}", stop.name, stop.postal_code),
            }
            customers_payload.append(customer_dict)

            global_key = key + (tour.name,)
            if global_key not in global_seen:
                global_seen.add(global_key)
                all_customers.append(
                    {
                        **customer_dict,
                        "tour_name": tour.name,
                        "tour_type": tour.category,
                        "tour_time": tour.time_label,
                        "tour_code": tour.tour_code,
                        "is_bar_tour": tour.is_bar_tour,
                    }
                )

        tours_payload.append(
            {
                "name": tour.name,
                "base_name": tour.base_name,
                "tour_type": tour.category,
                "time": tour.time_label,
                "tour_code": tour.tour_code,
                "is_bar_tour": tour.is_bar_tour,
                "customers": customers_payload,
                "customer_count": len(customers_payload),
                "bar_customer_count": sum(1 for c in customers_payload if c["bar_flag"]),
            }
        )

    stats = {
        "total_tours": len(tours_payload),
        "total_customers": len(all_customers),
        "total_bar_customers": sum(1 for c in all_customers if c["bar_flag"]),
    }

    return {
        "metadata": {
            "source_file": plan.source_file,
            "delivery_date": plan.delivery_date,
        },
        "tours": tours_payload,
        "customers": all_customers,
        "stats": stats,
    }


def parse_tour_plan_to_dict(file_path: Union[str, Path]) -> Dict[str, object]:
    return tour_plan_to_dict(parse_tour_plan(file_path))


def export_tour_plan_markdown(plan: TourPlan, output_path: Union[str, Path]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Alle Touren mit Kundennummern\n\n")
        for tour in plan.tours:
            handle.write(f"## {tour.name}\n\n")
            handle.write("| KdNr | Name | Straße | PLZ | Ort | Bar |\n")
            handle.write("|---|---|---|---|---|---|\n")
            seen: set = set()
            for stop in tour.customers:
                key = (stop.customer_number, stop.name, stop.street, stop.postal_code, stop.city)
                if key in seen:
                    continue
                seen.add(key)
                handle.write(
                    f"| {stop.customer_number} | {stop.name} | {stop.street} | {stop.postal_code} | {stop.city} | {'yes' if stop.is_bar_stop else 'no'} |\n"
                )
            handle.write("\n\n")


__all__ = [
    "TourStop",
    "TourInfo",
    "TourPlan",
    "tour_plan_to_dict",
    "parse_tour_plan",
    "parse_tour_plan_to_dict",
    "export_tour_plan_markdown",
]

