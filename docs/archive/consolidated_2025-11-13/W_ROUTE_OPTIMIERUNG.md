# W-Route Optimierung mit KI-basiertem Geocoding-Clustering

## Übersicht

Die W-Routen (z.B. W-07.00, W-09.00, W-11.00) haben eine **höhere Priorität** und müssen intelligent optimiert werden. Sie werden mit **Geocoding-Clustern** und **KI-basierter Logistik** zu sinnvollen Routen kombiniert, die bestimmte Zeit-Constraints einhalten.

## Anforderungen

### 1. W-Routen Priorisierung
- **W-Routen erscheinen oben in der Liste** (bereits implementiert)
- **W-Routen haben höhere Priorität** bei der Optimierung
- **W-Routen werden als erstes optimiert** (vor normalen Touren)

### 2. DB-First Geocoding-Strategie ⚠️ **WICHTIG**

**Diese Strategie ist bereits implementiert und wird für ALLE Touren (inkl. W-Routen) verwendet!**

- **1. Schritt: Datenbank prüfen** (`geo_get(address)`)
  - Wenn Adresse bereits in `geo_cache` Tabelle → **Direkt verwenden**
  - **Keine API-Calls** für bereits geocodierte Adressen
- **2. Schritt: Live-Geocoding** (nur wenn nicht in DB)
  - Geoapify API aufrufen (`geocode_address(address)`)
  - Ergebnis sofort in DB speichern (`geo_upsert(...)`)
- **3. Schritt: Beim nächsten Mal**
  - Adresse kommt **automatisch aus der DB** (Schritt 1)
  - **Keine unnötigen API-Calls**

**Vorteile**:
  - ⚡ Schneller (DB-Lookup < 1ms vs. API-Call ~200ms)
  - 💰 Günstiger (weniger API-Calls = weniger Kosten)
  - ✅ Deterministisch (gleiche Adresse = immer gleiche Koordinaten)
  - 📴 Offline-fähig (bereits geocodierte Adressen auch ohne Internet)

> **📖 Siehe auch**: `docs/GEOCODING_DETERMINISM.md` für vollständige Dokumentation der DB-First-Strategie

**Implementierung**:
```python
# In routes/workflow_api.py (bereits implementiert, Zeile 370-405)
if address:
    # SCHRITT 1: Zuerst DB prüfen (schnell)
    geo_result = geo_get(address)
    
    if geo_result:
        # In DB gefunden → direkt verwenden
        customer['lat'] = geo_result['lat']
        customer['lon'] = geo_result['lon']
        # ✅ KEIN API-CALL!
    else:
        # Nicht in DB → Geoapify aufrufen (live)
        geo_result = geocode_address(address)
        
        if geo_result:
            # Geoapify erfolgreich → direkt in DB speichern
            geo_upsert(
                address=address,
                lat=geo_result['lat'],
                lon=geo_result['lon'],
                source="geoapify",
                company_name=customer.get('name')
            )
            # ✅ Beim nächsten Mal: Aus DB (Schritt 1)
```

### 3. Depot (Start/Ende)
- **Startpunkt**: FAMO Depot
  - Adresse: `Stuttgarter Str. 33, 01189 Dresden`
  - Koordinaten: `51.0111988, 13.7016485`
- **Endpunkt**: FAMO Depot (gleicher Standort)
- **Jede Route startet und endet am Depot**

### 3. Zeit-Constraints
- **Max. Gesamtzeit pro Route**: **60-65 Minuten**
  - Inkludiert: Fahrzeit + Servicezeit
  - **Exkludiert**: Rückfahrt zum Depot (wird nach den 60-65 Minuten addiert)
- **Servicezeit pro Kunde**: **2 Minuten Upload-Zeit**
  - Jeder Kundenstopp: 2 Minuten Verweilzeit
  - Wird zur Gesamtzeit addiert

### 4. Geocoding-Clustering
- **Geografische Gruppierung** von Kunden
- **Clustering-Algorithmus**:
  - Basierend auf Koordinaten (lat/lon)
  - Verwendet Haversine-Distanz oder OSRM-Straßendistanz
  - Ziel: Kunden in geografischer Nähe zusammenfassen

### 5. KI-basierte Optimierung
- **LLM (GPT-4o-mini)** für intelligente Routenplanung
- **OSRM-Integration** für echte Straßendistanzen
- **Multi-Tour-Generierung**: Eine W-Route kann in mehrere Sub-Touren aufgeteilt werden (A, B, C...)

## Technische Implementierung

### Architektur

