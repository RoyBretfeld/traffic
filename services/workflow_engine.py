# -*- coding: utf-8 -*-
"""
FAMO TrafficApp – End‑to‑End Workflow: Parse → Geocode → Optimize

Ziel
----
Ein in sich geschlossener, leicht integrierbarer Workflow, der eine CSV
mit Tourdaten einliest, validiert, fehlende Geokodierung auffüllt (wenn
Lat/Lon fehlen), Touren gruppiert und pro Tour eine Route optimiert.

Highlights
----------
- Automatische Dialekt‑Erkennung für CSV (Delimiter, Quotechar)
- Robuste Feldzuordnung (konfigurierbar per ColumnMap)
- Adress‑Normalisierung (u. a. Straßensuffixe, doppelte Spaces)
- Geokodierung: Plug‑in‑Interface. Default: nutzt vorhandene Lat/Lon
  oder gibt eine Warnung aus (kein externer Call im Default)
- Optimierung: Nearest‑Neighbor + 2‑Opt (schnell, ohne Fremdbibliothek)
- Zählungen und Status: OK/Warn/Bad, analog zur UI‑Anzeige
- Saubere Python‑APIs für Integration in FastAPI/Flask/Streamlit

Hinweis: Dieser Code ist *framework‑agnostisch*. Die Funktionen
können direkt in eure bestehende App (routes/… bzw. backend/services/…)
integriert werden. Die Geocoder‑Schnittstelle kann z. B. via Nominatim
oder Google umgesetzt werden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Iterable
import csv
import io
import math
import re

# -----------------------------
# Datenmodelle
# -----------------------------

@dataclass
class TourStop:
    order_id: str
    customer: str
    street: str
    postal_code: str
    city: str
    country: str = "DE"
    lat: Optional[float] = None
    lon: Optional[float] = None
    # Metadaten
    attrs: Dict[str, str] = field(default_factory=dict)

@dataclass
class Tour:
    tour_id: str
    stops: List[TourStop]

@dataclass
class WorkflowResult:
    ok: int
    warn: int
    bad: int
    warnings: List[str]
    errors: List[str]
    tours: List[Tour]

# -----------------------------
# CSV Reader mit Dialekterkennung
# -----------------------------

class CSVReader:
    """Liest Tourdaten aus CSV. Erkennt Delimiter und Quotechar automatisch."""

    def __init__(self, encoding: str = "utf-8", strict: bool = False) -> None:
        self.encoding = encoding
        self.strict = strict

    def sniff(self, sample: bytes) -> csv.Dialect:
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample.decode(self.encoding, errors="ignore"))
            dialect.doublequote = True
            return dialect
        except csv.Error:
            # Fallback: Semikolon ist im DACH‑Raum häufig
            class _D(csv.Dialect):
                delimiter = ";"
                quotechar = '"'
                escapechar = None
                doublequote = True
                skipinitialspace = True
                lineterminator = "\n"
                quoting = csv.QUOTE_MINIMAL
            return _D()

    def read(self, content: bytes) -> List[Dict[str, str]]:
        sample = content[:4096]
        dialect = self.sniff(sample)
        text = io.StringIO(content.decode(self.encoding, errors="ignore"))
        reader = csv.DictReader(text, dialect=dialect)
        rows = []
        for row in reader:
            # Entferne BOM‑Artefakte aus Headern/Werten
            cleaned = {k.replace("\ufeff", "").strip(): (v or "").strip() for k, v in row.items()}
            rows.append(cleaned)
        if self.strict and not rows:
            raise ValueError("CSV enthält keine Datenzeilen.")
        return rows

# -----------------------------
# Normalisierung & Hilfsfunktionen
# -----------------------------

_spaces = re.compile(r"\s+")
_street_suffix = {
    "strasse": "straße",
    "str": "straße",
}

def normalize_address(street: str) -> str:
    s = street.strip()
    s = _spaces.sub(" ", s)
    low = s.lower()
    for k, v in _street_suffix.items():
        if low.endswith(k):
            s = s[: -len(k)] + v
            break
    return s

# Haversine für Luftlinie

def haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    R = 6371000.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(x))

# -----------------------------
# Geocoder‑Schnittstelle (Pluggable)
# -----------------------------

class Geocoder:
    """Interface. Implementiere `geocode` für Adressen.

    Default‑Implementierung: nutzt vorhandene Lat/Lon; andernfalls Warnung.
    """

    def geocode(self, stop: TourStop) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        if stop.lat is not None and stop.lon is not None:
            return stop.lat, stop.lon, None
        # Kein externer Call im Default: gib Warnung zurück
        return None, None, f"Keine Koordinaten für {stop.customer} – {stop.street}, {stop.postal_code} {stop.city}"

# -----------------------------
# Optimierung: NN + 2‑Opt
# -----------------------------

def optimize_route(coords: List[Tuple[float, float]]) -> List[int]:
    """Gibt eine Besuchsreihenfolge (Indizes) zurück.
    1) Nearest‑Neighbor Start = 0
    2) Lokale Verbesserung via 2‑Opt
    """
    if not coords:
        return []
    n = len(coords)
    remaining = set(range(1, n))
    tour = [0]
    while remaining:
        last = tour[-1]
        next_idx = min(remaining, key=lambda j: haversine(coords[last], coords[j]))
        tour.append(next_idx)
        remaining.remove(next_idx)
    # 2‑Opt
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                a, b = tour[i - 1], tour[i]
                c, d = tour[j], tour[j + 1]
                before = haversine(coords[a], coords[b]) + haversine(coords[c], coords[d])
                after = haversine(coords[a], coords[c]) + haversine(coords[b], coords[d])
                if after + 1e-6 < before:
                    tour[i : j + 1] = reversed(tour[i : j + 1])
                    improved = True
    return tour

# -----------------------------
# Column‑Mapping für unterschiedliche CSVs
# -----------------------------

@dataclass
class ColumnMap:
    tour_id: str = "tour_id"
    order_id: str = "order_id"
    customer: str = "customer"
    street: str = "street"
    postal_code: str = "postal_code"
    city: str = "city"
    lat: str = "lat"
    lon: str = "lon"

# -----------------------------
# Parser → Geocode → Optimize
# -----------------------------

def build_stops(rows: List[Dict[str, str]], cm: ColumnMap, warnings: List[str]) -> Dict[str, List[TourStop]]:
    tours: Dict[str, List[TourStop]] = {}
    for idx, r in enumerate(rows, 2):  # +2 für Header/1‑basiert
        try:
            tid = (r.get(cm.tour_id) or "").strip() or "DEFAULT"
            stop = TourStop(
                order_id=(r.get(cm.order_id) or f"ROW{idx}"),
                customer=(r.get(cm.customer) or "Unbekannt"),
                street=normalize_address(r.get(cm.street) or ""),
                postal_code=(r.get(cm.postal_code) or ""),
                city=(r.get(cm.city) or ""),
                lat=_to_float(r.get(cm.lat)),
                lon=_to_float(r.get(cm.lon)),
                attrs={k: v for k, v in r.items() if k not in cm.__dict__.values()},
            )
            tours.setdefault(tid, []).append(stop)
        except Exception as ex:
            warnings.append(f"Zeile {idx}: {ex}")
    return tours


def _to_float(x: Optional[str]) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


def run_workflow(
    content: bytes,
    column_map: Optional[ColumnMap] = None,
    geocoder: Optional[Geocoder] = None,
) -> WorkflowResult:
    """End‑to‑End Ausführung. Liefert Zählungen und Touren zurück."""
    cm = column_map or ColumnMap()
    gec = geocoder or Geocoder()

    reader = CSVReader()
    rows = reader.read(content)

    warnings: List[str] = []
    errors: List[str] = []

    grouped = build_stops(rows, cm, warnings)

    ok = 0
    warn = 0
    bad = 0
    tours_out: List[Tour] = []

    for tid, stops in grouped.items():
        # Geokodieren
        for s in stops:
            lat, lon, warn_msg = gec.geocode(s)
            if lat is not None and lon is not None:
                s.lat, s.lon = lat, lon
                ok += 1
            else:
                warn += 1
                warnings.append(warn_msg or f"Warnung bei {s.order_id}")
        # Filtere ungültige
        valid = [s for s in stops if s.lat is not None and s.lon is not None]
        invalid = [s for s in stops if s.lat is None or s.lon is None]
        bad += len(invalid)
        if not valid:
            errors.append(f"Tour {tid} hat keine gültigen Koordinaten.")
            continue
        # Optimieren
        coords = [(s.lat, s.lon) for s in valid]  # type: ignore
        order = optimize_route(coords)
        sorted_valid = [valid[i] for i in order]
        tours_out.append(Tour(tour_id=tid, stops=sorted_valid))

    return WorkflowResult(ok=ok, warn=warn, bad=bad, warnings=warnings, errors=errors, tours=tours_out)

# -----------------------------
# Beispielintegration (CLI/Dev)
# -----------------------------

if __name__ == "__main__":
    import argparse, pathlib, json

    ap = argparse.ArgumentParser(description="FAMO Workflow: Parse→Geocode→Optimize")
    ap.add_argument("csv", type=pathlib.Path)
    ap.add_argument("--encoding", default="utf-8")
    ap.add_argument("--tour-col", default="tour_id")
    ap.add_argument("--lat-col", default="lat")
    ap.add_argument("--lon-col", default="lon")
    args = ap.parse_args()

    cm = ColumnMap(tour_id=args.tour_col, lat=args.lat_col, lon=args.lon_col)
    data = args.csv.read_bytes()
    result = run_workflow(data, column_map=cm)

    print(f"Workflow erfolgreich. {result.ok} OK, {result.warn} Warn, {result.bad} Bad")
    if result.warnings:
        print("\nWARNINGS:")
        for w in result.warnings:
            print(" -", w)
    if result.errors:
        print("\nERRORS:")
        for e in result.errors:
            print(" -", e)
    # Beispiel: Ausgabe der ersten Tour als JSON
    if result.tours:
        t0 = result.tours[0]
        out = {
            "tour_id": t0.tour_id,
            "stops": [
                {
                    "order_id": s.order_id,
                    "customer": s.customer,
                    "lat": s.lat,
                    "lon": s.lon,
                }
                for s in t0.stops
            ],
        }
        print("\nERSTE TOUR (JSON):\n" + json.dumps(out, ensure_ascii=False, indent=2))
