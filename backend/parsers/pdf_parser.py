from __future__ import annotations

"""
PDF-Parser für FAMO TrafficApp
Ziel: Aus einem Touren-PDF strukturierte Daten extrahieren.

Erkennt:
- Tour-Header (z. B. "W-07:00", "PIR", "Anlief.")
- Kundenzeilen mit Trennzeichen zwischen Name und Adresse ("-", "–", "—")

Gibt eine Liste von Dicts zurück:
[
  {"tour": "W-07:00", "kunden": [{"name": "Muster GmbH", "adresse": "Straße 1, Ort"}, ...]}
]

Robustheit:
- Ignoriert leere/rauschartige Zeilen
- Normalisiert Whitespaces und Sonderstriche
- Akzeptiert auch Kundenzeilen mit mehrfachen Bindestrichen im Namen
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from backend.services.geocode import get_city_from_postal_code


# Erkenne typische Kopfzeilen wie
# - "W-07.00 Uhr BAR", "W-07:00 Uhr Tour"
# - "PIR Anlief. 7.45 BAR", "PIR Anlief. 7:45 Uhr"
# - "CB-08:30", "TA 09.15 Uhr", "BZ 10:00", "FG 12.00", "DPD 13:45"
# - "Anlief. 7:45"
# Punkt oder Doppelpunkt als Trenner sind erlaubt
TOUR_HEADER_RE = re.compile(
    r"^\s*(?:"
    r"(?:W|CB|TA|BZ|FG|DPD)\s*-?\s*\d{1,2}[:\.]\d{2}(?:\s*Uhr)?(?:\s*Tour)?(?:\s*BAR)?"  # Präfix + Zeit"
    r"|PIR\s*(?:Anlief\.?\s*)?\d{1,2}[:\.]\d{2}(?:\s*Uhr)?(?:\s*BAR)?"                       # PIR (+Anlief)"
    r"|Anlief\.?\s*\d{1,2}[:\.]\d{2}(?:\s*Uhr)?(?:\s*BAR)?"                                   # Nur Anlief"
    r")\s*$",
    re.IGNORECASE,
)

# Kundenzeile (Variante A): NAME <dash> ADRESSE, akzeptiere -, –, — als Trenner
CUSTOMER_RE = re.compile(r"^(?P<name>[^–—\-]{3,}?)\s*[–—\-]\s*(?P<addr>.+)$")

# Kundenzeile (Variante B): Spaltenlayout mit mindestens zwei Leerzeichen/Tabs als Trenner
# Optional führende Kundennummer (z. B. "5553 ") wird entfernt
CUSTOMER_COL_RE = re.compile(
    r"^(?P<name>.*?)\s{2,}"  # Name-Teil: Beliebige Zeichen (nicht-gierig) bis zu mindestens 2 Leerzeichen
    r"(?P<addr>.+)$",        # Adress-Teil: Beliebige Zeichen bis zum Zeilenende
    re.IGNORECASE,
)


def _clean_line(line: str) -> str:
    s = (line or "").strip()
    # Mehrfache Leerzeichen reduzieren
    while "  " in s:
        s = s.replace("  ", " ")
    # Steuerzeichen entfernen
    return re.sub(r"[\u200b\u200c\u200d]", "", s)


def _clean_line_for_column_parsing(line: str) -> str:
    s = (line or "").strip()
    # Steuerzeichen entfernen (aber keine Whitespaces reduzieren)
    return re.sub(r"[\u200b\u200c\u200d]", "", s)


def _is_tour_header(line: str) -> bool:
    s = _clean_line(line)
    print(f"[DEBUG] _is_tour_header: '" + s + "'") # Debug-Print
    if not s:
        return False
    if TOUR_HEADER_RE.match(s):
        return True
    # Fallback-Heuristik: Zeile enthält Uhrzeit und einen der Marker (W-, PIR, Anlief)
    has_time = re.search(r"\b\d{1,2}[:\.]\d{2}\b", s) is not None
    u = s.upper()
    markers = any(m in u for m in ("W", "PIR", "CB", "TA", "BZ", "FG", "DPD", "ANLIEF"))
    if has_time and markers:
        return True
    # Sehr kurze, komplett groß geschriebene Tokens
    if len(s) <= 8 and s.upper() == s and " " not in s:
        return True
    return False


def _extract_payment_flag(header: str) -> Optional[str]:
    """Liest Zahlungszusatz aus dem Tourkopf.
    Beispiele: "W-07:00 Uhr BAR" -> "bar"
    """
    s = _clean_line(header).lower()
    if " bar" in f" {s} ":
        return "bar"
    return None


def _normalize_tour_name(header: str) -> str:
    """Entfernt Zusätze wie "Uhr" und Zahlungsflags aus dem Tournamen."""
    s = _clean_line(header)
    # Entferne "Uhr" und "BAR" am Ende
    s = re.sub(r"\bUhr\b", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\bBAR\b", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\bTour\b", "", s, flags=re.IGNORECASE).strip()
    # Mehrfache Leerzeichen reduzieren
    while "  " in s:
        s = s.replace("  ", " ")
    return s


def _parse_customer_line(line: str) -> Optional[Tuple[str, str]]:
    # Zuerst versuchen, Spaltenlayout zu parsen, OHNE Leerzeichen zu reduzieren
    s_col = _clean_line_for_column_parsing(line)
    print(f"[DEBUG] _parse_customer_line (column try): '" + s_col + "'") # Debug-Print
    if s_col:
        # Entferne optionale führende Kundennummern
        s_col_no_num = re.sub(r"^\d{3,}\s+", "", s_col)
        mc = CUSTOMER_COL_RE.match(s_col_no_num)
        if mc:
            name = mc.group("name").strip()
            addr = mc.group("addr").strip()
            if len(name) >= 3 and len(addr) >= 5:
                # PLZ und Ort extrahieren und hinzufügen
                plz_match = re.search(r"\b(\d{5})\b", addr)
                if plz_match:
                    postal_code = plz_match.group(1)
                    city = get_city_from_postal_code(postal_code)
                    if city:
                        # Adresse so anpassen, dass der Ort nicht doppelt ist
                        if not city.lower() in addr.lower():
                            addr += f" {city}"
                return name, addr

    # Fallback: Wenn Spaltenlayout nicht passt, normale Zeilen mit Trennstrich
    s_dash = _clean_line(line)
    print(f"[DEBUG] _parse_customer_line (dash try): '" + s_dash + "'") # Debug-Print
    if not s_dash:
        return None
    # Entferne optionale führende Kundennummern
    s_dash_no_num = re.sub(r"^\d{3,}\s+", "", s_dash)

    # Variante A: Trennstrich zwischen Name und Adresse
    m = CUSTOMER_RE.match(s_dash_no_num)
    if m:
        name = m.group("name").strip(" -–—")
        addr = m.group("addr").strip()
        if len(name) >= 3 and len(addr) >= 5:
            # PLZ und Ort extrahieren und hinzufügen
            plz_match = re.search(r"\b(\d{5})\b", addr)
            if plz_match:
                postal_code = plz_match.group(1)
                city = get_city_from_postal_code(postal_code)
                if city:
                    # Adresse so anpassen, dass der Ort nicht doppelt ist
                    if not city.lower() in addr.lower():
                        addr += f" {city}"
            return name, addr

    return None


# Heuristik für zweispaltige PDFs: Name und Adresse stehen in getrennten Zeilen
NAME_ONLY_RE = re.compile(r"^(?:\d{3,}\s+)?(?P<name>[A-ZÄÖÜa-zäöü][\\wÄÖÜäöüß\\-\\&\\.,\\s]{3,})$")
ADDR_ONLY_RE = re.compile(
    r"^(?P<addr>.+?(?:strasse|straße|straße|str\.|weg|allee|platz|chaussee|ring|ufer|damm|steig|gasse|chaussee|chaussee)\s*\d+[\w\-/]*.*\b\d{5}\b.*)$",
    re.IGNORECASE,
)

def _is_name_only(line: str) -> Optional[str]:
    s = _clean_line(line)
    print(f"[DEBUG] _is_name_only: '" + s + "'") # Debug-Print
    if not s:
        return None
    m = NAME_ONLY_RE.match(s)
    if m:
        return m.group("name").strip()
    return None

def _is_addr_only(line: str) -> Optional[str]:
    s = _clean_line(line)
    print(f"[DEBUG] _is_addr_only: '" + s + "'") # Debug-Print
    if not s:
        return None
    # Entferne führende Spaltenreste
    s = re.sub(r"^(?:[A-ZÄÖÜ].{2,}?\s{2,})", "", s)
    m = ADDR_ONLY_RE.match(s)
    if m:
        return m.group("addr").strip()
    # Fallback: enthält 5-stellige PLZ und eine Hausnummer
    if re.search(r"\b\d{5}\b", s) and re.search(r"\b\d+[a-zA-Z]?\b", s):
        return s
    return None


def parse_pdf_tours(pdf_path: Path) -> List[Dict[str, object]]:
    try:
        import pdfplumber  # import hier, damit Modul optional bleibt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"pdfplumber nicht verfügbar: {exc}")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(str(pdf_path))

    tours: List[Dict[str, object]] = []
    current_name: Optional[str] = None
    current_kunden: List[Dict[str, str]] = []
    current_payment_tour: Optional[str] = None  # Tour-weit (nur Info)
    current_payment_for_customers: Optional[str] = None  # gilt für neu folgende Kunden bis Kopf ohne BAR

    def flush():
        nonlocal current_name, current_kunden, current_payment_tour, current_payment_for_customers
        if current_name and current_kunden:
            tour_obj: Dict[str, object] = {
                "tour": _normalize_tour_name(current_name),
                "kunden": current_kunden,
            }
            if current_payment_tour:
                tour_obj["payment"] = current_payment_tour
            tours.append(tour_obj)
        current_name = None
        current_kunden = []
        current_payment_tour = None
        current_payment_for_customers = None

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pending_name: Optional[str] = None
            for raw in text.splitlines():
                line = _clean_line(raw)
                print(f"[DEBUG] Verarbeite Zeile: '" + line + "', pending_name: " + str(pending_name)) # Debug-Print
                if not line:
                    continue
                if _is_tour_header(line):
                    # Prüfe auf doppelte Kopfzeile (z. B. "W-07:00 Uhr BAR" gefolgt von "W-07:00 Uhr Tour")
                    new_norm = _normalize_tour_name(line)
                    if current_name and _normalize_tour_name(current_name) == new_norm:
                        # Gleiche Tour – BAR soll nur für davorstehende Kunden gelten
                        pay = _extract_payment_flag(line)
                        current_payment_for_customers = "bar" if pay else None
                        # Tour-weite Info beibehalten, falls gesetzt
                        if pay:
                            current_payment_tour = pay
                        continue
                    # Neue Tour beginnen
                    flush()
                    current_name = line
                    current_payment_tour = _extract_payment_flag(line)
                    current_payment_for_customers = "bar" if current_payment_tour else None
                    continue
                parsed = _parse_customer_line(line)
                if parsed:
                    name, addr = parsed
                    row: Dict[str, str] = {"name": name, "adresse": addr}
                    if current_payment_for_customers:
                        row["payment"] = current_payment_for_customers
                    current_kunden.append(row)
                    pending_name = None
                    continue

                # Zweizeilige Zeilen erkennen (Name in Zeile A, Adresse in Zeile B)
                if pending_name is None:
                    maybe_name = _is_name_only(line)
                    if maybe_name:
                        pending_name = maybe_name
                        continue
                else:
                    maybe_addr = _is_addr_only(line)
                    if maybe_addr:
                        row2: Dict[str, str] = {"name": pending_name, "adresse": maybe_addr}
                        if current_payment_for_customers:
                            row2["payment"] = current_payment_for_customers
                        current_kunden.append(row2)
                        pending_name = None
                        continue

                # Debug-Ausgabe für nicht erkannte Zeilen
                print(f"[DEBUG] Unbekannte Zeile übersprungen: '" + line + "'")

            # Fallback: Spaltenweise Zuordnung per Wortkoordinaten, wenn bisher keine Kunden erkannt wurden
            if not current_kunden:
                try:
                    words = page.extract_words(x_tolerance=2, y_tolerance=3)
                    if words:
                        # Gruppiere nach Zeilen (y Mitte runden)
                        rows: Dict[int, List[dict]] = {}
                        for w in words:
                            ymid = int(round((w.get("top", 0) + w.get("bottom", 0)) / 2))
                            rows.setdefault(ymid, []).append(w)
                        # Heuristik: drei Spalten (Name | Straße/Hausnr | PLZ/Ort)
                        x0_page = page.bbox[0]; x1_page = page.bbox[2]
                        width = (x1_page - x0_page)
                        c1 = x0_page + width * 0.33
                        c2 = x0_page + width * 0.66
                        for y in sorted(rows.keys()):
                            items = sorted(rows[y], key=lambda z: z.get("x0", 0))
                            left = " ".join([it["text"] for it in items if it.get("x0", 0) < c1]).strip()
                            middle = " ".join([it["text"] for it in items if c1 <= it.get("x0", 0) < c2]).strip()
                            right = " ".join([it["text"] for it in items if it.get("x0", 0) >= c2]).strip()
                            if not left and not right:
                                continue
                            # Header-Zeilen überspringen
                            if _is_tour_header(left) or _is_tour_header(right):
                                # flush aktuelle Gruppe
                                flush()
                                current_name = left if _is_tour_header(left) else right
                                current_payment_tour = _extract_payment_flag(current_name)
                                current_payment_for_customers = "bar" if current_payment_tour else None
                                continue
                            # Kundennummer vorne (z. B. 5023) abtrennen
                            import re as _re
                            kundennr = None
                            if left:
                                mnum = _re.match(r"^(\d{3,})\s+(.*)$", left)
                                if mnum:
                                    kundennr = mnum.group(1)
                                    left = mnum.group(2).strip()
                            # Adresse zusammensetzen: Mitte + (optionale) rechte Spalte (PLZ/Ort)
                            addr_parts = [s for s in [middle, right] if s]
                            addr = ", ".join(addr_parts).strip(", ")
                            addr = _re.sub(r"\s+", " ", addr)
                            # Nur Zeilen mit Name und Adresse als Kunden interpretieren
                            if left and addr and len(left) > 2 and len(addr) > 4:
                                row2: Dict[str, str] = {"name": left, "adresse": addr}
                                if kundennr:
                                    row2["kundennr"] = kundennr
                                if current_payment_for_customers:
                                    row2["payment"] = current_payment_for_customers
                                current_kunden.append(row2)
                except Exception:
                    pass

    # Letzte Gruppe flushen
    flush()

    return tours


def preview_summary(pdf_path: Path) -> Dict[str, object]:
    """Erzeugt eine kompakte Vorschau zur Anzeige im UI."""
    tours = parse_pdf_tours(pdf_path)
    total_customers = sum(len(t.get("kunden", [])) for t in tours)
    return {
        "tours_found": len(tours),
        "customers_found": total_customers,
        "tours": [
            {
                "tour": t["tour"],
                "customers": len(t.get("kunden", [])),
                "sample": t.get("kunden", [])[:5],
            }
            for t in tours
        ],
    }


