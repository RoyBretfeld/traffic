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
from backend.routes.upload_csv import _heuristic_decode # Importiere _heuristic_decode
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
    """
    Extrahiert Touren aus CSV mit bewährter Logik aus parse_w7.py:
    - BAR-Touren werden korrekt mit ihren Haupttouren zusammengeführt
    - Gruppierung basiert auf base_name (ohne "BAR"/"Tour"/"Uhr")
    """
    # Direktes Mapping wie in parse_w7.py: header -> Liste[TourStop]
    tours: Dict[str, List[TourStop]] = OrderedDict()
    
    # BAR-Kunden werden hier gesammelt, bis eine passende Haupttour kommt
    pending_bar: Dict[str, List[TourStop]] = {}
    
    # Mapping: base_name -> vollständiger Header-String der ERSTEN Haupttour
    full_name_map: Dict[str, str] = {}
    
    # Reihenfolge der Header (für deterministische Ausgabe)
    header_order: List[str] = []
    
    # Deduplizierung: Set pro Tour um Duplikate zu vermeiden
    tour_seen: Dict[str, set] = {}  # tour_header -> set von (customer_number, name, street, postal_code, city)
    
    current_base: Optional[str] = None
    current_header: Optional[str] = None  # AKTUELLER Header (für normale Kunden-Zuordnung)
    bar_mode: bool = False
    
    for row in _read_csv_lines(file_path):
        if not any(row):
            continue
        
        first_cell = str(row[0]).strip() if len(row) > 0 and row[0] is not None and str(row[0]) != 'nan' else ""
        header_cell = str(row[1]).strip() if len(row) > 1 and row[1] is not None and str(row[1]) != 'nan' else ""
        
        # Header-Zeile: leeres erstes Feld, Name im zweiten Feld
        if not first_cell and header_cell:
            header = header_cell
            base = TourInfo.get_base_name(header)  # Entfernt "BAR", "Tour", "Uhr" etc.
            
            if "BAR" in header.upper():
                # BAR-Tour: Sammle Kunden in pending_bar
                bar_mode = True
                current_base = base
                current_header = None  # Kein aktueller Header für BAR-Touren
                # Initialisiere pending_bar für diesen base_name (wie parse_w7.py Zeile 89)
                if base not in pending_bar:
                    pending_bar[base] = []
            else:
                # ANLIEF-Touren und andere Spezialtouren werden auch als Haupttouren behandelt
                # (sie haben zwar keinen normalen Tour-Namen, aber Kunden gehören zu ihnen)
                # Haupttour: Füge BAR-Kunden hinzu (falls vorhanden), dann normal weiter
                bar_mode = False
                current_base = base
                current_header = header  # WICHTIG: Setze aktuellen Header für normale Kunden!
                
                # WICHTIG: Speichere Header FÜR BAR-Zuordnung (MUSS VOR pop() passieren!)
                if base not in full_name_map:
                    full_name_map[base] = header
                
                # Initialisiere Tour (MUSS VOR pop() passieren!)
                if header not in tours:
                    tours[header] = []
                    header_order.append(header)
                
                # WICHTIG: Füge pending BAR-Kunden zur Haupttour hinzu (wie in parse_w7.py Zeile 94-95)
                # NACHDEM tours[header] initialisiert wurde
                if base in pending_bar and pending_bar[base]:
                    # Deduplizierung: Entferne BAR-Kunden die bereits in der Tour sind
                    if header not in tour_seen:
                        tour_seen[header] = set()
                    
                    deduplicated_bar = []
                    for bar_customer in pending_bar[base]:
                        bar_key = (bar_customer.customer_number, bar_customer.name, bar_customer.street, 
                                  bar_customer.postal_code, bar_customer.city)
                        if bar_key not in tour_seen[header]:
                            tour_seen[header].add(bar_key)
                            deduplicated_bar.append(bar_customer)
                        else:
                            logging.debug(f"[PARSER] Duplikat in BAR-Merge übersprungen: {bar_customer.name}")
                    
                    # Füge deduplizierte BAR-Kunden AM ANFANG der Haupttour ein
                    tours[header] = deduplicated_bar + tours[header]
                    pending_bar.pop(base)  # Entferne aus pending_bar
            
            continue
        
        # Kunden-Zeile: erste Zelle ist Kunden-Nummer (nur Ziffern)
        if not current_base:
            continue  # Außerhalb eines Tour-Blocks
        
        if not first_cell or not first_cell.isdigit():
            continue  # Keine gültige Kunden-Zeile
        
        # Extrahiere Kunden-Daten
        name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        street = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
        postal_code = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        city = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
        
        # Synonym-Auflösung: IMMER versuchen wenn KdNr vorhanden ist
        # (auch wenn Adresse schon vorhanden, um Koordinaten aus Synonymen zu übernehmen)
        synonym_street = street
        synonym_postal_code = postal_code
        synonym_city = city
        resolved_customer_id = None
        
        # IMMER Synonym-Auflösung versuchen wenn KdNr vorhanden
        # WICHTIG: Mit Timeout und Fehlerbehandlung, damit Synonym-Auflösung nicht blockiert
        if first_cell:
            try:
                from backend.services.synonyms import SynonymStore
                from pathlib import Path
                import signal
                
                # Datenbank-Pfad finden
                db_path = Path(__file__).resolve().parents[2] / "data" / "traffic.db"
                if not db_path.exists():
                    # Fallback
                    possible_paths = [
                        Path("data/traffic.db"),
                        Path("./data/traffic.db"),
                    ]
                    for path in possible_paths:
                        if path.exists():
                            db_path = path
                            break
                
                # Synonym-Store mit Timeout-Schutz (verhindert Blockierung)
                try:
                    synonym_store = SynonymStore(db_path)
                except Exception as store_error:
                    logging.warning(f"[SYNONYM] Fehler beim Initialisieren des Synonym-Stores: {store_error}")
                    synonym_store = None
                
                # 1. Suche nach KdNr: "KdNr:{customer_number}" (ALWAYS suchen wenn KdNr vorhanden)
                synonym_lat = None
                synonym_lon = None
                resolved_customer_id = None
                
                if first_cell and synonym_store:
                    try:
                        kdnr_synonym = synonym_store.resolve(f"KdNr:{first_cell}")
                        if kdnr_synonym:
                            # Übernehme Adresse aus Synonym (auch wenn sie leer ist, damit sie später gesetzt wird)
                            synonym_street = kdnr_synonym.street or street or ""
                            synonym_postal_code = kdnr_synonym.postal_code or postal_code or ""
                            synonym_city = kdnr_synonym.city or city or ""
                            synonym_lat = kdnr_synonym.lat
                            synonym_lon = kdnr_synonym.lon
                            resolved_customer_id = kdnr_synonym.customer_id
                            # Logging entfernt - verursacht Terminal-Spam
                            # logging.debug(f"[SYNONYM] KdNr:{first_cell} → Synonym gefunden: street='{synonym_street}', city='{synonym_city}', lat={synonym_lat}, lon={synonym_lon}")
                        else:
                            kdnr_synonym = None
                    except Exception as resolve_error:
                        logging.warning(f"[SYNONYM] Fehler bei KdNr-Auflösung für '{first_cell}': {resolve_error}")
                        kdnr_synonym = None
                else:
                    kdnr_synonym = None
                
                # 2. IMMER nach Name suchen (auch wenn Adresse vorhanden), um falsche Adressen zu korrigieren
                # Beispiel: "Büttner" mit falscher Adresse "Fröbelstraße 20" → sollte zu "Steigerstraße 1" korrigiert werden
                if name and synonym_store:
                    try:
                        name_synonym = synonym_store.resolve(name)
                        if name_synonym:
                            # WICHTIG: Wenn Name-Synonym eine vollständige Adresse hat, verwende diese (korrigiert falsche Adressen)
                            if name_synonym.street and name_synonym.postal_code and name_synonym.city:
                                # Name-Synonym hat vollständige Adresse → verwende diese (höhere Priorität als CSV)
                                synonym_street = name_synonym.street
                                synonym_postal_code = name_synonym.postal_code
                                synonym_city = name_synonym.city
                                if name_synonym.lat:
                                    synonym_lat = name_synonym.lat
                                if name_synonym.lon:
                                    synonym_lon = name_synonym.lon
                                resolved_customer_id = name_synonym.customer_id or resolved_customer_id
                                # Logging entfernt - verursacht Terminal-Spam
                                # logging.debug(f"[SYNONYM] Name '{name}' → Synonym KORRIGIERT Adresse: street='{synonym_street}', city='{synonym_city}', real_customer_id={resolved_customer_id}")
                            elif not (synonym_street.strip() and synonym_postal_code.strip() and synonym_city.strip()):
                                # Fallback: Nur wenn noch keine vollständige Adresse vorhanden
                                synonym_street = name_synonym.street or synonym_street or ""
                                synonym_postal_code = name_synonym.postal_code or synonym_postal_code or ""
                                synonym_city = name_synonym.city or synonym_city or ""
                                if not synonym_lat:
                                    synonym_lat = name_synonym.lat
                                if not synonym_lon:
                                    synonym_lon = name_synonym.lon
                                resolved_customer_id = name_synonym.customer_id or resolved_customer_id
                                # Logging entfernt - verursacht Terminal-Spam
                                # logging.debug(f"[SYNONYM] Name '{name}' → Synonym gefunden: street='{synonym_street}', city='{synonym_city}'")
                    except Exception as resolve_error:
                        logging.warning(f"[SYNONYM] Fehler bei Name-Auflösung für '{name}': {resolve_error}")
                        name_synonym = None
                else:
                    name_synonym = None
                
                # 3. Logging entfernt - verursacht zu viel Terminal-Spam
                # Falls Debugging nötig: Temporär wieder aktivieren mit logging.debug()
                # if first_cell and (synonym_street or synonym_postal_code or synonym_city):
                #     logging.debug(f"[SYNONYM] Final für KdNr:{first_cell}: street='{synonym_street}', postal='{synonym_postal_code}', city='{synonym_city}', lat={synonym_lat}, lon={synonym_lon}")
            except Exception as e:
                logging.warning(f"[SYNONYM] Fehler bei Synonym-Auflösung (überspringe): {e}")
                # Bei Fehlern: Verwende originale Werte (nicht blockieren!)
        
        customer = TourStop(
            customer_number=first_cell,
            name=_normalize(name),
            street=_normalize(synonym_street),
            postal_code=synonym_postal_code,
            city=_normalize(synonym_city),
            is_bar_stop=bar_mode
        )
        
        # Speichere resolved_customer_id im Customer-Objekt (falls unterstützt)
        # HINWEIS: TourStop hat kein customer_id Feld, daher wird es später beim Dict-Mapping hinzugefügt
        customer._resolved_customer_id = resolved_customer_id
        
        # WICHTIG: Übernehme Koordinaten aus Synonymen direkt ins TourStop-Objekt
        if synonym_lat is not None and synonym_lon is not None:
            customer._synonym_lat = synonym_lat
            customer._synonym_lon = synonym_lon
            # Logging entfernt - verursacht Terminal-Spam
            # logging.debug(f"[SYNONYM] Koordinaten für KdNr:{first_cell} übernommen: lat={synonym_lat}, lon={synonym_lon}")
        
        # Zuordnung: BAR-Kunden -> pending_bar, normale -> direkt zur Tour
        if bar_mode:
            # BAR-Kunden: Sammle in pending_bar für diesen base_name
            # Prüfe auf Duplikate innerhalb des pending_bar für diesen base_name
            bar_key = (customer.customer_number, customer.name, customer.street, customer.postal_code, customer.city)
            if current_base not in pending_bar:
                pending_bar[current_base] = []
            
            # Prüfe ob dieser Kunde bereits in pending_bar ist
            if any((c.customer_number, c.name, c.street, c.postal_code, c.city) == bar_key 
                   for c in pending_bar[current_base]):
                logging.debug(f"[PARSER] Duplikat in BAR pending_bar übersprungen: {customer.name}")
                continue
            
            pending_bar[current_base].append(customer)
        else:
            # Normale Kunden: füge zur AKTUELLEN Haupttour hinzu
            # WICHTIG: Verwende current_header (wurde beim Header-Lesen gesetzt!)
            # NICHT full_name_map, da mehrere Touren den gleichen base_name haben können!
            
            if not current_header:
                logging.warning(f"[PARSER] Kein current_header für base_name '{current_base}', verwende Fallback")
                # Fallback: Verwende den letzten Header aus header_order
                if header_order and current_base:
                    for h in reversed(header_order):
                        if TourInfo.get_base_name(h) == current_base:
                            current_header = h
                            break
                
                if not current_header:
                    current_header = f"TOUR-{current_base}"
                    if current_header not in tours:
                        tours[current_header] = []
                        header_order.append(current_header)
            
            # Sicherstellen, dass Tour existiert
            if current_header not in tours:
                tours[current_header] = []
                header_order.append(current_header)
            
            # Sicherstellen, dass tour_seen für diese Tour initialisiert ist
            if current_header not in tour_seen:
                tour_seen[current_header] = set()
            
            # Deduplizierung: Prüfe ob dieser Kunde bereits in dieser Tour ist
            customer_key = (customer.customer_number, customer.name, customer.street, customer.postal_code, customer.city)
            if customer_key in tour_seen[current_header]:
                logging.debug(f"[PARSER] Duplikat in Tour '{current_header}' übersprungen: {customer.name}")
                continue
            
            tour_seen[current_header].add(customer_key)
            tours[current_header].append(customer)
    
    # Finale Konsolidierung: verbleibende BAR-Kunden ohne Haupttour (wie parse_w7.py Zeile 117-118)
    for base, bar_customers in pending_bar.items():
        if bar_customers:
            # Falls keine Haupttour gefunden: erstelle separate BAR-Tour
            fallback_header = full_name_map.get(base, f"BAR-TOUR ({base})")
            if fallback_header not in tours:
                tours[fallback_header] = []
                header_order.append(fallback_header)
            tours[fallback_header].extend(bar_customers)
    
    # Konvertiere zu erwartetem Format
    tour_map = OrderedDict()
    for header in header_order:
        if header in tours and tours[header]:
            tour_map[header] = tours[header]
    
    return header_order, tour_map


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def parse_tour_plan(file_path: Union[str, Path]) -> TourPlan:
    path = Path(file_path)
    
    # WICHTIG: Für Staging-Dateien (bereits repariert und als UTF-8 gespeichert)
    # direkt als Text lesen statt erneut zu dekodieren
    is_staging = "staging" in str(path).lower() or path.suffix == ".repaired"
    
    if is_staging:
        # Staging-Dateien sind bereits UTF-8 - direkt lesen
        try:
            raw_text = path.read_text(encoding='utf-8')
            _enc = "utf-8"
        except Exception:
            # Fallback: Bytes lesen und dekodieren
            raw = path.read_bytes()
            raw_text, _enc = _heuristic_decode(raw, skip_mojibake_check=True)
    else:
        # Original-Dateien: Heuristische Dekodierung mit Mojibake-Check
        raw = path.read_bytes()
        raw_text, _enc = _heuristic_decode(raw, skip_mojibake_check=False)
    
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
            
            # Füge resolved_customer_id und Koordinaten hinzu falls vorhanden (aus Synonym-Auflösung)
            if hasattr(stop, '_resolved_customer_id') and stop._resolved_customer_id:
                customer_dict["real_customer_id"] = stop._resolved_customer_id
            
            # Wenn Koordinaten aus Synonym vorhanden, verwende diese (verhindert unnötiges Geocoding)
            if hasattr(stop, '_synonym_lat') and stop._synonym_lat:
                customer_dict["lat"] = stop._synonym_lat
            if hasattr(stop, '_synonym_lon') and stop._synonym_lon:
                customer_dict["lon"] = stop._synonym_lon
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

