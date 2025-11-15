"""
Test-Code für KI-Codechecker Demo.
Enthält ABSICHTLICH bekannte Fehlermuster aus LESSONS_LOG!
"""

def process_tour_data(tour_data):
    """
    Verarbeitet Tour-Daten - ENTHÄLT BEKANNTE FEHLER!
    """
    # ❌ FEHLER 1: Keine Array-Validierung (LESSONS_LOG Pattern: Missing Defensive Checks)
    tour_data.forEach(lambda stop: print(stop))  # Kein Array.isArray() Check!
    
    # ❌ FEHLER 2: Keine Null-Checks (LESSONS_LOG Pattern: Defensive Programming)
    customer = tour_data['customer']
    print(customer.name)  # Kein if customer is not None!
    
    # ❌ FEHLER 3: Fehlende Schema-Validierung (LESSONS_LOG Pattern: Schema-Drift)
    # Zugriff auf DB-Spalte ohne zu prüfen ob sie existiert
    result = db.execute("SELECT next_attempt FROM geo_fail")  # Spalte könnte fehlen!
    
    # ❌ FEHLER 4: Memory Leak potential (LESSONS_LOG Pattern: Event Listener)
    # Simulierter Event Listener (in Python unüblich, aber Konzept zählt)
    def cleanup():
        pass  # Event Listener nicht entfernt!
    
    return tour_data


def calculate_distance_without_fallback(start, end):
    """
    Berechnet Distanz via OSRM - OHNE Fallback!
    """
    # ❌ FEHLER 5: Kein OSRM-Timeout-Handling (LESSONS_LOG Pattern: OSRM-Timeout)
    response = osrm_client.get_route(start, end)  # Kein try-except, kein Fallback auf Haversine!
    
    return response['distance']


def api_handler_without_validation(request):
    """
    API-Handler ohne Validierung - API-Kontrakt-Bruch!
    """
    # ❌ FEHLER 6: Keine Request-Validierung (LESSONS_LOG Pattern: API-Kontrakt-Brüche)
    data = request.json()  # Kein try-except, keine Validierung
    stops = data['stops']  # KeyError möglich!
    
    # Backend erwartet 'stops', Frontend sendet 'subRoutes' -> Kontrakt-Bruch!
    result = generate_subroutes(stops)
    
    return result


def browser_feature_without_detection():
    """
    Nutzt moderne Browser-Features ohne Check.
    """
    # ❌ FEHLER 7: Keine Browser-Kompatibilität (LESSONS_LOG Pattern: Browser-Compat)
    # In Python unüblich, aber Konzept für Frontend:
    # window.BroadcastChannel() ohne Check ob verfügbar!
    pass