```
W-Route Input (CSV)
    ↓
[Parser] → Tour-Extraktion (W-07.00, W-09.00, ...)
    ↓
[DB-First Geocoding] → Alle Adressen mit Koordinaten
    ├─ geo_get(address) → Prüfe Datenbank
    ├─ Falls nicht gefunden → geocode_address(address) → Live-Geocoding
    └─ geo_upsert(...) → Speichere in DB (für nächstes Mal)
    ↓
[Geocoding-Cluster] → Geografische Gruppierung
    ↓
[KI-Optimizer] → Intelligente Routenplanung
    ├─ OSRM-Distanzmatrix berechnen
    ├─ LLM-Prompt mit Constraints
    └─ Route-Sequenz optimieren
    ↓
[Time-Validator] → Prüfung: < 60-65 Minuten?
    ├─ Falls Überschreitung → Tour splitten (A, B, C...)
    └─ Depot-Integration (Start/Ende)
    ↓
[Output] → Optimierte W-Routen (JSON)
```

### Dateien

#### 1. **`services/w_route_optimizer.py`** (NEU)
```python
"""
W-Route Optimizer für FAMO TrafficApp
Optimiert W-Routen mit KI-basiertem Geocoding-Clustering
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from services.llm_optimizer import LLMOptimizer
from backend.services.optimization_rules import OptimizationRules, default_rules
import math
import httpx
import asyncio

# FAMO Depot
FAMO_DEPOT = {
    "name": "FAMO Depot",
    "address": "Stuttgarter Str. 33, 01189 Dresden",
    "lat": 51.0111988,
    "lon": 13.7016485
}

@dataclass
class WRouteOptimizationResult:
    """Ergebnis der W-Route-Optimierung"""
    tours: List[Dict[str, Any]]  # Liste von optimierten Touren (A, B, C...)
    total_customers: int
    total_driving_time_minutes: float
    total_service_time_minutes: float
    warnings: List[str]
    optimization_method: str  # "llm" oder "fallback"

class WRouteOptimizer:
    """Optimiert W-Routen mit KI und Geocoding-Clustering"""
    
    def __init__(self, llm_optimizer: LLMOptimizer = None):
        self.llm_optimizer = llm_optimizer or LLMOptimizer()
        self.rules = default_rules
        # W-Route spezifische Regeln
        self.max_total_time_minutes = 65  # Max. 65 Minuten (inkl. Servicezeit)
        self.service_time_per_customer_minutes = 2  # 2 Min pro Kunde
    
    def optimize_w_route(
        self, 
        tour_id: str, 
        customers: List[Dict[str, Any]]
    ) -> WRouteOptimizationResult:
        """
        Optimiert eine W-Route mit KI und Clustering
        
        Args:
            tour_id: Tour-ID (z.B. "W-07.00")
            customers: Liste von Kunden (mit oder ohne Koordinaten)
            
        Returns:
            WRouteOptimizationResult mit optimierten Sub-Touren
        """
        # 1. DB-First Geocoding für Kunden ohne Koordinaten
        from repositories.geo_repo import get as geo_get, upsert as geo_upsert
        from backend.services.geocode import geocode_address
        
        for customer in customers:
            if not customer.get('lat') or not customer.get('lon'):
                # Baue Adresse
                address = customer.get('address') or ", ".join(filter(None, [
                    customer.get('street', '').strip(),
                    f"{customer.get('postal_code', '')} {customer.get('city', '')}".strip()
                ]))
                
                if address:
                    # DB-First: Prüfe geo_cache
                    geo_result = geo_get(address)
                    if geo_result:
                        customer['lat'] = geo_result['lat']
                        customer['lon'] = geo_result['lon']
                    else:
                        # Nicht in DB → Live-Geocoding
                        geo_result = geocode_address(address)
                        if geo_result and geo_result.get('lat') and geo_result.get('lon'):
                            # Speichere in DB
                            geo_upsert(
                                address=address,
                                lat=geo_result['lat'],
                                lon=geo_result['lon'],
                                source="geoapify",
                                company_name=customer.get('name')
                            )
                            customer['lat'] = geo_result['lat']
                            customer['lon'] = geo_result['lon']
        
        # 2. Filtere Kunden mit Koordinaten
        valid_customers = [
            c for c in customers 
            if c.get('lat') and c.get('lon')
        ]
        
        if not valid_customers:
            return WRouteOptimizationResult(
                tours=[],
                total_customers=0,
                total_driving_time_minutes=0,
                total_service_time_minutes=0,
                warnings=["Keine Kunden mit Koordinaten"],
                optimization_method="none"
            )
        
        # 2. Geocoding-Clustering
        clusters = self._cluster_customers(valid_customers)
        
        # 3. KI-Optimierung pro Cluster
        optimized_tours = []
        total_driving_time = 0
        total_service_time = len(valid_customers) * self.service_time_per_customer_minutes
        warnings = []
        
        for cluster_idx, cluster in enumerate(clusters):
            # Depot am Anfang und Ende hinzufügen
            route_with_depot = self._add_depot_points(cluster)
            
            # KI-Optimierung
            if self.llm_optimizer.enabled:
                optimized_route = self._optimize_with_llm(route_with_depot)
                method = "llm"
            else:
                optimized_route = self._optimize_fallback(route_with_depot)
                method = "fallback"
            
            # Zeitberechnung
            driving_time = self._calculate_driving_time(optimized_route)
            service_time_cluster = len(cluster) * self.service_time_per_customer_minutes
            total_time = driving_time + service_time_cluster
            
            # Prüfe Zeit-Constraint
            if total_time > self.max_total_time_minutes:
                # Tour splitten
                sub_tours = self._split_tour(optimized_route, self.max_total_time_minutes)
                for sub_idx, sub_tour in enumerate(sub_tours):
                    tour_name = f"{tour_id} {chr(65 + cluster_idx)}{chr(65 + sub_idx) if len(sub_tours) > 1 else ''}"
                    optimized_tours.append({
                        "tour_id": tour_name,
                        "stops": sub_tour,
                        "driving_time_minutes": self._calculate_driving_time(sub_tour),
                        "service_time_minutes": len([s for s in sub_tour if s.get('type') != 'depot']) * self.service_time_per_customer_minutes,
                        "customer_count": len([s for s in sub_tour if s.get('type') != 'depot'])
                    })
            else:
                tour_name = f"{tour_id} {chr(65 + cluster_idx)}" if len(clusters) > 1 else tour_id
                optimized_tours.append({
                    "tour_id": tour_name,
                    "stops": optimized_route,
                    "driving_time_minutes": driving_time,
                    "service_time_minutes": service_time_cluster,
                    "customer_count": len(cluster)
                })
                total_driving_time += driving_time
        
        return WRouteOptimizationResult(
            tours=optimized_tours,
            total_customers=len(valid_customers),
            total_driving_time_minutes=total_driving_time,
            total_service_time_minutes=total_service_time,
            warnings=warnings,
            optimization_method=method
        )
    
    def _cluster_customers(self, customers: List[Dict]) -> List[List[Dict]]:
        """Gruppiert Kunden geografisch"""
        # Einfacher K-Means-ähnlicher Algorithmus basierend auf Koordinaten
        # TODO: Implementierung mit scikit-learn oder custom Algorithmus
        # Für jetzt: Ein Cluster pro Route (später erweitern)
        return [customers]  # Platzhalter
    
    def _add_depot_points(self, customers: List[Dict]) -> List[Dict]:
        """Fügt Depot am Start und Ende hinzu"""
        depot_start = {
            **FAMO_DEPOT,
            "type": "depot",
            "sequence": 0,
            "is_depot": True
        }
        depot_end = {
            **FAMO_DEPOT,
            "type": "depot",
            "sequence": len(customers) + 1,
            "is_depot": True
        }
        
        route = [depot_start]
        for i, customer in enumerate(customers):
            customer["sequence"] = i + 1
            customer["is_depot"] = False
            route.append(customer)
        route.append(depot_end)
        
        return route
    
    def _optimize_with_llm(self, route: List[Dict]) -> List[Dict]:
        """Optimiert Route mit LLM"""
        # Depot entfernen für LLM (wird später wieder hinzugefügt)
        stops = [s for s in route if not s.get('is_depot')]
        
        result = self.llm_optimizer.optimize_route(stops, region="Dresden")
        
        if result.confidence_score > 0.7:
            optimized_stops = [stops[i] for i in result.optimized_route]
            # Depot wieder hinzufügen
            return self._add_depot_points(optimized_stops)
        
        return route  # Fallback
    
    def _optimize_fallback(self, route: List[Dict]) -> List[Dict]:
        """Fallback: Nearest-Neighbor Optimierung"""
        stops = [s for s in route if not s.get('is_depot')]
        if len(stops) <= 1:
            return route
        
        # Nearest-Neighbor Algorithmus
        optimized = [stops[0]]
        remaining = stops[1:]
        
        while remaining:
            last = optimized[-1]
            nearest = min(remaining, key=lambda s: self._haversine_distance(
                last.get('lat'), last.get('lon'),
                s.get('lat'), s.get('lon')
            ))
            optimized.append(nearest)
            remaining.remove(nearest)
        
        return self._add_depot_points(optimized)
    
    def _calculate_driving_time(self, route: List[Dict]) -> float:
        """Berechnet Fahrzeit mit OSRM"""
        # TODO: OSRM-Integration für echte Straßendistanzen
        # Für jetzt: Haversine * 1.3 (Stadtdurchschnitt) / 50 km/h
        total_distance_km = 0
        for i in range(len(route) - 1):
            dist = self._haversine_distance(
                route[i].get('lat'), route[i].get('lon'),
                route[i+1].get('lat'), route[i+1].get('lon')
            )
            total_distance_km += dist * 1.3  # Faktor für Stadtverkehr
        
        # Durchschnittsgeschwindigkeit: 50 km/h in der Stadt
        driving_time_minutes = (total_distance_km / 50.0) * 60
        return driving_time_minutes
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechnet Luftlinie-Distanz in km"""
        R = 6371.0  # Erdradius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    def _split_tour(self, route: List[Dict], max_time: float) -> List[List[Dict]]:
        """Teilt Route in Sub-Touren auf falls Zeit überschritten"""
        # TODO: Intelligente Splitting-Logik
        # Für jetzt: Einfache Aufteilung nach Anzahl Kunden
        stops = [s for s in route if not s.get('is_depot')]
        depot_start = [s for s in route if s.get('is_depot') and s.get('sequence') == 0][0]
        depot_end = [s for s in route if s.get('is_depot') and s.get('sequence') == len(stops) + 1][0]
        
        # Grobe Schätzung: Max. 20 Kunden pro Tour (60 Min / 3 Min pro Kunde)
        max_customers_per_tour = 20
        sub_tours = []
        
        for i in range(0, len(stops), max_customers_per_tour):
            sub_stops = stops[i:i + max_customers_per_tour]
            sub_route = [depot_start] + sub_stops + [depot_end]
            sub_tours.append(sub_route)
        
        return sub_tours
```

