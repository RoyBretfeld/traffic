"""
Parse the provided tour plan CSV and extract the W‑7:00 Uhr tour
with customer numbers included.

This script reimplements the parsing logic from the MD document
`route_plan_parser.md` but runs directly from Python.  It reads
`Tourenplan 21.08.2025.csv`, identifies tour headers and customer
records, merges any BAR stops into the following tour, and then
prints out the W‑7:00 Uhr tour with customer number (KdNr), name,
street, postal code and locality.  The output is printed to
standard output, one record per line.

Usage: python3 parse_w7.py
"""

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


def normalize(text: str) -> str:
    """
    Normalise German/European characters into ASCII.

    * Replaces the Eszett (ß) with "ss".
    * Uses Unicode normalisation (NFKD) to decompose accents and drops combining marks.
    * Returns a plain ASCII string.  Any remaining non‑ASCII characters are removed.
    """
    if not text:
        return ""
    # replace eszett/sharp‑s explicitly
    text = text.replace("ß", "ss").replace("ẞ", "SS")
    # decompose accents and remove combining marks
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    # encode to ASCII and ignore unknown characters
    ascii_text = stripped.encode("ascii", "ignore").decode("ascii")
    return ascii_text


def unify_route_name(name: str) -> str:
    """
    Remove key words like "BAR", "Tour" and "Uhr" from a route header
    and collapse multiple spaces.  The result is used as a key to match
    BAR‑prefixed routes to their corresponding main tours.
    """
    cleaned = re.sub(r"\b(BAR|Tour|Uhr)\b", "", name, flags=re.IGNORECASE)
    return " ".join(cleaned.split()).strip()


def parse_tour_plan(csv_path: Path) -> Dict[str, List[Dict]]:
    """
    Parse a tour plan exported as a semicolon‑delimited CSV.

    Returns a mapping from human‑readable tour name to a list of customer
    dictionaries.  Each dictionary contains the following keys:

    * ``kdnr`` – customer number as a string
    * ``name`` – normalised customer name
    * ``street`` – normalised street address
    * ``plz`` – postal code
    * ``ort`` – normalised locality
    * ``bar`` – boolean indicating if this stop came from a BAR tour
    """
    tours: Dict[str, List[Dict]] = defaultdict(list)
    pending_bar: Dict[str, List[Dict]] = defaultdict(list)
    full_name_map: Dict[str, str] = {}
    current_base: Optional[str] = None
    bar_mode: bool = False

    with open(csv_path, encoding="latin1", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            # skip completely empty rows
            if not any(row):
                continue
            # header rows: an empty first cell and a route name in the second cell
            if not row[0].strip():
                header = row[1].strip()
                if not header:
                    continue
                base = unify_route_name(header)
                if "BAR" in header.upper():
                    bar_mode = True
                    current_base = base
                    _ = pending_bar[base]
                else:
                    bar_mode = False
                    current_base = base
                    full_name_map[base] = header
                    if base in pending_bar:
                        tours[header].extend(pending_bar.pop(base))
                continue
            # customer line
            if current_base is None:
                continue
            kdnr = row[0].strip()
            if not kdnr:
                continue
            cust = {
                "kdnr": kdnr,
                "name": normalize(row[1].strip()),
                "street": normalize(row[2].strip()),
                "plz": row[3].strip(),
                "ort": normalize(row[4].strip()),
                "bar": bar_mode,
            }
            if bar_mode:
                pending_bar[current_base].append(cust)
            else:
                tour_name = full_name_map.get(current_base, header)
                tours[tour_name].append(cust)
    # assign any remaining BAR customers that did not find a match
    for base, custs in pending_bar.items():
        tours[base].extend(custs)
    return tours


def main():
    csv_file = Path("Tourenplan 21.08.2025.csv")
    tours = parse_tour_plan(csv_file)
    # find the W‑07.00 Uhr Tour
    tour_name = "W-07.00 Uhr Tour"
    stops = tours.get(tour_name, [])
    # print header
    print("KdNr;Name;Street;PLZ;Ort;Bar")
    # Deduplicate by a tuple of the main identifying fields.  This prevents
    # printing the same customer more than once when duplicates appear in
    # the source CSV (e.g. Auto-Service Becker was listed twice).
    seen = set()
    for s in stops:
        key = (s["kdnr"], s["name"], s["street"], s["plz"], s["ort"], s["bar"])
        if key in seen:
            continue
        seen.add(key)
        print("{};{};{};{};{};{}".format(
            s["kdnr"], s["name"], s["street"], s["plz"], s["ort"], "yes" if s["bar"] else "no"
        ))


if __name__ == "__main__":
    main()