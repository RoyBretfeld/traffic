"""
Tour Consolidator - Vereinigt kleine T-Touren (z.B. T10 mit ≤3 Stopps)

Logik:
- T-Touren mit ≤3 Stopps werden zusammengelegt
- Zeit ist hier irrelevant (Fahrer kommen am Nachmittag zurück)
- Nur Touren mit gleicher Tour-Nummer werden zusammengelegt (T10 + T10 → T10)
"""

from __future__ import annotations
from typing import List, Dict, Any
import re


def consolidate_t10_tours(tours: List[Dict[str, Any]], max_stops: int = 3) -> List[Dict[str, Any]]:
    """
    Vereinigt kleine T-Touren (T10, T17, etc.) wenn sie ≤ max_stops Stopps haben.
    
    Args:
        tours: Liste von Tour-Dictionaries mit tour_id und stops/customers
        max_stops: Maximale Anzahl Stopps für Zusammenlegung (Default: 3)
    
    Returns:
        Konsolidierte Touren-Liste
    """
    if not tours:
        return tours
    
    # Trenne T-Touren und andere Touren
    t_tours: Dict[str, List[Dict[str, Any]]] = {}  # tour_number -> [tours]
    other_tours: List[Dict[str, Any]] = []
    
    for tour in tours:
        tour_id = tour.get('tour_id', '') or tour.get('name', '')
        
        # Prüfe ob T-Tour (T10, T17, etc.)
        t_match = re.match(r'^T(\d+)', tour_id.upper())
        if t_match:
            tour_number = t_match.group(1)  # z.B. "10" aus "T10"
            
            # Zähle Stopps
            stops_count = len(tour.get('stops', [])) or len(tour.get('customers', []))
            
            # Nur zusammenlegen wenn ≤ max_stops Stopps
            if stops_count <= max_stops:
                if tour_number not in t_tours:
                    t_tours[tour_number] = []
                t_tours[tour_number].append(tour)
            else:
                # Zu groß → als normale Tour behalten
                other_tours.append(tour)
        else:
            # Keine T-Tour → behalten
            other_tours.append(tour)
    
    # Konsolidiere T-Touren pro Tour-Nummer
    consolidated_tours: List[Dict[str, Any]] = []
    
    for tour_number, tour_list in t_tours.items():
        if len(tour_list) == 0:
            continue
        
        if len(tour_list) == 1:
            # Nur eine Tour → behalten
            consolidated_tours.append(tour_list[0])
        else:
            # Mehrere Touren → zusammenlegen
            merged_tour = _merge_t10_tours(tour_list, tour_number)
            if merged_tour:
                consolidated_tours.append(merged_tour)
                print(f"[CONSOLIDATOR] T{tour_number}: {len(tour_list)} Touren → 1 zusammengelegte Tour ({len(merged_tour.get('stops', merged_tour.get('customers', [])))} Stopps)")
    
    # Füge konsolidierte T-Touren und andere Touren zusammen
    final_tours = consolidated_tours + other_tours
    
    return final_tours


def _merge_t10_tours(tours: List[Dict[str, Any]], tour_number: str) -> Dict[str, Any]:
    """
    Vereint mehrere T-Touren mit gleicher Nummer zu einer Tour.
    
    Args:
        tours: Liste von T-Touren mit gleicher Nummer (z.B. mehrere "T10" Touren)
        tour_number: Tour-Nummer (z.B. "10" für T10)
    
    Returns:
        Zusammengelegte Tour
    """
    if not tours:
        return {}
    
    # Nimm erste Tour als Basis
    merged = tours[0].copy()
    
    # Neue Tour-ID
    merged['tour_id'] = f'T{tour_number}'
    merged['name'] = f'T{tour_number}'
    
    # Sammle alle Stopps/Kunden
    all_stops = []
    all_customers = []
    
    for tour in tours:
        # Stopps sammeln
        stops = tour.get('stops', [])
        if stops:
            all_stops.extend(stops)
        
        # Customers sammeln (falls vorhanden)
        customers = tour.get('customers', [])
        if customers:
            all_customers.extend(customers)
    
    # Aktualisiere Stopps/Customers
    if all_stops:
        merged['stops'] = all_stops
    if all_customers:
        merged['customers'] = all_customers
    
    # Metadaten aktualisieren
    merged['_consolidated'] = True
    merged['_original_tour_count'] = len(tours)
    
    # Zeiten zusammenrechnen (falls vorhanden)
    total_driving_time = sum(t.get('driving_time_minutes', 0) or 0 for t in tours)
    total_service_time = sum(t.get('service_time_minutes', 0) or 0 for t in tours)
    total_time = sum(t.get('total_time_minutes', 0) or 0 for t in tours)
    
    if total_driving_time > 0:
        merged['driving_time_minutes'] = total_driving_time
    if total_service_time > 0:
        merged['service_time_minutes'] = total_service_time
    if total_time > 0:
        merged['total_time_minutes'] = total_time
    
    # BAR-Status: True wenn mindestens eine Tour BAR ist
    merged['is_bar_tour'] = any(t.get('is_bar_tour', False) for t in tours)
    
    return merged

