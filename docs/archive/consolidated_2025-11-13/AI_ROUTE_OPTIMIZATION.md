# AI-basierte Route-Optimierung mit System-Prompts

## Übersicht

Das System verwendet **GPT-4o-mini** für intelligente Routenoptimierung mit **detailliertem Reasoning** und **geografischem Clustering**. Die AI entscheidet basierend auf definierten Regeln und erklärt ihre Entscheidungen.

## Kern-Regeln

### 1. Zeit-Constraints
- **Max. Gesamtzeit pro Route**: 60-65 Minuten
  - **Inkludiert**: Fahrzeit + Servicezeit (bis zum letzten Kunden)
  - **Exkludiert**: Rückfahrt zum Depot (wird danach addiert)
- **Servicezeit pro Kunde**: 2 Minuten Upload-Zeit
- **FAMO Depot**: Start- und Endpunkt jeder Route
  - Adresse: `Stuttgarter Str. 33, 01189 Dresden`
  - Koordinaten: `51.0111988, 13.7016485`

### 2. Geografisches Clustering
- **Gruppierung nach geografischer Nähe**
- **Straßendistanzen** (OSRM) statt Luftlinie
- **Ausgewogene Touren** (nicht eine Tour mit 50, andere mit 5 Kunden)

### 3. AI-Reasoning
- **Jede Entscheidung wird erklärt**
- **Logging der Begründung** für Debugging und Transparenz
- **Metadaten** über Clustering-Entscheidungen

## System-Prompt Struktur

### Basis-System-Prompt für Route-Optimierung

```python
SYSTEM_PROMPT_ROUTE_OPTIMIZATION = """
Du bist ein Experte für Logistik und Routenoptimierung für FAMO TrafficApp.

DEINE AUFGABE:
Optimiere Routen für LKW-Fahrer basierend auf geografischer Nähe und Zeit-Constraints.

VERBINDLICHE REGELN:

1. ZEIT-CONSTRAINTS (KRITISCH):
   - Max. Gesamtzeit pro Route: 60-65 Minuten (inkl. Servicezeit)
   - Servicezeit pro Kunde: 2 Minuten (Ladezeit)
   - Rückfahrt zum Depot zählt NICHT in die 60-65 Minuten
   - Berechnung: Fahrzeit + (Anzahl_Kunden × 2_Minuten) ≤ 65 Minuten

2. DEPOT (Start/Ende):
   - Jede Route startet bei FAMO Depot: Stuttgarter Str. 33, 01189 Dresden
   - Koordinaten: 51.0111988, 13.7016485
   - Jede Route endet beim Depot (Rückfahrt wird nach der 60-65 Min Regel addiert)

3. GEOGRAFISCHES CLUSTERING:
   - Gruppiere Kunden nach geografischer Nähe
   - Verwende OSRM-Straßendistanzen (nicht Luftlinie)
   - Ziel: Minimale Gesamtfahrzeit
   - Ausgewogene Touren: Keine Tour sollte deutlich mehr Kunden haben als andere

4. REASONING (WICHTIG):
   - Erkläre WARUM du Kunden in bestimmte Touren gruppierst
   - Erkläre WARUM du die Reihenfolge so gewählt hast
   - Erkläre WARUM du Touren splittest (falls nötig)
   - Gib geografische Begründungen (z.B. "Kunden 1-5 sind alle in Dresden-West")

FORMAT DER ANTWORT:
- JSON mit optimierter Route
- Detaillierte reasoning-Feld mit Erklärungen
- Metadaten über Clustering-Entscheidungen
"""
```

### Erweiterter System-Prompt für Multi-Tour-Generierung

