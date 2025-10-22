from __future__ import annotations
from typing import Dict, Iterable, List, Optional, Tuple, Union
from collections import OrderedDict
from pathlib import Path
import re
import pandas as pd
import logging
from common.normalize import normalize_address
from common.tour_data_models import TourStop, TourInfo, TIME_PATTERN, TOUR_CODE_PATTERN, BROKEN_CHAR_TRANSLATION, _fix_broken_chars # Importiere TourStop und Hilfsfunktionen
from routes.upload_csv import _heuristic_decode # Importiere _heuristic_decode
from ingest.csv_reader import read_csv_unified # Importiere read_csv_unified


# (Datenstrukturen aus tour_plan_parser.py kopiert)
# @dataclass # Entfernt: TourStop wird jetzt aus common.tour_data_models importiert
# class TourStop:
#     customer_number: str
#     name: str
#     street: str
#     postal_code: str
#     city: str
#     is_bar_stop: bool

# (Hilfsfunktionen für Encoding/Normalisierung aus tour_plan_parser.py kopiert)

# TIME_PATTERN = re.compile(r"(\d{1,2})[.:](\d{2})") # Entfernt
# TOUR_CODE_PATTERN = re.compile(r"T(\d+)") # Entfernt
# BROKEN_CHAR_TRANSLATION = str.maketrans(...) # ... # Entfernt

# def _heuristic_decode(raw: bytes) -> tuple[str, str]: # Entfernt
#     # ... Heuristik-Code ...
#     for enc in ("cp850", "utf-8-sig", "latin-1"):
#         try:
#             return raw.decode(enc), enc
#         except UnicodeDecodeError:
#             continue
#     return raw.decode("utf-8", errors="replace"), "utf-8*replace"

# def _fix_broken_chars(text: str) -> str: # Entfernt
#     # ... Fix-Code ...
#     if not text:
#         return ""
#     return text.translate(BROKEN_CHAR_TRANSLATION)

def _normalize(text: str) -> str:
    # ... Normalize-Code ...
    if not text:
        return ""
    text = _fix_broken_chars(text)
    text = text.strip()
    return re.sub(r"\\s+", " ", text)

def _read_csv_lines(file_path: Union[str, Path]) -> Iterable[List[str]]:
    # ... CSV-Reader-Code ...
    # from ingest.csv_reader import read_csv_unified # Entfernt: Wird jetzt oben importiert
    df = read_csv_unified(file_path, sep=';', header=None, dtype=str)
    for _, row in df.iterrows():
        yield row.tolist()

# def _unify_route_name(name: str) -> str: # Entfernt
#     # ... Unify-Code ...
#     name = _fix_broken_chars(name)
#     cleaned = re.sub(r"\\b(BAR|Tour|Uhr)\\b", "", name, flags=re.IGNORECASE)
#     return " ".join(cleaned.split()).strip()

def extract_raw_stops(file_path: Union[str, Path]) -> Tuple[List[str], Dict[str, List[TourStop]], Dict[str, str]]:
    """
    Phase 1: Liest die CSV-Rohdaten und extrahiert Touren-Header und TourStops.
    Diese Funktion ist die neue '_extract_tours'.
    """
    tour_groups: "OrderedDict[str, List[TourStop]]" = OrderedDict()
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

        # 1. Tour-Header-Zeilen beginnen mit leerem ersten Feld
        if not first_cell and header_cell:
            header = header_cell
            base = TourInfo.get_base_name(header) # Verwende TourInfo.get_base_name
            
            # WICHTIG: Hier NUR die Daten erfassen, nicht konsolidieren
            if "BAR" in header.upper():
                bar_mode = True
                current_base = base
                current_header = header
                pending_bar.setdefault(header, []) # Nutze den vollen Header für BAR
            else:
                bar_mode = False
                current_base = base
                current_header = header
                
                # Verwende den VOLLEN Header (inkl. Zeit) als Schlüssel für die Tourengruppen
                if header not in tour_groups:
                    tour_groups[header] = []
                    order.append(header)
                
                full_name_map[base] = header # Mappe Base-Name auf den ersten Vollen Header

            continue

        # 2. Kundenzeilen
        if not current_base:
            logging.warning(f"[RAW_READER WARN] Kunde {first_cell} konnte keiner Tour zugeordnet werden (kein Header gefunden).") # Füge Logging hinzu
            continue  # außerhalb eines Tour-Blocks

        if not first_cell.isdigit():
            continue  # keine Kundenzeile

        name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        street = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        postal_code = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        city = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""

        customer = TourStop(
            customer_number=first_cell,
            name=normalize_address(name), # Verwende normalize_address
            street=normalize_address(street), # Verwende normalize_address
            postal_code=postal_code,
            city=normalize_address(city), # Verwende normalize_address
            is_bar_stop=bar_mode,
        )

        if bar_mode:
            # BAR-Stops werden unter ihrem eigenen BAR-Header gespeichert
            pending_bar.setdefault(current_header, []).append(customer)
        else:
            # Normale Stops werden unter ihrem vollen Header gespeichert
            tour_groups.setdefault(current_header, []).append(customer)
    
    # Füge BAR-Stops am Ende als separate Tour hinzu, falls sie keine Haupttour gefunden haben
    for header, customers in pending_bar.items():
        if header not in tour_groups:
             tour_groups[header] = customers
             order.append(header)
        else:
            # Falls BAR-Tour bereits erfasst wurde (sollte nicht passieren, aber sicherer)
            tour_groups[header].extend(customers)
            
    # Rückgabe: Reihenfolge, alle Touren (inkl. BAR), Mapping von Base-Name auf ersten Vollen Header
    return order, tour_groups, full_name_map
