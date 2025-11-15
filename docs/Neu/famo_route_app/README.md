# FAMO Route Planner – Offline MVP

Dieses Repository enthält einen minimalen Prototypen einer Routenplanungs‑Webapp.

## Funktionen

* Upload von CSV‑Dateien mit Kundendaten (KdNr, Name, Straße, PLZ, Ort).
* Normalisierung deutscher Sonderzeichen und Entfernen von Duplikaten.
* Einfache Routenberechnung mit Haversine‑Distanzen und Sweep‑Clustering:
  * Start am FAMO‑Depot (Dresden).
  * Maximal 60 Minuten Fahrzeit pro Tour, inklusive 2 Minuten Servicezeit pro Kunde.
  * Nearest‑Neighbor‑Heuristik für die Reihenfolge der Stopps.
* Visualisierung der Touren als Liste im Browser; Bar‑Kunden werden farblich hervorgehoben.

## Installation

1. **Abhängigkeiten installieren**

   Wechseln Sie ins Verzeichnis `backend` und installieren Sie die Python‑Abhängigkeiten:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Anwendung starten**

   ```bash
   python -m app
   ```

   Der Server läuft anschließend unter `http://127.0.0.1:5000/`.

3. **Weboberfläche verwenden**

   Öffnen Sie die URL in Ihrem Browser und laden Sie eine CSV‑Datei hoch. Die berechneten Touren werden im Browser angezeigt.

## Hinweise

* Dieses MVP nutzt keine externe Geokodierung oder Live‑Verkehrsdaten; die Reisedauer wird anhand von Luftlinienentfernung und einer konstanten Geschwindigkeit (50 km/h) geschätzt.
* Die Koordinaten der Kunden sollten in der CSV in den Spalten `lat` und `lon` enthalten sein; andernfalls wird der Standort des Depots genutzt, was zu ungenauen Ergebnissen führt.
* Die Routen‑Heuristiken sind einfach gehalten (Sweep‑Algorithmus【581186749357520†L720-L727】, Nearest‑Neighbor); in realen Anwendungen kommen komplexere Verfahren zum Einsatz【581186749357520†L247-L256】.