```python
SYSTEM_PROMPT_MULTI_TOUR = """
Du bist ein Experte für Logistik und Routenoptimierung für FAMO TrafficApp.

DEINE AUFGABE:
Teile große Touren (z.B. W-07.00 mit 36 Kunden) in mehrere optimale Sub-Touren (A, B, C...) auf.

VERBINDLICHE REGELN:

1. ZEIT-CONSTRAINTS:
   - Max. 60-65 Minuten pro Sub-Tour (inkl. Servicezeit)
   - Servicezeit: 2 Minuten pro Kunde
   - Rückfahrt zum Depot zählt NICHT in die 60-65 Minuten
   - Berechnung für jede Sub-Tour:
     Fahrzeit_bis_letzter_Kunde + (Anzahl_Kunden × 2_Minuten) ≤ 65 Minuten

2. DEPOT-INTEGRATION:
   - Jede Sub-Tour startet bei FAMO Depot (51.0111988, 13.7016485)
   - Jede Sub-Tour endet beim Depot
   - Depot wird automatisch als erster und letzter Punkt eingefügt

3. GEOGRAFISCHES CLUSTERING:
   - Gruppiere Kunden nach geografischer Nähe
   - Verwende OSRM-Straßendistanzen für echte Fahrzeiten
   - Ziel: Minimale Gesamtfahrzeit über alle Sub-Touren
   - Ausgewogene Verteilung: Sub-Touren sollten ähnliche Größe haben

4. TOUR-SPLITTING:
   - Wenn eine Tour > 65 Minuten: Splitte in mehrere Sub-Touren
   - Naming: "W-07.00 A", "W-07.00 B", "W-07.00 C", ...
   - Jede Sub-Tour muss selbstständig funktionieren (Start/Ende Depot)

5. REASONING (KRITISCH):
   - Erkläre WARUM du bestimmte Kunden zusammen gruppierst
   - Erkläre WARUM du die Reihenfolge innerhalb einer Tour so gewählt hast
   - Erkläre WARUM du die Tour an bestimmten Stellen gesplittet hast
   - Gib konkrete geografische Begründungen

FORMAT DER ANTWORT:
{
  "tours": [
    {
      "tour_id": "W-07.00 A",
      "customer_ids": [1, 2, 3, ...],
      "driving_time_minutes": 45.5,
      "service_time_minutes": 30,
      "customer_count": 15,
      "reasoning": "Kunden 1-15 sind alle in Dresden-West und bilden ein kompaktes geografisches Cluster..."
    }
  ],
  "overall_reasoning": "Die ursprüngliche Tour W-07.00 wurde in 3 Sub-Touren gesplittet, da sie 105 Minuten gedauert hätte..."
}
"""
```

## Prompt-Erstellung im Code

### Datei: `services/llm_optimizer.py`

```python
def _get_system_prompt(self, prompt_type: str = "route_optimization") -> str:
    """Gibt den System-Prompt für verschiedene Optimierungs-Typen zurück"""
    
    prompts = {
        "route_optimization": """
Du bist ein Experte für Logistik und Routenoptimierung für FAMO TrafficApp.

DEINE AUFGABE:
Optimiere Routen für LKW-Fahrer basierend auf geografischer Nähe und Zeit-Constraints.

VERBINDLICHE REGELN:

1. ZEIT-CONSTRAINTS (KRITISCH):
   - Max. Gesamtzeit pro Route: 60-65 Minuten (inkl. Servicezeit)
   - Servicezeit pro Kunde: 2 Minuten (Ladezeit)
   - Rückfahrt zum Depot zählt NICHT in die 60-65 Minuten
   - Berechnung: Fahrzeit + (Anzahl_Kunden × 2_Minuten) ≤ 65 Minuten

2. DEPOT (Start/Ende):
   - Jede Route startet bei FAMO Depot: Stuttgarter Str. 33, 01189 Dresden
   - Koordinaten: 51.0111988, 13.7016485
   - Jede Route endet beim Depot (Rückfahrt wird nach der 60-65 Min Regel addiert)

3. GEOGRAFISCHES CLUSTERING:
   - Gruppiere Kunden nach geografischer Nähe
   - Verwende OSRM-Straßendistanzen (nicht Luftlinie)
   - Ziel: Minimale Gesamtfahrzeit
   - Ausgewogene Touren: Keine Tour sollte deutlich mehr Kunden haben als andere

4. REASONING (WICHTIG):
   - Erkläre WARUM du Kunden in bestimmte Touren gruppierst
   - Erkläre WARUM du die Reihenfolge so gewählt hast
   - Erkläre WARUM du Touren splittest (falls nötig)
   - Gib geografische Begründungen

FORMAT DER ANTWORT:
- JSON mit optimierter Route
- Detaillierte reasoning-Feld mit Erklärungen
- Metadaten über Clustering-Entscheidungen
""",
        
        "multi_tour_generation": """
Du bist ein Experte für Logistik und Routenoptimierung für FAMO TrafficApp.

DEINE AUFGABE:
Teile große Touren (z.B. W-07.00 mit 36 Kunden) in mehrere optimale Sub-Touren (A, B, C...) auf.

VERBINDLICHE REGELN:

1. ZEIT-CONSTRAINTS:
   - Max. 60-65 Minuten pro Sub-Tour (inkl. Servicezeit)
   - Servicezeit: 2 Minuten pro Kunde
   - Rückfahrt zum Depot zählt NICHT in die 60-65 Minuten
   - Berechnung: Fahrzeit_bis_letzter_Kunde + (Anzahl_Kunden × 2_Minuten) ≤ 65 Minuten

2. DEPOT-INTEGRATION:
   - Jede Sub-Tour startet bei FAMO Depot (51.0111988, 13.7016485)
   - Jede Sub-Tour endet beim Depot
   - Depot wird automatisch als erster und letzter Punkt eingefügt

3. GEOGRAFISCHES CLUSTERING:
   - Gruppiere Kunden nach geografischer Nähe
   - Verwende OSRM-Straßendistanzen für echte Fahrzeiten
   - Ziel: Minimale Gesamtfahrzeit über alle Sub-Touren
   - Ausgewogene Verteilung: Sub-Touren sollten ähnliche Größe haben

4. TOUR-SPLITTING:
   - Wenn eine Tour > 65 Minuten: Splitte in mehrere Sub-Touren
   - Naming: "W-07.00 A", "W-07.00 B", "W-07.00 C", ...
   - Jede Sub-Tour muss selbstständig funktionieren (Start/Ende Depot)

5. REASONING (KRITISCH):
   - Erkläre WARUM du bestimmte Kunden zusammen gruppierst
   - Erkläre WARUM du die Reihenfolge innerhalb einer Tour so gewählt hast
   - Erkläre WARUM du die Tour an bestimmten Stellen gesplittet hast
   - Gib konkrete geografische Begründungen

FORMAT DER ANTWORT:
{
  "tours": [
    {
      "tour_id": "W-07.00 A",
      "customer_ids": [1, 2, 3, ...],
      "driving_time_minutes": 45.5,
      "service_time_minutes": 30,
      "customer_count": 15,
      "reasoning": "Detaillierte Begründung..."
    }
  ],
  "overall_reasoning": "Gesamtbegründung..."
}
"""
    }
    
    return prompts.get(prompt_type, prompts["route_optimization"])
```

