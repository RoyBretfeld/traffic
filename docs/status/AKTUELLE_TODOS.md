# 🚀 FAMO TrafficApp - Aktuelle ToDo-Liste

## 🔥 **BLOCKER** (Sofort beheben)

### 1. **CSV-zu-Datenbank Import mit Geocoding**
- **Status:** ⚠️ Teilweise vorhanden, aber nicht vollständig funktional
- **Problem:** CSV Bulk Processor existiert, aber Geocoding ist deaktiviert
- **Dateien:** `docs/csv_bulk_processor.py`, `backend/services/geocode.py`
- **Schritte:**
  - [ ] Geocoding in CSV Bulk Processor aktivieren
  - [ ] Cache-System für Koordinaten optimieren
  - [ ] Batch-Import aller CSV-Dateien testen
- **Akzeptanz:** Alle CSV-Dateien werden mit korrekten Koordinaten in DB importiert

### 2. **Multi-Tour Generator reparieren**
- **Status:** ❌ Defekt nach gestern's Änderungen
- **Problem:** Endpoint `/tour/{tour_id}/generate_multi_ai` funktioniert nicht
- **Dateien:** `backend/app.py` (Zeile ~1724)
- **Schritte:**
  - [ ] Debugging-Output analysieren
  - [ ] Datenbank-Tabellen-Namen korrigieren
  - [ ] API-Response testen
- **Akzeptanz:** Multi-Tour Generator erstellt erfolgreich Sub-Touren

## 🔴 **HOCH** (Diese Woche)

### 3. **Kunden-Markierungen auf Karte**
- **Status:** ⚠️ Karte funktioniert, aber keine Kunden-Markierungen
- **Problem:** Frontend zeigt nur FAMO-Marker, keine Kunden
- **Dateien:** `frontend/index.html` (JavaScript)
- **Schritte:**
  - [ ] API-Endpoint für Kunden-Daten mit Koordinaten
  - [ ] JavaScript-Funktion für Kunden-Markierungen
  - [ ] Marker-Styling (verschiedene Farben für Tour-Typen)
- **Akzeptanz:** Alle Kunden werden als Marker auf der Karte angezeigt

### 4. **Daten-Refresh-Probleme beheben**
- **Status:** ❌ Frontend aktualisiert Daten nicht korrekt
- **Problem:** Nach CSV-Upload werden Daten nicht sofort angezeigt
- **Dateien:** `frontend/index.html` (refreshData Funktion)
- **Schritte:**
  - [ ] API-Calls debuggen
  - [ ] Daten-Validierung verbessern
  - [ ] Error-Handling implementieren
- **Akzeptanz:** Nach Upload werden sofort alle neuen Daten angezeigt

### 5. **BAR-Kunden-Darstellung korrigieren**
- **Status:** ❌ BAR-Kunden werden nicht korrekt hervorgehoben
- **Problem:** Spezielle Kennzeichnung für BAR-Kunden fehlt
- **Dateien:** `frontend/index.html`, `backend/app.py`
- **Schritte:**
  - [ ] BAR-Flag in Datenbank prüfen
  - [ ] Frontend-Styling für BAR-Kunden
  - [ ] Karten-Marker für BAR-Kunden
- **Akzeptanz:** BAR-Kunden sind deutlich als solche erkennbar

## 🟡 **MITTEL** (Nächste Woche)

### 6. **Tour-Routen auf Karte visualisieren**
- **Status:** ❌ Routen werden nicht auf Karte gezeichnet
- **Problem:** Keine Verbindungslinien zwischen Kunden
- **Dateien:** `frontend/index.html`, `backend/services/real_routing.py`
- **Schritte:**
  - [ ] GeoJSON-Route-Format implementieren
  - [ ] Leaflet-Polyline für Routen
  - [ ] Route-Optimierung anzeigen
- **Akzeptanz:** Tour-Routen werden als Linien auf der Karte gezeigt

### 7. **Routing-System optimieren**
- **Status:** ⚠️ Teilweise implementiert, aber Fallback aktiv
- **Problem:** Luftlinien-Fallback noch aktiv
- **Dateien:** `backend/services/real_routing.py`
- **Schritte:**
  - [ ] ORS-API-Integration testen
  - [ ] Fallback entfernen
  - [ ] Error-Handling verbessern
- **Akzeptanz:** Nur echte Straßenrouten, keine Luftlinien

## 🟢 **NIEDRIG** (Später)

### 8. **Performance-Optimierung**
- **Status:** ⚠️ Langsame API-Responses
- **Problem:** Große Datenmengen verlangsamen App
- **Schritte:**
  - [ ] Datenbank-Indizes optimieren
  - [ ] API-Pagination implementieren
  - [ ] Frontend-Lazy-Loading
- **Akzeptanz:** App reagiert schnell auch bei vielen Daten

### 9. **Erweiterte KI-Features**
- **Status:** ⚠️ KI-Integration vorhanden, aber nicht voll genutzt
- **Problem:** KI-Parser wird nicht optimal eingesetzt
- **Schritte:**
  - [ ] KI-Modelle optimieren
  - [ ] Automatische Tour-Optimierung
  - [ ] Intelligente Adress-Korrektur
- **Akzeptanz:** KI verbessert automatisch Tour-Planung

---

## 📋 **Nächste Schritte**

1. **Sofort:** CSV-zu-DB Import reparieren
2. **Heute:** Multi-Tour Generator debuggen
3. **Diese Woche:** Karten-Features vervollständigen
4. **Nächste Woche:** Routing-System optimieren

**Letzte Aktualisierung:** $(Get-Date -Format "dd.MM.yyyy HH:mm")
