# 🔍 Analyse: Key-Mismatch bei Sub-Routen-Generator

**Datum:** 2025-11-16  
**Status:** 🔴 KRITISCH  
**Fehler:** `[SELECT-TOUR] ❌ Tour nicht gefunden: workflow-W-07_00`

---

## 🎯 Problem-Identifikation

### Fehler aus Console-Log

```
[SELECT-TOUR] Key: workflow-W-07_00
[SELECT-TOUR] allTourCustomers keys: 
  - 'workflow-W-07.00 Uhr Tour-A'
  - 'workflow-W-07.00 Uhr Tour-B'
  - ...
[SELECT-TOUR] ❌ Tour nicht gefunden: workflow-W-07_00
```

### Root Cause: Inkonsistente Key-Generierung

**Problem 1: Zwei verschiedene Key-Generierungs-Methoden**

1. **`generateTourKey()` (Zeile 2202-2214):**
   ```javascript
   function generateTourKey(tour) {
       const baseId = extractBaseTourId(tour);  // "W-07.00"
       const normalizedBaseId = baseId.replace(/[^a-zA-Z0-9-]/g, '_');  // "W_07_00" (Punkt → Unterstrich)
       return subRoute 
           ? `workflow-${normalizedBaseId}-${subRoute}`  // "workflow-W_07_00-A"
           : `workflow-${normalizedBaseId}`;            // "workflow-W_07_00"
   }
   ```
   - **Ergebnis:** `workflow-W_07_00` (mit Unterstrich `_`)

2. **Manuelle Key-Generierung in `processTour()` (Zeile 4964):**
   ```javascript
   const subRouteKey = `workflow-${tour.tour_id}-${subRouteLetter}`;
   // tour.tour_id = "W-07.00 Uhr Tour"
   // subRouteLetter = "A"
   // Ergebnis: "workflow-W-07.00 Uhr Tour-A"
   ```
   - **Ergebnis:** `workflow-W-07.00 Uhr Tour-A` (mit Punkt `.` und "Uhr Tour")

**Problem 2: `renderToursFromMatch()` verwendet `generateTourKey()`**

- Zeile 2593: `const key = generateTourKey(tourMeta);`
- Erstellt Keys: `workflow-W_07_00-A` (mit Unterstrich)
- ABER: Sub-Routen wurden in Zeile 4964 mit `workflow-W-07.00 Uhr Tour-A` erstellt
- **Mismatch!**

**Problem 3: `selectTour()` findet Key nicht**

- Zeile 3360-3379: `selectTour(key)` sucht nach `workflow-W-07_00`
- Verfügbare Keys: `workflow-W-07.00 Uhr Tour-A`, `workflow-W-07.00 Uhr Tour-B`
- **Key existiert nicht!**

---

## 🔧 Lösung

### Fix 1: Vereinheitliche Key-Generierung

**Alle Key-Generierung muss `generateTourKey()` verwenden!**

**Zeile 4964 ändern:**
```javascript
// VORHER (FALSCH):
const subRouteKey = `workflow-${tour.tour_id}-${subRouteLetter}`;

// NACHHER (RICHTIG):
const tourMeta = {
    tour_id: tour.tour_id,
    _base_tour_id: tour._base_tour_id || extractBaseTourId(tour),
    _sub_route: subRouteLetter
};
const subRouteKey = generateTourKey(tourMeta);
```

### Fix 2: `selectTour()` robuster machen

**Fallback-Mechanismus für Key-Mismatch:**