## User-Prompt Struktur

### Beispiel: Multi-Tour-Generierung

```python
def _build_multi_tour_prompt(
    self, 
    tour_id: str,
    customers: List[Dict],
    osrm_distances: Dict[str, float] = None
) -> str:
    """Erstellt User-Prompt für Multi-Tour-Generierung"""
    
    # Kunden-Liste formatieren
    customers_list = []
    for i, customer in enumerate(customers):
        customers_list.append({
            "id": i + 1,
            "name": customer.get('name', 'Unbekannt'),
            "address": customer.get('address', ''),
            "lat": customer.get('lat'),
            "lon": customer.get('lon'),
            "postal_code": customer.get('postal_code', ''),
            "city": customer.get('city', '')
        })
    
    # OSRM-Distanzmatrix (optional)
    distance_matrix_text = ""
    if osrm_distances:
        distance_matrix_text = f"""
OSRM-Straßendistanzen (in Metern):
{json.dumps(osrm_distances, indent=2)}
"""
    
    prompt = f"""
Optimiere die Route "{tour_id}" mit {len(customers)} Kunden.

KUNDEN-LISTE:
{json.dumps(customers_list, indent=2, ensure_ascii=False)}
{distance_matrix_text}

AUFGABE:
1. Teile die Kunden in mehrere Sub-Touren auf (A, B, C, ...)
2. Jede Sub-Tour muss ≤ 65 Minuten sein (inkl. Servicezeit, exkl. Rückfahrt)
3. Gruppiere geografisch nahe Kunden
4. Optimiere die Reihenfolge innerhalb jeder Sub-Tour
5. Erkläre deine Entscheidungen ausführlich

DEPOT:
- Start/Ende: FAMO Depot (51.0111988, 13.7016485)
- Adresse: Stuttgarter Str. 33, 01189 Dresden

ANTWORTE MIT JSON im folgenden Format:
{{
  "tours": [
    {{
      "tour_id": "{tour_id} A",
      "customer_ids": [1, 2, 3, ...],
      "estimated_driving_time_minutes": 45.5,
      "estimated_service_time_minutes": 30,
      "customer_count": 15,
      "reasoning": "Diese Kunden wurden gruppiert, weil sie alle in Dresden-West liegen..."
    }}
  ],
  "overall_reasoning": "Die Tour wurde in 3 Sub-Touren gesplittet, weil die Gesamtzeit 105 Minuten betragen hätte..."
}}
"""
    return prompt
```

## Reasoning-Logging

### Struktur des Reasoning-Objekts

```python
@dataclass
class OptimizationReasoning:
    """Detaillierte Begründung für Optimierungsentscheidungen"""
    clustering_decisions: List[str]  # Warum bestimmte Kunden zusammen gruppiert wurden
    sequencing_decisions: List[str]  # Warum bestimmte Reihenfolge gewählt wurde
    splitting_decisions: List[str]  # Warum Touren gesplittet wurden
    time_constraint_violations: List[str]  # Falls Constraints verletzt wurden
    geographical_analysis: str  # Geografische Analyse der Kundenverteilung
    overall_strategy: str  # Gesamtstrategie der Optimierung
```

