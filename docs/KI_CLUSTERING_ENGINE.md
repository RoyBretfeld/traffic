# KI-Clustering-Engine für Sub-Routen-Generierung

## Übersicht

Die KI-Clustering-Engine ist das Herzstück der Sub-Routen-Generierung. Sie verwendet **OpenAI GPT-4o-mini** für intelligente geografische Clustering und Routenoptimierung.

**Zweck:** Große Touren (z.B. W-07.00 mit 30 Adressen) in mehrere optimierte Sub-Routen aufteilen, die jeweils < 60 Minuten dauern.

---

## Wie funktioniert es? (Schritt für Schritt)

### 1. Eingabe: Tour mit vielen Stopps

**Beispiel: W-07.00 mit 30 Adressen**

```json
{
  "tour_id": "W-07.00 Uhr Tour",
  "stops": [
    {"name": "Kunde 1", "lat": 51.0492, "lon": 13.6984, "address": "Fröbelstraße 1, Dresden"},
    {"name": "Kunde 2", "lat": 51.0504, "lon": 13.7373, "address": "Hauptstraße 5, Dresden"},
    // ... 28 weitere Stopps
  ]
}
```

---

### 2. KI-Analyse: Geografisches Clustering

**Was macht die KI?**

Die KI analysiert:
1. **Geografische Nähe:** Welche Stopps sind nah beieinander?
2. **Straßen-Connectivity:** Welche Stopps sind über Straßen gut erreichbar?
3. **Zeit-Limits:** Wie kann ich Gruppen bilden, die jeweils < 60 Min dauern?

**Prompt an die KI:**
```
Du bist ein Routenplanungs-Experte. Analysiere 30 Stopps in Dresden:

Stopps mit Koordinaten:
0: Kunde 1 - Fröbelstraße 1 (51.0492, 13.6984)
1: Kunde 2 - Hauptstraße 5 (51.0504, 13.7373)
...

Ziel:
- Erstelle optimale Reihenfolge für alle Stopps
- Berücksichtige geografische Nähe
- Start/Ende: FAMO-Depot (51.0111988, 13.7016485)
- Max. 60 Minuten pro Route

Gib zurück:
- Optimierte Reihenfolge als Index-Liste
- Begründung deiner Entscheidung
```

**KI-Antwort (Beispiel):**
```json
{
  "optimized_route": [5, 12, 3, 7, 1, 15, 8, 22, 11, 4, 16, 9, 23, 6, 18, 2, 14, 20, 13, 19, 17, 10, 24, 21, 25, 26, 27, 28, 29, 0],
  "reasoning": "Ich habe die Stopps in drei geografische Cluster aufgeteilt: Nord-Dresden (Stopps 5,12,3,7,1), Zentrum (Stopps 15,8,22,11,4), und Süd-Dresden (Rest). Innerhalb jedes Clusters habe ich die optimale Reihenfolge berechnet.",
  "estimated_total_time_minutes": 105.5
}
```

---

### 3. Zeitberechnung: Ist Splitting nötig?

**Formel:**
```
Gesamtzeit = Fahrzeit + Service-Zeit
Fahrzeit = Summe aller Distanzen zwischen Stopps (über Straßen)
Service-Zeit = Anzahl_Stopps × 2 Minuten
```

**Beispiel für 30 Stopps:**
```
Fahrzeit (optimiert): 45.5 Minuten
Service-Zeit: 30 × 2 = 60 Minuten
─────────────────────────────────
Gesamtzeit: 105.5 Minuten

→ ÜBER 60 MINUTEN! → Splitting erforderlich
```

---

### 4. Intelligentes Splitting

**Strategie:** Nicht einfach sequenziell, sondern intelligent basierend auf KI-Clustering

