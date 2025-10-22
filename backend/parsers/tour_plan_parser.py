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
from pathlib import Path
from common.normalize import normalize_address
import logging # Added for error logging
from typing import Dict, Iterable, List, Optional, Tuple, Union
from routes.upload_csv import _heuristic_decode # Importiere _heuristic_decode
from services.tour_plan_grouper import group_and_consolidate_tours # Importiere neue Gruppierungsfunktion
from common.tour_data_models import TourInfo, TourStop, TourPlan, _parse_delivery_date, _parse_tour_header, _fix_broken_chars # Importiere Datenstrukturen und Hilfsfunktionen

# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------


# Alle Datenstrukturen wurden nach common/tour_data_models.py verschoben

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


# Alle Hilfsfunktionen wurden nach common/tour_data_models.py verschoben oder sind über normalize_address zugänglich

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
    text = _fix_broken_chars(text) # Verwende die importierte Funktion
    text = text.strip()
    return re.sub(r"\s+", " ", text)


# def _unify_route_name(name: str) -> str: # Entfernt
#     name = _fix_broken_chars(name) # Entfernt
#     cleaned = re.sub(r"\b(BAR|Tour|Uhr)\b", "", name, flags=re.IGNORECASE) # Entfernt
#     return " ".join(cleaned.split()).strip() # Entfernt


# def _parse_delivery_date(raw_text: str) -> Optional[str]: # Entfernt
#     match = re.search(r"Lieferdatum:\s*(\d{2})\.(\d{2})\.(\d{2})", raw_text) # Entfernt
#     if not match: # Entfernt
#         return None # Entfernt
#     day, month, year = match.groups() # Entfernt
#     # Jahr zweistellig → 20xx # Entfernt
#     return f"20{year}-{month}-{day}" # Entfernt


# def _parse_time_label(header: str) -> Optional[str]: # Entfernt
#     match = TIME_PATTERN.search(header) # Entfernt
#     if not match: # Entfernt
#         return None # Entfernt
#     hour, minute = match.groups() # Entfernt
#     return f"{int(hour):02d}:{minute}" # Entfernt


# def _parse_category(header: str) -> str: # Entfernt
#     upper = header.upper() # Entfernt
#     if upper.startswith("W-"): # Entfernt
#         return "W" # Entfernt
#     if upper.startswith("PIR"): # Entfernt
#         return "PIR" # Entfernt
#     if upper.startswith("CB"): # Entfernt
#         return "CB" # Entfernt
#     if upper.startswith("TA"): # Entfernt
#         return "TA" # Entfernt
#     if "ANLIEF" in upper: # Entfernt
#         return "ANLIEF" # Entfernt
#     return "OTHER" # Entfernt


# def _parse_tour_header(header: str) -> Tuple[str, str, Optional[str], Optional[str], bool]: # Entfernt
#     base_name = TourInfo.get_base_name(header) # Entfernt
#     category = _parse_category(header) # Entfernt
#     time_label = _parse_time_label(header) # Entfernt
#     tour_code_match = TOUR_CODE_PATTERN.search(header) # Entfernt
#     tour_code = tour_code_match.group(1) if tour_code_match else None # Entfernt
#     is_bar = "BAR" in header.upper() # Entfernt
#     return base_name, category, time_label, tour_code, is_bar # Entfernt


# ---------------------------------------------------------------------------
# Hauptlogik (portiert aus parse_w7.py)
# ---------------------------------------------------------------------------


def _extract_tours(file_path: Union[str, Path]) -> Tuple[List[str], Dict[str, List[TourStop]]]:
    # Phase 1: Rohextraktion der Kunden und Header
    raw_tour_data: List[Tuple[str, TourStop]] = [] # (header_string, TourStop)
    headers_in_order: List[str] = []
    last_normal_header: Optional[str] = None
    
    for row in _read_csv_lines(file_path):
        if not any(row):
            continue
        
        first_cell = str(row[0]).strip() if len(row) > 0 and row[0] is not None and str(row[0]) != 'nan' else ""
        header_cell = str(row[1]).strip() if len(row) > 1 and row[1] is not None and str(row[1]) != 'nan' else ""
        
        if not first_cell and header_cell: # This is a header line
            header = header_cell
            headers_in_order.append(header)
            if TourInfo.get_base_name(header) not in ["BAR", "ANLIEF"]: # Nutze get_base_name zum Filtern
                last_normal_header = header
            continue
        
        if not first_cell.isdigit(): # Not a customer line
            continue

        # Skip customers before first normal tour header is seen
        if not last_normal_header and TourInfo.get_base_name(header_cell) not in ["BAR", "ANLIEF"]: # Auch hier get_base_name
            continue
        
        name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        street = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        postal_code = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        city = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
        
        is_bar_customer = "BAR" in header_cell.upper()

        customer = TourStop(
            customer_number=first_cell,
            name=_normalize(name),
            street=_normalize(street),
            postal_code=postal_code,
            city=_normalize(city),
            is_bar_stop=is_bar_customer
        )
        
        # Fügen Sie alle Kunden zur Rohextraktion hinzu, gruppierung erfolgt später
        if last_normal_header:
             raw_tour_data.append((last_normal_header, customer))
        elif is_bar_customer: # Fallback für BAR-Kunden ohne vorherige Haupttour
             raw_tour_data.append((header_cell, customer))
        else:
             logging.warning(f"[PARSER WARN] Kunde {customer.customer_number} konnte keiner Tour zugeordnet werden (kein Header gefunden).")

    # Phase 2 & 3: Gruppierung und Konsolidierung durch den Grouper-Service
    grouped_tours_as_maps = group_and_consolidate_tours(raw_tour_data)

    # Konvertiere die Maps zurück in das erwartete Format (order, tour_map)
    order = []
    tour_map = OrderedDict()
    for tour_map_entry in grouped_tours_as_maps:
        header = tour_map_entry["header"]
        order.append(header)
        tour_map[header] = tour_map_entry["customers"]

    return order, tour_map


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
            # NaN-Werte abfangen und zu leeren Strings machen + Excel-Apostrophe entfernen
            def clean_excel_value(val):
                if not val or str(val).lower() == 'nan':
                    return ''
                s = str(val).strip()
                # Excel-Apostrophe entfernen (führende/abschließende Quotes)
                s = s.strip("'").strip('"')
                # Mehrfach-Spaces normalisieren
                s = ' '.join(s.split())
                return s
            
            street = clean_excel_value(stop.street)
            postal_code = clean_excel_value(stop.postal_code)
            city = clean_excel_value(stop.city)
            
            # Adresse nur zusammenbauen wenn mindestens ein Teil vorhanden ist
            address_parts = [part for part in [street, postal_code, city] if part.strip()]
            raw_address = ', '.join(address_parts) if address_parts else ''
            
            customer_dict = {
                "customer_number": stop.customer_number,
                "kdnr": stop.customer_number,
                "name": stop.name,
                "street": street,
                "postal_code": postal_code,
                "city": city,
                "bar_flag": stop.is_bar_stop,
                "address": normalize_address(raw_address, stop.name, postal_code),
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

