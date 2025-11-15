from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, TypedDict
import re

import pandas as pd


class CustomerRow(TypedDict):
    name: str
    adresse: str
    kundennr: str # Hinzugefügt für CSV
    street: str # Hinzugefügt für CSV
    plzOrt: str # Hinzugefügt für CSV
    isBarCash: bool # NEU: Für BAR-Zahler


def _parse_standard_layout(df: pd.DataFrame) -> Dict[str, object]:
    """Standardlayout mit Überschriften: datum/tour/name/adresse o.ä."""
    # Spalten normalisieren
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Versuche, passende Spalten zu finden
    col_date = next((c for c in df.columns if c in ("datum", "date")), None)
    col_tour = next((c for c in df.columns if c in ("tour", "tour-id", "tourid")), None)
    col_name = next(
        (c for c in df.columns if c in ("name", "firma", "kunde", "kundenname")), None
    )
    col_addr = next(
        (c for c in df.columns if c in ("adresse", "anschrift", "address")), None
    )

    if not all([col_date, col_tour, col_name, col_addr]):
        raise ValueError("Spalten im Standardlayout nicht gefunden")

    first_valid_date = df[col_date].dropna().astype(str).iloc[0]
    first_valid_tour = df[col_tour].dropna().astype(str).iloc[0]

    kunden: List[CustomerRow] = []
    for _, row in df.iterrows():
        name = str(row.get(col_name, "")).strip()
        adresse = str(row.get(col_addr, "")).strip()
        if name and adresse:
            kunden.append({"name": name, "adresse": adresse})

    return {"tour": first_valid_tour, "datum": first_valid_date, "kunden": kunden}


def _parse_bretfeld_layout(
    df_raw: pd.DataFrame, fallback_date: Optional[str]
) -> Dict[str, object]:
    """
    Layout laut Nutzer:
    - A = Kunden nummer; B = Name; C = Strasse; D = PLZ; E = Ort-M; F = gedruckt Ja/Nein
    - B5 enthält den Tour-Namen
    - Ab Zeile 6 beginnen die Datenzeilen
    Hinweis: Header sind ggf. nicht vorhanden → wir nutzen header=None.
    """
    df = df_raw.copy()
    # Sicherstellen, dass wir genug Zeilen/Spalten haben
    if df.shape[0] < 6 or df.shape[1] < 5:
        raise ValueError("Excel hat zu wenig Zeilen/Spalten für das erwartete Layout")

    # Tourname in B5 (0-basierter Index: Zeile 4, Spalte 1)
    tour_cell = df.iloc[4, 1]
    tour = str(tour_cell).strip() if pd.notna(tour_cell) else "Unbenannte Tour"

    kunden: List[CustomerRow] = []
    for _, row in df.iloc[5:].iterrows():  # ab Zeile 6
        name = (
            str(row.iloc[1]).strip()
            if row.shape[0] > 1 and pd.notna(row.iloc[1])
            else ""
        )
        strasse = (
            str(row.iloc[2]).strip()
            if row.shape[0] > 2 and pd.notna(row.iloc[2])
            else ""
        )
        plz = (
            str(row.iloc[3]).strip()
            if row.shape[0] > 3 and pd.notna(row.iloc[3])
            else ""
        )
        ort = (
            str(row.iloc[4]).strip()
            if row.shape[0] > 4 and pd.notna(row.iloc[4])
            else ""
        )

        if not name:
            # Heuristik: leere Name-Zeile beendet Liste
            continue

        adresse_parts = [part for part in [strasse, f"{plz} {ort}".strip()] if part]
        adresse = ", ".join(adresse_parts)
        if name and adresse:
            kunden.append({"name": name, "adresse": adresse})

    datum = fallback_date or ""
    return {"tour": tour, "datum": datum, "kunden": kunden}


def parse_teha_excel(
    path: str | Path, *, fallback_date: Optional[str] = None, encoding: Optional[str] = None
) -> Dict[str, object]:
    """
    Erwartetes Excel-Layout (minimal):
    - Blatt 1 enthält Spalten: Datum, Tour, Name, Adresse
    - Überschriften können variieren, werden aber per Lower/strip normalisiert
    """

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

    # Bestimme, ob es eine CSV-Datei ist
    is_csv = file_path.suffix.lower() == ".csv"
    # Verwende die übergebene Kodierung oder einen Standardwert
    actual_encoding = encoding if encoding is not None else "cp850"

    # Zuerst versuchen wir das Standardlayout
    try:
        if is_csv:
            df_std = pd.read_csv(file_path, sep=';', encoding=actual_encoding)
        else:
            df_std = pd.read_excel(file_path)
        return _parse_standard_layout(df_std)
    except Exception as e:
        print(f"[DEBUG] Standardlayout-Parsing fehlgeschlagen: {e}")
        # Fallback: Bretfeld-Layout (headerlos, feste Zellpositionen)
        if is_csv:
            df_bret = pd.read_csv(file_path, header=None, dtype=str, sep=';', encoding=actual_encoding)
        else:
            df_bret = pd.read_excel(file_path, header=None, dtype=str)
        return _parse_bretfeld_layout(df_bret, fallback_date=fallback_date)