**Beispiel-Ergebnis:**
```
Original: W-07.00 (30 Stopps, 105.5 Min)
  ↓
Sub-Route A: Stopps [5, 12, 3, 7, 1, 15, 8, 22, 11, 4]
  → 10 Stopps, 58 Minuten ✅
  → Cluster: Nord-Dresden + Zentrum-Nord

Sub-Route B: Stopps [16, 9, 23, 6, 18, 2, 14, 20, 13, 19]
  → 10 Stopps, 59 Minuten ✅
  → Cluster: Zentrum-Süd

Sub-Route C: Stopps [17, 10, 24, 21, 25, 26, 27, 28, 29, 0]
  → 10 Stopps, 60 Minuten ✅
  → Cluster: Süd-Dresden
```

**Wichtig:** Die KI hat bereits geclustert → Splitting nutzt diese Cluster

---

### 5. Ergebnis: Optimierte Sub-Routen

**Finale Ausgabe:**
```json
[
  {
    "tour_id": "W-07.00 Uhr Tour",
    "sub_route": "A",
    "stops": [10 optimierte Stopps],
    "total_time_minutes": 58,
    "reasoning": "Nord-Dresden Cluster, optimierte Reihenfolge basierend auf Straßen-Distanzen"
  },
  {
    "tour_id": "W-07.00 Uhr Tour",
    "sub_route": "B",
    "stops": [10 optimierte Stopps],
    "total_time_minutes": 59,
    "reasoning": "Zentrum-Süd Cluster"
  },
  {
    "tour_id": "W-07.00 Uhr Tour",
    "sub_route": "C",
    "stops": [10 optimierte Stopps],
    "total_time_minutes": 60,
    "reasoning": "Süd-Dresden Cluster"
  }
]
```

---

## Technische Details

### KI-Modell

- **Model:** OpenAI GPT-4o-mini
- **Temperature:** 0.3 (niedrig für konsistente Ergebnisse)
- **Max Tokens:** 1000
- **Response Format:** JSON (strukturiert)

### Fallback-Strategie

**Wenn KI nicht verfügbar:**
1. **Nearest-Neighbor Algorithmus**
   - Starte mit erstem Stopp
   - Finde nächsten unbesuchten Stopp (Haversine-Distanz)
   - Wiederhole bis alle besucht

**Wenn auch Nearest-Neighbor fehlschlägt:**
- Standard-Reihenfolge (wie in CSV)
- Warnung anzeigen

---

## Datenfluss

```
[Tour mit 30 Stopps]
    ↓
[KI-Analyse: Clustering & Optimierung]
    ↓
[Optimierte Route: Indizes [5,12,3,7,...]]
    ↓
[Zeitberechnung: 105.5 Min]
    ↓
[Über 60 Min?] → JA
    ↓
[Intelligentes Splitting in 3 Sub-Routen]
    ↓
[Ergebnis: 3 optimierte Sub-Routen < 60 Min]
```

---

## Vorteile der KI-Clustering-Engine

✅ **Intelligente Gruppierung:** Stopps werden geografisch sinnvoll gruppiert  
✅ **Optimale Reihenfolge:** KI berücksichtigt Straßen-Connectivity  
✅ **Zeit-Optimierung:** Jede Sub-Route < 60 Minuten  
✅ **Begründung:** KI erklärt warum diese Reihenfolge gewählt wurde  
✅ **Skalierbar:** Funktioniert für 10, 30, 50+ Stopps  

---

## Dateien & Code

- **Backend:** `routes/workflow_api.py` → `optimize_tour_with_ai()`
- **AI-Service:** `services/llm_optimizer.py` → `optimize_route()`
- **Frontend:** `frontend/index.html` → `generateSubRoutes()`
- **Splitting:** `frontend/index.html` → `splitTourIntoSubRoutes()`

---

## Nächste Schritte (Morgen)

1. ✅ **404-Fehler beheben** → Endpoint muss erreichbar sein
2. ✅ **KI-Response prüfen** → Wird JSON korrekt geparst?
3. ✅ **Splitting-Logik testen** → Werden Sub-Routen korrekt erstellt?
4. 🆕 **OSRM-Integration** → Straßen-Routen statt Luftlinie
5. 🆕 **Verkehrszeiten** → Unterschiedliche Routen je nach Uhrzeit

---

**Status:** ✅ Engine ist implementiert, muss noch getestet und debugged werden.

