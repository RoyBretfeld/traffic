ANWEISUNG FÜR CURSOR KI

ZIEL: Den Geocoding- und Tourenplan-Workflow bereinigen, Fehler in der Synonym-Verarbeitung beheben, den Datenfluss von Geocoder-Ergebnissen sicherstellen und die ursprüngliche Logik zur Konsolidierung von BAR-Kunden wiederherstellen/verbessern.

ALLGEMEINE ANWEISUNG FÜR DIE KI

Modell-Empfehlung: Verwende für diese Aufgabe das Modell Gemini 2.5 Flash, da es schnell und präzise im Code-Refactoring ist.

Priorität: Führe die Korrekturen in der Reihenfolge 4, 1, 2, 3 durch.

Logging: Ersetze alle print(...) durch logging-Aufrufe.

1. CSV_Recognition_Audit_Package.zip/normalize.py

AKTION: Entferne redundante/fehlerhafte Synonym- und Fuzzy-Logik.

ENTFERNEN: Lösche die beiden Definitionen der Funktion _check_synonym (die hartkodierte und die DB-abfragende Version). Die Synonym-Auflösung erfolgt zentral über common/synonyms.py:resolve_synonym.

ENTFERNEN: Lösche die ungenutzte/fehlerhafte Funktion _fuzzy_name_match.

ENTFERNEN: Entferne den hartkodierten Synonym-Check-Block aus normalize_address (Zeile 195 ff im Original):

if customer_name:
    synonym_address = _check_synonym(customer_name)
    if synonym_address:
        return synonym_address



REFACTORING (Optional, aber empfohlen): Prüfe, ob die vielen verschiedenen Adress-Korrektur-RegEx (Haupstr., Strae, etc.) und die Mojibake-Fixes (z.B. _SAFE_FIXES) in normalize_address in logischere, kleinere Unterfunktionen zerlegt werden können, um die Lesbarkeit der Hauptfunktion zu verbessern. Die Funktionalität muss dabei erhalten bleiben.

2. CSV_Recognition_Audit_Package.zip/geocode_fill.py

AKTION: Behebe den kritischen Datenfluss-Fehler (addressdetails) und implementiere Logging.

DATENFLUSS-FIX (KRITISCH): Ändere die Rückgabe der Funktion _geocode_variant (Zeile 163), um das vollständige address-Detail und das Feld _note (Quelle) aus der Nominatim-Antwort zu inkludieren. Dies ist notwendig, damit geocode_persist.py die region_ok-Logik korrekt ausführen kann.

Geänderte Rückgabe in _geocode_variant soll sein:

return {
    "lat": lat, 
    "lon": lon, 
    "address": best.get("address", {}), 
    "_note": "geocoder",
    "display_name": display_name
}



CODE CLEANUP: Ersetze alle einfachen print(...)-Anweisungen durch das Standard-Python-logging-Modul (z.B. logging.info, logging.warning, logging.error), um eine kontrollierte Ausgabe zu ermöglichen. Führe dazu import logging ein.

3. CSV_Recognition_Audit_Package.zip/tourplan_match.py

AKTION: Bereinige den Synonym-Check vor der DTO-Erstellung.

BEREINIGUNG: Stelle sicher, dass der Synonym-Check vor der DTO-Erstellung (Zeile 108 ff) die unnötige manuelle Filterung auf 'pf' oder 'bar' im customer_name nicht enthält, da resolve_synonym dies bereits selbst handhabt.

Das ist die korrigierte Logik, die beibehalten werden soll:

# Vereinfachter Check: Rufe resolve_synonym immer auf
from common.synonyms import resolve_synonym
synonym_hit = resolve_synonym(customer_name)



4. CSV_Recognition_Audit_Package.zip/tour_plan_parser.py

AKTION: Stelle die Logik zur Konsolidierung von BAR-Kunden in die zeitlich gleiche Tour wieder her oder verbessere sie.

Wiederherstellung/Verbesserung: Überprüfe und korrigiere die Logik in _extract_tours (Zeile 211 ff), die für das Mapping von BAR-Kunden (pending_bar) auf die zeitlich/namentechnisch passende Haupttour zuständig ist. Die Logik muss sicherstellen, dass alle BAR-Kunden (die oft nur den base_name teilen) in die reguläre Tour mit dem gleichen base_name und Zeitstempel (time_label/header) integriert werden, sobald diese reguläre Tour erkannt wird.

Fokusbereich in _extract_tours:

# ... In _extract_tours (BAR-Mode/Non-BAR-Mode Umschaltung) ...
if "BAR" in header.upper():
    # ... Logik bleibt ...
else:
    bar_mode = False
    current_base = base
    current_header = header
    full_name_map[base] = header
    if header not in tours:
        tours[header] = []
        order.append(header)
    # KRITISCHE LOGIK ZUR BAR-ÜBERNAHME
    if base in pending_bar and pending_bar[base]:
        # Stelle sicher, dass hier alle Kunden aus `pending_bar[base]` zur
        # aktuellen Tour (`header`) hinzugefügt und aus `pending_bar` entfernt werden.
        tours[header].extend(pending_bar.pop(base))
    # ...



Die KI soll überprüfen, ob die pending_bar.pop(base)-Logik in _extract_tours korrekt implementiert ist, um die BAR-Stops zuverlässig der ersten gefundenen Nicht-BAR-Tour mit dem gleichen base_name zuzuordnen. Wenn die ursprüngliche Logik fehlerhaft war, korrigiere sie.

Priorität der Ausführung: 4, 1, 2, 3.