def parse_teha_excel_all_sheets(
    path: str | Path, *, fallback_date: Optional[str] = None, encoding: Optional[str] = None
) -> List[Dict[str, object]]:
    """Liest alle Tabellenblätter und gibt pro Blatt eine Tour zurück (sofern Daten vorhanden)."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

    is_csv = file_path.suffix.lower() == ".csv"
    actual_encoding = encoding if encoding is not None else "cp850"

    if is_csv:
        # CSV hat keine Blätter, also nur das eine Blatt lesen
        try:
            df_std = pd.read_csv(file_path, sep=';', encoding=actual_encoding)
            tour = _parse_standard_layout(df_std)
        except Exception:
            df_bret = pd.read_csv(file_path, header=None, dtype=str, sep=';', encoding=actual_encoding)
            tour = _parse_bretfeld_layout(df_bret, fallback_date=fallback_date)
        if tour.get("kunden"):
            return [tour]
        return []

    xl = pd.ExcelFile(file_path)
    tours: List[Dict[str, object]] = []
    for sheet in xl.sheet_names:
        try:
            df_std = xl.parse(sheet)
            tour = _parse_standard_layout(df_std)
        except Exception:
            df_bret = xl.parse(sheet, header=None, dtype=str)
            tour = _parse_bretfeld_layout(df_bret, fallback_date=fallback_date)

        if tour.get("kunden"):
            tours.append(tour)
    return tours


_HEADER_REGEXES = [
    re.compile(
        r"\b\d{1,2}[:\.]\d{2}\s*Uhr\b", re.IGNORECASE
    ),  # 9:45 Uhr oder 09.00 Uhr
    re.compile(r"\bW\s*-?\s*\d+", re.IGNORECASE),  # W-09 oder W 09
    re.compile(r"\bPIR\b", re.IGNORECASE),  # PIR Marker
]


def _is_tour_header(cell: Optional[str]) -> bool:
    if not cell:
        return False
    text = str(cell).strip()
    if not text:
        return False
    # Heuristik: enthält Uhrzeit oder Muster wie W1/W2/PIR Anlief.
    if "Uhr" in text or ("W" in text and "-" in text) or ("PIR Anlief." in text):
        return True
    # Touren beginnen laut Vorgabe oft mit W oder T
    if text.upper().startswith("W") or text.upper().startswith("T"):
        return True
    return any(rx.search(text) for rx in _HEADER_REGEXES)


def parse_teha_excel_sections(
    path: str | Path,
    *,
    fallback_date: Optional[str] = None,
    headerless: bool = True,
    encoding: Optional[str] = None  # Neuer Parameter
) -> List[Dict[str, object]]:
    """
    Eine Tabelle enthält mehrere Touren hintereinander:
    - Tourkopf steht in Spalte B (Beispiel: "PIR.Anlief. 7:45 Uhr")
    - Zwischen den Touren kann mindestens eine Leerzeile stehen
    - Datenzeilen: B=Name, C=Straße, D=PLZ, E=Ort
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")

    is_csv = file_path.suffix.lower() == ".csv"
    actual_encoding = encoding if encoding is not None else "cp850"

    if is_csv:
        df = pd.read_csv(file_path, header=None if headerless else 0, dtype=str, sep=';', encoding=actual_encoding)
    else:
        df = pd.read_excel(file_path, header=None if headerless else 0, dtype=str)

    tours: List[Dict[str, object]] = []
    current_tour_name: Optional[str] = None
    current_customers: List[CustomerRow] = []

    def flush_current():
        nonlocal current_tour_name, current_customers
        if current_tour_name and current_customers:
            tours.append(
                {
                    "tour": current_tour_name,
                    "datum": fallback_date or "",
                    "kunden": list(current_customers),
                }
            )
        current_tour_name = None
        current_customers = []

    for _, row in df.iterrows():
        # Spalte A = Kundennummer, B = Name/Tourkopf, C = Straße, D = PLZ, E = Ort
        a = (
            str(row.iloc[0]).strip()
            if row.shape[0] > 0 and pd.notna(row.iloc[0])
            else ""
        )
        b = (
            str(row.iloc[1]).strip()
            if row.shape[0] > 1 and pd.notna(row.iloc[1])
            else ""
        )
        c = (
            str(row.iloc[2]).strip()
            if row.shape[0] > 2 and pd.notna(row.iloc[2])
            else ""
        )
        d = (
            str(row.iloc[3]).strip()
            if row.shape[0] > 3 and pd.notna(row.iloc[3])
            else ""
        )
        e = (
            str(row.iloc[4]).strip()
            if row.shape[0] > 4 and pd.notna(row.iloc[4])
            else ""
        )

        # Debug-Ausgabe für PIR-Zeilen
        if "PIR" in str(b):
            print(f"[DEBUG] PIR-Zeile gefunden: A='{a}', B='{b}', C='{c}', D='{d}', E='{e}'")
            print(f"[DEBUG] _is_tour_header(b) = {_is_tour_header(b)}")
            print(f"[DEBUG] not a = {not a}, not any([c,d,e]) = {not any([c, d, e])}")

        # komplett leer → überspringen
        if not (a or b or c or d or e):
            continue

        # Header nur wenn: A leer, B sieht wie Tourkopf aus, C–E leer
        if not a and _is_tour_header(b) and not any([c, d, e]):
            print(f"[DEBUG] Tour-Header erkannt: '{b}'")
            flush_current()
            current_tour_name = b
            continue

        # Datenzeile-Heuristik:
        # - A ist (meist) Nummer;
        # - B = Name nicht leer;
        # - Mindestens eine Adresse (C/D/E) vorhanden;
        # - D (PLZ) optional 4–5-stellig numerisch
        is_plz = bool(re.fullmatch(r"\d{4,5}", d)) if d else False
        has_addr = bool(c or d or e)
        is_data_row = b and has_addr and (a.isdigit() or is_plz or c)

        if is_data_row and current_tour_name:
            adresse_parts = [c]
            if d or e:
                adresse_parts.append(f"{d} {e}".strip())
            adresse = ", ".join([p for p in adresse_parts if p])
            
            # Bestimme den Ort aus der PLZ, falls nicht direkt vorhanden oder inkonsistent
            plz_ort_combined = f"{d} {e}".strip()

            # Prüfe auf 'BAR' im Tournamen, um isBarCash zu setzen
            is_bar_cash = "BAR" in (current_tour_name or "").upper()

            if adresse:
                current_customers.append(CustomerRow(
                    name=b,
                    adresse=adresse,
                    kundennr=a,
                    street=c,
                    plzOrt=plz_ort_combined,
                    isBarCash=is_bar_cash
                ))

    # Rest flushen
    flush_current()

    # NEUE LOGIK: "BAR"-Touren in reguläre Touren zusammenführen und Kunden flaggen
    final_tours: List[Dict[str, object]] = []
    tours_by_base_name = {}

    for tour_data in tours:
        tour_name = tour_data["tour"]
        # Basis-Tournamen erstellen durch Entfernen von bekannten Präfixen und Suffixen
        base_tour_name = tour_name
        
        # 1. Normalisiere UHR und entferne Suffixe zuerst
        base_tour_name = base_tour_name.replace("UHR", "Uhr").strip()
        base_tour_name = base_tour_name.replace(" BAR", "").strip()
        base_tour_name = base_tour_name.replace(" Tour", "").strip()
        base_tour_name = base_tour_name.replace(" our", "").strip()

        # 2. Entferne T-Präfixe (T gefolgt von Ziffern, optional /Ziffern) als eigenständige Codes
        # Verwendet eine sehr spezifische Regex, um nur T-Codes zu entfernen und Wortgrenzen zu respektieren.
        # Beispiel: "Anlief. T3, 9.30 Uhr" -> "Anlief. 9.30 Uhr"
        # Beispiel: "BZ T2/11 Anlief. 11.30 Uhr" -> "BZ Anlief. 11.30 Uhr"
        base_tour_name = re.sub(r"\bT\d+(?:/\d+)?\b[,\s]*", "", base_tour_name).strip()

        # 3. Entferne regionale/Liefer-Präfixe nur am Anfang des Strings (jetzt ohne 'Anlief.')
        # Das Ziel ist hier, "BZ", "CB", "FG", "PIR" am Anfang zu entfernen.
        base_tour_name = re.sub(r"^(BZ|CB|FG|PIR)\s*", "", base_tour_name).strip()

        # 4. Bereinige mehrfache Leerzeichen, die durch Entfernungen entstehen könnten
        base_tour_name = re.sub(r"\s+", " ", base_tour_name).strip()

        # 5. Entferne Kommas am Ende
        base_tour_name = base_tour_name.rstrip(',')

        # Finaler Fallback, falls der Name immer noch leer ist
        if not base_tour_name:
            base_tour_name = tour_name.replace(" BAR", "").strip()
            if not base_tour_name:
                base_tour_name = "Unbekannte Tour"
        
        # Wenn die Tour schon existiert, füge die Kunden hinzu
        if base_tour_name not in tours_by_base_name:
            tours_by_base_name[base_tour_name] = {
                "tour": base_tour_name,
                "datum": tour_data["datum"],
                "kunden": []
            }
        
        # Kunden zur entsprechenden Basistour hinzufügen
        tours_by_base_name[base_tour_name]["kunden"].extend(tour_data["kunden"])

    # Konvertiere das Dictionary zurück in eine Liste von Touren
    final_tours = list(tours_by_base_name.values())

    # Sortiere Touren chronologisch nach der Uhrzeit im Tournamen
    def get_tour_time_key(tour_data):
        # Sortiere nur Touren mit mehr als 5 Kunden nach Zeit
        if len(tour_data['kunden']) <= 5:
            return float('inf') # Diese Touren ans Ende der Liste schieben

        tour_name = tour_data["tour"]
        # Versuche, die Uhrzeit im Format HH:MM zu finden
        match = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*Uhr\b", tour_name, re.IGNORECASE)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        # Touren mit >5 Kunden aber ohne explizite Zeit am Ende sortieren
        return float('inf')

    final_tours.sort(key=get_tour_time_key)

    return final_tours