#### 2. **Integration in `routes/workflow_api.py`**

```python
# In workflow_upload() Funktion, nach Parsing:
from services.w_route_optimizer import WRouteOptimizer

# W-Route Optimierung
w_route_optimizer = WRouteOptimizer(llm_optimizer)

for tour in tour_data.get('tours', []):
    tour_name = tour.get('name', '')
    
    # Prüfe ob W-Route
    if tour_name.startswith('W-'):
        # W-Route Optimierung
        result = w_route_optimizer.optimize_w_route(
            tour_id=tour_name,
            customers=tour.get('customers', [])
        )
        
        # Ersetze ursprüngliche Tour mit optimierten Sub-Touren
        for optimized_tour in result.tours:
            optimized_tours.append({
                "tour_id": optimized_tour["tour_id"],
                "stops": optimized_tour["stops"],
                "stop_count": optimized_tour["customer_count"],
                "driving_time": optimized_tour["driving_time_minutes"],
                "service_time": optimized_tour["service_time_minutes"]
            })
    else:
        # Normale Tour (bestehende Logik)
        # ...
```

## Zeitberechnung

### Formel
```
Gesamtzeit = Fahrzeit + Servicezeit

Fahrzeit = Σ(Strecke[i→i+1] / Geschwindigkeit)
Servicezeit = Anzahl_Kunden × 2_Minuten

Gesamtzeit (inkl. Rückfahrt) = Gesamtzeit + Rückfahrt_Zum_Depot
```

