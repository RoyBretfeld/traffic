from __future__ import annotations
from collections import OrderedDict
from typing import Dict, List, Tuple

# Importiere Datenstrukturen aus dem Haupt-Parser
from common.tour_data_models import TourInfo, TourStop # Importiere Datenstrukturen

def group_and_consolidate_tours(raw_tour_data: List[Tuple[str, TourStop]]) -> List[Dict]: # Rückgabe ist eine Liste von Dictionaries, nicht TourInfo
    """
    Führt das modulare Gruppieren und die BAR-Konsolidierung durch.
    
    Diese Funktion ersetzt die komplexe Schleifenlogik in _extract_tours
    durch drei stabile Phasen: Mapping, BAR-Vorbereitung und Konsolidierung.
    
    Args:
        raw_tour_data: Liste von (Header-String, TourStop-Objekt) Tupeln 
                       aus der Rohextraktion (tour_plan_raw_reader).
                       
    Returns:
        Liste der finalen TourInfo-Objekte (fertige Touren).
    """
    
    # Phase 1: Eindeutige Tour-Header mappen
    # map: header_string -> Liste[TourStop]
    tours: Dict[str, List[TourStop]] = OrderedDict()
    
    # Phase 2: BAR-Kunden (noch nicht zugeordnet)
    # map: base_name -> Liste[TourStop]
    pending_bar: Dict[str, List[TourStop]] = {}
    
    # map: base_name -> vollständiger header_string der ERSTEN Haupttour
    full_name_map: Dict[str, str] = {}
    
    # Liste der Header in Reihenfolge des Auftretens
    header_order: List[str] = []

    for header, stop in raw_tour_data:
        base = TourInfo.get_base_name(header) # Annahme: get_base_name existiert in TourInfo oder ist eine separate Utility
        
        if stop.is_bar_stop:
            # BAR-Stop: Wird nur im pending_bar Puffer gesammelt
            pending_bar.setdefault(base, []).append(stop)
            
        else:
            # Normale (Haupt-) Tour
            
            # A. Eindeutige Tourenzuweisung (inkl. Zeit)
            if header not in tours:
                tours[header] = []
                header_order.append(header)
                
            # B. Speicherung des Headers für BAR-Zuordnung (nur die ERSTE Version zählt)
            if base not in full_name_map:
                full_name_map[base] = header
            
            # C. Kunden zur Haupttour hinzufügen
            tours[header].append(stop)

    # Phase 3: BAR-Konsolidierung
    # Durchlaufe die gesammelten BAR-Kunden
    for base, customers in pending_bar.items():
        if not customers:
            continue

        # Finde den Header der ERSTEN passenden Haupttour
        target_header = full_name_map.get(base)
        
        if target_header and target_header in tours:
            # Füge BAR-Kunden am ANFANG der Haupttour ein
            tours[target_header] = customers + tours[target_header]
            
        else:
            # Wenn keine passende Haupttour gefunden, füge sie als separate
            # BAR-Tour am Ende an (z.B. für "BAR-TOUR UNBEKANNT")
            
            # Verwende den BAR-Header als Fallback
            # WICHTIG: Erzeuge einen eindeutigen Header, falls der base_name generisch ist
            fallback_header = f"BAR-TOUR ({base})" 
            if fallback_header not in tours:
                tours[fallback_header] = []
                header_order.append(fallback_header)
            tours[fallback_header].extend(customers)

    # Phase 4: TourInfo-Objekte erstellen
    final_tours = []
    for header in header_order:
        stops = tours.get(header, [])
        if not stops:
            continue
            
        # Hier müssten die parsing-Hilfsfunktionen aus tour_plan_parser.py
        # aufgerufen werden, um die TourInfo-Objekte zu erstellen.
        # Da diese in diesem Modul nicht verfügbar sind, geben wir nur die Maps zurück,
        # damit der Haupt-Parser die TourInfo-Objekte bauen kann.
        
        final_tours.append({
            "header": header,
            "customers": stops
        })

    return final_tours # Rückgabe der Liste der Touren-Maps
