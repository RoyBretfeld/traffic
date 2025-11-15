# Tour-Management: Manuelle Tour-Verschiebung

**Status:** 🚧 Geplant  
**Priorität:** Medium  
**Datum:** 2025-01-09

---

## Ziel

Die Möglichkeit, **Touren manuell zu verschieben/anpassen**, nachdem sie automatisch erstellt wurden.

### Anwendungsfälle:
- Touren zwischen Fahrern umverteilen
- Kunden von einer Tour zu einer anderen verschieben
- Touren manuell zusammenführen oder aufteilen
- Reihenfolge von Kunden innerhalb einer Tour ändern

---

## Features

### 1. Drag & Drop für Kunden
- **Kunde aus Tour A** → **in Tour B verschieben**
- Automatische Neuberechnung der Zeiten für beide Touren
- Warnung wenn Zeit-Constraint überschritten wird

### 2. Kunde innerhalb Tour verschieben
- **Reihenfolge ändern** durch Drag & Drop in Kunden-Liste
- Automatische Neuberechnung der Route

### 3. Tour zusammenführen
- **Tour A + Tour B** → **neue Tour C**
- Automatische Route-Optimierung für neue Tour

### 4. Tour aufteilen
- **Tour A** → **Tour A1 + Tour A2**
- Automatische Aufteilung mit Zeit-Constraints

### 5. Undo/Redo
- **Rückgängig** für letzte Änderung
- **Wiederholen** für rückgängig gemachte Änderung

---

## UI-Design

### In Tour-Details-Panel

```
┌─────────────────────────────────────┐
│ Tour: W-07.00 Uhr Tour A            │
│ ⏱️ 55.5 Min (OHNE Rückfahrt)        │
├─────────────────────────────────────┤
│ Kunden (drag & drop aktiviert):     │
│ ┌─────────────────────────────────┐ │
│ │ 🖱️ Kunde 1 (Fröbelstraße 20)   │ │ ← Drag Handle
│ │ 🖱️ Kunde 2 (Tharandter Str.)    │ │
│ │ 🖱️ Kunde 3 (Fröbelstraße 51a)   │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ Aktionen:                            │
│ [Tour zusammenführen] [Tour aufteilen]│
│ [Zurück] [Wiederholen]              │
└─────────────────────────────────────┘
```

### Drop-Zone für andere Tour

```
┌─────────────────────────────────────┐
│ Tour: W-09.00 Uhr Tour B            │
│ ⏱️ 48.2 Min                          │
├─────────────────────────────────────┤
│ 👉 Hier ablegen (Drop-Zone)          │ ← Visuelles Feedback
│                                     │
│ 🖱️ Kunde 4                          │
│ 🖱️ Kunde 5                          │
└─────────────────────────────────────┘
```

---

## Implementierung

### Phase 1: Drag & Drop Library

Verwende **SortableJS** für Drag & Drop:
```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
```

### Phase 2: Tour-Management API

#### `routes/tour_management_api.py`
```python
@router.post("/api/tour/move-customer")
async def move_customer(
    from_tour_id: str,
    to_tour_id: str,
    customer_id: str,
    new_position: Optional[int] = None
):
    """
    Verschiebt einen Kunden von einer Tour zu einer anderen.
    
    - Validiert Zeit-Constraints nach Verschiebung
    - Gibt Warnung zurück wenn Constraint überschritten
    """
    pass

@router.post("/api/tour/reorder-customers")
async def reorder_customers(
    tour_id: str,
    new_order: List[str]  # Liste von customer_ids in neuer Reihenfolge
):
    """
    Ändert die Reihenfolge von Kunden innerhalb einer Tour.
    
    - Berechnet neue Route
    - Aktualisiert Zeiten
    """
    pass

@router.post("/api/tour/merge")
async def merge_tours(
    tour_ids: List[str]
):
    """
    Führt mehrere Touren zusammen.
    
    - Optimiert neue Route
    - Prüft Zeit-Constraints
    """
    pass

@router.post("/api/tour/split")
async def split_tour(
    tour_id: str,
    split_at_customer: str
):
    """
    Teilt eine Tour an einem bestimmten Kunden auf.
    
    - Erstellt zwei neue Touren
    - Optimiert beide Routen
    """
    pass
```

### Phase 3: Undo/Redo System

#### `frontend/tour-history.js`
```javascript
class TourHistory {
    constructor() {
        this.history = [];
        this.currentIndex = -1;
    }
    
    push(state) {
        // Entferne alle Einträge nach currentIndex (wenn Undo gemacht wurde)
        this.history = this.history.slice(0, this.currentIndex + 1);
        this.history.push(JSON.parse(JSON.stringify(state))); // Deep copy
        this.currentIndex++;
    }
    
    undo() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            return this.history[this.currentIndex];
        }
        return null;
    }
    
    redo() {
        if (this.currentIndex < this.history.length - 1) {
            this.currentIndex++;
            return this.history[this.currentIndex];
        }
        return null;
    }
}
```

---

## Validierung

### Nach jeder Änderung:
1. **Zeit-Check:** Neue Tour ≤ 65 Min (ohne Rückfahrt)?
2. **Stopp-Check:** Alle Kunden noch vorhanden?
3. **Route-Check:** Route noch gültig?

### Warnungen:
- ⚠️ **Tour überschreitet Zeit-Constraint** → Orange Badge
- ⚠️ **Kunde kann nicht verschoben werden** (z.B. BAR-Kunde muss in bestimmter Tour bleiben)

---

## Nächste Schritte

1. ✅ Dokumentation erstellt (dieses Dokument)
2. ⬜ SortableJS integrieren
3. ⬜ Drag & Drop für Kunden implementieren
4. ⬜ API-Endpoints erstellen
5. ⬜ Undo/Redo System implementieren
6. ⬜ Validierung und Warnungen
7. ⬜ Tests

---

**Hinweis:** Dies ist eine geplante Feature. Die Implementierung kann schrittweise erfolgen.