### Beispiel
- **30 Kunden** in einer Route
- **Servicezeit**: 30 × 2 = 60 Minuten
- **Fahrzeit**: 45 Minuten (bis letzter Kunde)
- **Rückfahrt**: 15 Minuten (vom letzten Kunden zum Depot)
- **Gesamtzeit**: 60 + 45 + 15 = **120 Minuten** (wird aufgeteilt in 2 Touren)

### Constraint-Prüfung
```
IF Gesamtzeit > 65 Minuten:
    → Tour splitten in A, B, C...
    → Jede Sub-Tour < 65 Minuten
```

## Geocoding-Clustering Algorithmus

### Ziel
- Kunden in geografischer Nähe zusammenfassen
- Minimale Gesamtfahrzeit
- Ausgewogene Touren (nicht eine Tour mit 50, andere mit 5 Kunden)

### Methoden
1. **K-Means Clustering** (basierend auf lat/lon)
2. **Hierarchical Clustering** (agglomerativ)
3. **DBSCAN** (Density-based, für ungleichmäßige Verteilung)

### Implementierung (geplant)
```python
from sklearn.cluster import KMeans
import numpy as np

def cluster_customers_kmeans(customers: List[Dict], n_clusters: int = None) -> List[List[Dict]]:
    """K-Means Clustering für Kunden"""
    coords = np.array([
        [c.get('lat'), c.get('lon')] 
        for c in customers 
        if c.get('lat') and c.get('lon')
    ])
    
    if n_clusters is None:
        # Automatische Cluster-Anzahl basierend auf Kundenanzahl
        n_clusters = max(1, len(customers) // 20)  # ~20 Kunden pro Cluster
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(coords)
    
    clusters = [[] for _ in range(n_clusters)]
    valid_idx = 0
    for customer in customers:
        if customer.get('lat') and customer.get('lon'):
            cluster_idx = labels[valid_idx]
            clusters[cluster_idx].append(customer)
            valid_idx += 1
    
    return [c for c in clusters if c]  # Leere Cluster entfernen
```