### Beispiel-Output

```json
{
  "reasoning": {
    "overall_strategy": "Die Tour W-07.00 wurde in 3 geografische Cluster aufgeteilt: Dresden-West (A), Dresden-Ost (B), und Umland (C).",
    "clustering_decisions": [
      "Kunden 1-15 (W-07.00 A): Alle liegen in Dresden-West (PLZ 01109-01129), maximale Distanz zwischen Kunden: 8km",
      "Kunden 16-28 (W-07.00 B): Alle liegen in Dresden-Ost (PLZ 01277-01279), kompaktes Gebiet um Pirnaer Landstraße",
      "Kunden 29-36 (W-07.00 C): Umland-Gebiet (Bannewitz, Freital), weiter entfernt vom Depot"
    ],
    "sequencing_decisions": [
      "W-07.00 A: Start mit Kunde 3 (nächster zum Depot), dann spiralförmig nach außen",
      "W-07.00 B: Start mit Kunde 20 (nächster zum Depot), dann linear entlang der Hauptstraße"
    ],
    "splitting_decisions": [
      "Ursprüngliche Tour hätte 105 Minuten gedauert (45 Min Fahrzeit + 72 Min Servicezeit).",
      "Splitting in 3 Sub-Touren: A=65 Min, B=62 Min, C=58 Min (jeweils inkl. Servicezeit)"
    ],
    "time_constraint_violations": [],
    "geographical_analysis": "Kunden sind in 3 klar abgrenzbare geografische Cluster aufgeteilt. Keine Überlappungen."
  }
}
```

## Implementierung

### Datei: `services/w_route_optimizer.py` (Erweitert)

```python
async def optimize_with_ai_reasoning(
    self,
    tour_id: str,
    customers: List[Dict],
    osrm_distances: Dict[str, float] = None
) -> Dict[str, Any]:
    """Optimiert Route mit AI und detailliertem Reasoning"""
    
    # 1. System-Prompt laden
    system_prompt = self.llm_optimizer._get_system_prompt("multi_tour_generation")
    
    # 2. User-Prompt erstellen
    user_prompt = self._build_multi_tour_prompt(tour_id, customers, osrm_distances)
    
    # 3. LLM-Call mit Reasoning-Anforderung
    response = self.llm_optimizer.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,  # Niedrig für konsistente Ergebnisse
        max_tokens=2000,  # Mehr Tokens für detailliertes Reasoning
        response_format={"type": "json_object"}  # Strukturierte Antwort
    )
    
    # 4. Parse Response
    result = json.loads(response.choices[0].message.content)
    
    # 5. Reasoning extrahieren und loggen
    reasoning = result.get("reasoning", {})
    self._log_reasoning(tour_id, reasoning, result.get("tours", []))
    
    return result
```

## Integration in Workflow

### Datei: `routes/workflow_api.py`

```python
@router.post("/api/workflow/generate-multi-tours")
async def generate_multi_tours(request: Request):
    """Generiert Multi-Touren mit AI und Reasoning"""
    
    body = await request.json()
    tour_id = body.get("tour_id")
    customers = body.get("customers", [])
    
    # W-Route Optimizer mit AI
    from services.w_route_optimizer import WRouteOptimizer
    optimizer = WRouteOptimizer(llm_optimizer)
    
    # Optimierung mit Reasoning
    result = await optimizer.optimize_with_ai_reasoning(
        tour_id=tour_id,
        customers=customers,
        osrm_distances=calculate_osrm_distances(customers)
    )
    
    # Reasoning im Response inkludieren
    return JSONResponse({
        "success": True,
        "tours": result.get("tours", []),
        "reasoning": result.get("reasoning", {}),
        "overall_reasoning": result.get("overall_reasoning", "")
    })
```

## Vorteile der System-Prompt-basierten Lösung

1. **Transparenz**: AI erklärt jede Entscheidung
2. **Anpassbarkeit**: Prompts können leicht angepasst werden
3. **Konsistenz**: System-Prompts garantieren konsistente Entscheidungen
4. **Debugging**: Reasoning-Logs helfen bei Problemanalyse
5. **Vertrauen**: Benutzer sehen, warum AI bestimmte Entscheidungen getroffen hat

## Nächste Schritte

1. ✅ System-Prompts definiert
2. ✅ Reasoning-Struktur erstellt
3. 🔨 Integration in `services/w_route_optimizer.py`
4. 🔨 OSRM-Distanzmatrix-Integration
5. 🔨 Frontend-Anzeige für Reasoning
6. 🔨 Testing mit echten Daten