```javascript
function selectTour(key) {
    console.log('[SELECT-TOUR] Key:', key);
    console.log('[SELECT-TOUR] allTourCustomers keys:', Object.keys(allTourCustomers));
    
    if (!key) {
        console.warn('[SELECT-TOUR] Kein Key angegeben');
        return;
    }
    
    // Versuche 1: Exakter Match
    if (allTourCustomers[key]) {
        activeTourKey = key;
        updateTourListSelection(key);
        renderTourDetails(allTourCustomers[key]);
        return;
    }
    
    // Versuche 2: Ähnlicher Key (für Sub-Routen)
    const similarKey = Object.keys(allTourCustomers).find(k => {
        // Normalisiere beide Keys für Vergleich
        const normalizedKey = key.replace(/[^a-zA-Z0-9-]/g, '_');
        const normalizedK = k.replace(/[^a-zA-Z0-9-]/g, '_');
        return normalizedK.includes(normalizedKey) || normalizedKey.includes(normalizedK);
    });
    
    if (similarKey) {
        console.warn(`[SELECT-TOUR] Key-Mismatch erkannt: "${key}" → "${similarKey}"`);
        activeTourKey = similarKey;
        updateTourListSelection(similarKey);
        renderTourDetails(allTourCustomers[similarKey]);
        return;
    }
    
    // Versuche 3: Erste verfügbare Tour mit ähnlichem Base-ID
    const baseId = extractBaseTourId({ tour_id: key.replace('workflow-', '') });
    const matchingKey = Object.keys(allTourCustomers).find(k => {
        const tour = allTourCustomers[k];
        const tourBaseId = extractBaseTourId(tour);
        return tourBaseId === baseId;
    });
    
    if (matchingKey) {
        console.warn(`[SELECT-TOUR] Fallback: Erste Tour mit Base-ID "${baseId}": "${matchingKey}"`);
        activeTourKey = matchingKey;
        updateTourListSelection(matchingKey);
        renderTourDetails(allTourCustomers[matchingKey]);
        return;
    }
    
    // Versuche 4: Erste verfügbare Tour
    const firstKey = Object.keys(allTourCustomers)[0];
    if (firstKey) {
        console.warn(`[SELECT-TOUR] Fallback: Erste verfügbare Tour: "${firstKey}"`);
        activeTourKey = firstKey;
        updateTourListSelection(firstKey);
        renderTourDetails(allTourCustomers[firstKey]);
        return;
    }
    
    // Keine Tour gefunden
    console.error('[SELECT-TOUR] ❌ Tour nicht gefunden:', key);
    console.log('[SELECT-TOUR] Verfügbare Keys:', Object.keys(allTourCustomers));
}
```

---

## 📊 Vergleich: Vorher vs. Nachher

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| **Key-Format in `processTour()`** | `workflow-W-07.00 Uhr Tour-A` | `workflow-W_07_00-A` |
| **Key-Format in `renderToursFromMatch()`** | `workflow-W_07_00-A` | `workflow-W_07_00-A` |
| **Konsistenz** | ❌ Inkonsistent | ✅ Konsistent |
| **`selectTour()` findet Key** | ❌ Nein | ✅ Ja (mit Fallback) |
| **Stabilität** | ❌ Fehler | ✅ Robust |

---

## 🧪 Test-Plan

1. **Sub-Routen generieren**
   - CSV hochladen mit W-Touren
   - "Routen optimieren" klicken
   - Sub-Routen werden generiert

2. **Key-Konsistenz prüfen**
   - Console: `Object.keys(allTourCustomers)`
   - **Erwartung:** Alle Keys haben Format `workflow-W_XX_XX-A` (mit Unterstrich)

3. **Tour-Auswahl testen**
   - Auf Tour in Liste klicken
   - **Erwartung:** Tour wird ausgewählt, kein Fehler

4. **Fallback testen**
   - Alten Key aus localStorage laden (z.B. `workflow-W-07_00`)
   - **Erwartung:** Ähnliche Tour wird gefunden (z.B. `workflow-W_07_00-A`)

---

## 📝 Implementierung

**Dateien:**
- `frontend/index.html` - Zeile 4964 (Key-Generierung)
- `frontend/index.html` - Zeile 3360-3395 (`selectTour()` Funktion)

**Änderungen:**
1. Zeile 4964: `generateTourKey()` verwenden statt manueller String-Konkatenation
2. Zeile 3360-3395: `selectTour()` mit Fallback-Mechanismus erweitern

---

**Erstellt:** 2025-11-16  
**Status:** ⏳ WARTET AUF IMPLEMENTIERUNG