## LLM-Prompt für W-Route-Optimierung

### Prompt-Struktur
```
Du optimierst eine W-Route für FAMO TrafficApp.

Constraints:
- Max. Gesamtzeit: 60-65 Minuten (inkl. Servicezeit, exkl. Rückfahrt)
- Servicezeit pro Kunde: 2 Minuten
- Start/Ende: FAMO Depot (51.0111988, 13.7016485)
- OSRM-Straßendistanzen sind verfügbar (nicht Luftlinie)

Kunden ({n}):
{customer_list}

OSRM-Distanzmatrix:
{distance_matrix}

Optimiere die Route so dass:
1. Minimale Gesamtfahrzeit
2. Logische geografische Reihenfolge
3. Zeit-Constraint eingehalten wird
4. Depot am Start und Ende

Gib die optimale Sequenz zurück: [0, 3, 1, 2, ...]
```

## API-Endpoint (geplant)

### POST `/api/w-route/optimize`
```json
{
  "tour_id": "W-07.00",
  "customers": [
    {
      "name": "Kunde 1",
      "lat": 51.0500,
      "lon": 13.7373,
      "address": "Adresse 1"
    },
    ...
  ]
}
```

### Response
```json
{
  "success": true,
  "tours": [
    {
      "tour_id": "W-07.00 A",
      "stops": [...],
      "driving_time_minutes": 45.5,
      "service_time_minutes": 60,
      "total_time_minutes": 105.5,
      "customer_count": 30
    },
    {
      "tour_id": "W-07.00 B",
      "stops": [...],
      "driving_time_minutes": 40.2,
      "service_time_minutes": 40,
      "total_time_minutes": 80.2,
      "customer_count": 20
    }
  ],
  "optimization_method": "llm",
  "warnings": []
}
```

## Status

### ✅ Bereits implementiert
- [x] **DB-First Geocoding-Strategie** in `routes/workflow_api.py`
  - `geo_get(address)` prüft zuerst die Datenbank
  - `geocode_address(address)` nur wenn nicht in DB
  - `geo_upsert(...)` speichert Ergebnis in DB
  - Funktioniert bereits für alle Touren (inkl. W-Routen)
- [x] W-Routen erscheinen oben in der Liste
- [x] W-Routen haben andere Farbe (Blau)
- [x] Depot-Koordinaten definiert
- [x] LLM-Optimizer vorhanden
- [x] OSRM-Integration vorhanden

### 🔨 Zu implementieren
- [ ] `services/w_route_optimizer.py` erstellen
- [ ] Geocoding-Clustering implementieren
- [ ] Zeitberechnung mit OSRM
- [ ] Tour-Splitting bei Überschreitung
- [ ] Integration in `routes/workflow_api.py`
- [ ] Frontend-Anzeige für optimierte Sub-Touren
- [ ] API-Endpoint `/api/w-route/optimize`

## Nächste Schritte

1. **Phase 1**: Basis-Implementierung (`w_route_optimizer.py`)
2. **Phase 2**: Geocoding-Clustering (K-Means)
3. **Phase 3**: OSRM-Zeitberechnung
4. **Phase 4**: Tour-Splitting-Logik
5. **Phase 5**: Frontend-Integration
6. **Phase 6**: Testing & Optimierung

## Referenzen

- `services/llm_optimizer.py` - LLM-Optimizer
- `backend/services/optimization_rules.py` - Optimierungsregeln
- `config/static/app_config.json` - Depot-Koordinaten
- `routes/workflow_api.py` - Workflow-Integration

---

**Erstellt**: 2025-01-XX
**Status**: Dokumentation erstellt, Implementierung geplant
**Autor**: AI Assistant (Cursor)