def parse_universal_routes(df: pd.DataFrame) -> Dict[str, object]:
    """
    Universeller Parser für alle Routen-Typen:
    - W-XX:00 Routen
    - PIR Anlief. Routen  
    - T-Routen
    - Alle anderen CSV-Überschriften
    
    Extrahiert echte Kundendaten aus der CSV statt Beispielwerte zu verwenden.
    """
    df = df.copy()
    
    # Alle Spalten-Überschriften als Routen extrahieren
    route_headers = []
    for col in df.columns:
        header = str(col).strip()
        if header and header.lower() not in ['nan', 'none', '']:
            route_headers.append(header)
    
    # Doppelte Einträge entfernen
    unique_routes = list(dict.fromkeys(route_headers))
    
    # Routen kategorisieren
    w_routes = [r for r in unique_routes if r.startswith('W-')]
    pir_routes = [r for r in unique_routes if 'PIR' in r or 'pir' in r]
    t_routes = [r for r in unique_routes if r.startswith('T') and r[1:].isdigit()]
    other_routes = [r for r in unique_routes if r not in w_routes + pir_routes + t_routes]
    
    # Echte Kundendaten pro Route extrahieren
    route_data = {}
    
    for route in unique_routes:
        # Spalte für diese Route finden
        route_col = None
        for col in df.columns:
            if str(col).strip() == route:
                route_col = col
                break
        
        if route_col is None:
            continue
            
        # Kunden in dieser Route zählen (nicht-leere Zeilen)
        customer_count = 0
        bar_customers = 0
        
        # Durch alle Zeilen der Route-Spalte gehen
        for _, row in df.iterrows():
            cell_value = str(row[route_col]).strip()
            if cell_value and cell_value.lower() not in ['nan', 'none', '', '0']:
                customer_count += 1
                # BAR-Flag prüfen (wenn in der Zelle "BAR" steht)
                if 'bar' in cell_value.lower():
                    bar_customers += 1
        
        # Route-Typ bestimmen
        route_type = "w_route" if route in w_routes else \
                    "pir_route" if route in pir_routes else \
                    "t_route" if route in t_routes else "other_route"
        
        # Nur W-Routen werden in Subtouren aufgeteilt
        ready_for_subtours = route in w_routes
        
        route_data[route] = {
            "name": route,
            "customer_count": customer_count,
            "type": route_type,
            "bar_customers": bar_customers,
            "ready_for_subtours": ready_for_subtours,
            "column_name": str(route_col)  # Für Debugging
        }
    
    return {
        "total_routes": len(unique_routes),
        "routes": route_data,
        "categories": {
            "w_routes": w_routes,
            "pir_routes": pir_routes, 
            "t_routes": t_routes,
            "other_routes": other_routes
        },
        "total_customers": sum(route["customer_count"] for route in route_data.values()),
        "total_bar_customers": sum(route["bar_customers"] for route in route_data.values())
    }
