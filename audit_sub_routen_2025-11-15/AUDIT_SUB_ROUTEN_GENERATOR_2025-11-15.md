# 🔍 Audit-Report: Sub-Routen-Generator – Sub-Routen verschwinden nach Erstellung

**Datum:** 2025-11-15  
**Schweregrad:** 🔴 KRITISCH  
**Status:** Problem identifiziert, Lösungsvorschläge erstellt

---

## 📋 Executive Summary

**Symptom:** Sub-Routen werden erfolgreich generiert und angezeigt, verschwinden aber nach kurzer Zeit wieder. Die ursprünglichen Haupttouren erscheinen erneut.

**Root Cause:** Inkonsistenz zwischen `workflowResult` und `allTourCustomers` beim State-Management. Sub-Routen werden nur in `workflowResult` gespeichert, aber `allTourCustomers` wird nicht synchronisiert.

**Impact:** Sub-Routen-Generator ist nicht produktiv nutzbar, da generierte Routen verloren gehen.

---

## 🔍 Detaillierte Analyse

### 1. Problem-Identifikation

#### 1.1 Datenfluss beim Erstellen von Sub-Routen

**Datei:** `frontend/index.html`

**Schritt 1: Sub-Routen werden generiert** (Zeile 4738)
```javascript
updateToursWithSubRoutes(allSubRoutes);
```

**Schritt 2: `updateToursWithSubRoutes()` aktualisiert nur `workflowResult`** (Zeile 5218-5310)
```javascript
function updateToursWithSubRoutes(subRoutes) {
    // ...
    if (workflowResult && workflowResult.tours) {
        workflowResult.tours = workflowResult.tours.map(tour => {
            // Ersetze Tour mit Sub-Routen
            // ...
        }).flat();
    }
    
    // Rendere neu
    renderToursFromMatch(workflowResult);
    saveToursToStorage();
}
```

**Problem:** `allTourCustomers` wird NICHT aktualisiert!

#### 1.2 State-Management: Zwei parallele Datenstrukturen

**Struktur 1: `workflowResult`**
```javascript
workflowResult = {
    tours: [
        { tour_id: "W-07.00 A", stops: [...], customers: [...] },
        { tour_id: "W-07.00 B", stops: [...], customers: [...] }
    ]
}
```

**Struktur 2: `allTourCustomers`**
```javascript
allTourCustomers = {
    "workflow-0": { name: "W-07.00", customers: [...] },
    "workflow-1": { name: "W-08.00", customers: [...] }
}
```

**Problem:** Beide Strukturen werden parallel verwendet, aber nicht synchron gehalten!

#### 1.3 Wiederherstellung beim Seiten-Reload

**Datei:** `frontend/index.html`, Zeile 434-484

```javascript
function restoreToursFromStorage() {
    const savedWorkflow = localStorage.getItem('workflowResult');
    const savedCustomers = localStorage.getItem('allTourCustomers');
    
    if (savedWorkflow) {
        workflowResult = JSON.parse(savedWorkflow);  // ✅ Enthält Sub-Routen
    }
    
    if (savedCustomers) {
        allTourCustomers = JSON.parse(savedCustomers);  // ❌ Enthält NOCH alte Haupttouren!
    }
    
    // Rendere Touren neu
    if (workflowResult && workflowResult.tours && workflowResult.tours.length > 0) {
        renderToursFromMatch(workflowResult);  // ✅ Rendert Sub-Routen
    } else if (Object.keys(allTourCustomers).length > 0) {
        renderToursFromCustomers();  // ❌ Rendert alte Haupttouren!
    }
}
```

**Problem:** Wenn `allTourCustomers` vorhanden ist, wird `renderToursFromCustomers()` aufgerufen, was die alten Haupttouren rendert!

#### 1.4 `renderToursFromMatch()` löscht nicht alle alten Einträge

**Datei:** `frontend/index.html`, Zeile 2104-2113

```javascript
function renderToursFromMatch(matchData) {
    // Lösche alte allTourCustomers-Einträge
    Object.keys(allTourCustomers).forEach(key => {
        if (key.startsWith('workflow-')) {  // ❌ Nur 'workflow-' Keys werden gelöscht!
            delete allTourCustomers[key];
        }
    });
    // ...
}
```

**Problem:** Wenn `allTourCustomers` Keys hat, die NICHT mit 'workflow-' beginnen, bleiben diese erhalten!

---

## 🎯 Root Cause Analysis

### Hauptproblem: Inkonsistenz zwischen `workflowResult` und `allTourCustomers`

1. **Sub-Routen werden nur in `workflowResult` gespeichert**
   - `updateToursWithSubRoutes()` aktualisiert nur `workflowResult.tours`
   - `allTourCustomers` wird nicht aktualisiert

2. **Beim Seiten-Reload werden beide Strukturen geladen**
   - `workflowResult` enthält Sub-Routen ✅
   - `allTourCustomers` enthält noch alte Haupttouren ❌

3. **`restoreToursFromStorage()` priorisiert `allTourCustomers`**
   - Wenn `allTourCustomers` vorhanden ist, wird `renderToursFromCustomers()` aufgerufen
   - Dies überschreibt die Sub-Routen mit den alten Haupttouren

4. **`renderToursFromMatch()` löscht nicht alle alten Einträge**
   - Nur Keys mit 'workflow-' Prefix werden gelöscht
   - Andere Keys bleiben erhalten und können die Sub-Routen überschreiben

---

## 💡 Lösungsvorschläge

### Lösung 1: `allTourCustomers` synchronisieren (EMPFOHLEN)

**Datei:** `frontend/index.html`, Funktion `updateToursWithSubRoutes()`

**Änderung:** Nach dem Aktualisieren von `workflowResult.tours` auch `allTourCustomers` aktualisieren.

```javascript
function updateToursWithSubRoutes(subRoutes) {
    // ... bestehender Code ...
    
    // WICHTIG: Aktualisiere auch allTourCustomers!
    if (workflowResult && workflowResult.tours) {
        // Lösche alte Einträge für diese Touren
        const baseTourIds = new Set();
        workflowResult.tours.forEach(tour => {
            const baseId = tour._base_tour_id || tour.tour_id.split(' ')[0];
            baseTourIds.add(baseId);
        });
        
        // Lösche alle Einträge, die zu diesen Touren gehören
        Object.keys(allTourCustomers).forEach(key => {
            const tour = allTourCustomers[key];
            const tourBaseId = tour._base_tour_id || (tour.name || '').split(' ')[0];
            if (baseTourIds.has(tourBaseId)) {
                delete allTourCustomers[key];
            }
        });
        
        // Erstelle neue Einträge für Sub-Routen
        workflowResult.tours.forEach((tour, index) => {
            const key = `workflow-${index}`;
            allTourCustomers[key] = {
                name: tour.tour_id,
                customers: tour.customers || [],
                stops: tour.stops || [],
                isBarTour: tour.is_bar_tour || false,
                _base_tour_id: tour._base_tour_id,
                _sub_route: tour._sub_route,
                _tour_color: tour._tour_color,
                // ... alle anderen Felder ...
            };
        });
    }
    
    // Rendere neu
    renderToursFromMatch(workflowResult);
    saveToursToStorage();
}
```

**Vorteile:**
- ✅ Beide Datenstrukturen bleiben synchron
- ✅ Keine Breaking Changes
- ✅ Funktioniert mit bestehendem Code

**Risiko:** Niedrig (nur State-Management verbessert)

---

### Lösung 2: `restoreToursFromStorage()` priorisiert `workflowResult`

**Datei:** `frontend/index.html`, Funktion `restoreToursFromStorage()`

**Änderung:** Wenn `workflowResult` vorhanden ist, IMMER `renderToursFromMatch()` aufrufen, auch wenn `allTourCustomers` vorhanden ist.

```javascript
function restoreToursFromStorage() {
    // ... bestehender Code ...
    
    // WICHTIG: Priorisiere workflowResult über allTourCustomers!
    if (workflowResult && workflowResult.tours && workflowResult.tours.length > 0) {
        // Lösche alte allTourCustomers-Einträge, die zu diesen Touren gehören
        const baseTourIds = new Set();
        workflowResult.tours.forEach(tour => {
            const baseId = tour._base_tour_id || tour.tour_id.split(' ')[0];
            baseTourIds.add(baseId);
        });
        
        Object.keys(allTourCustomers).forEach(key => {
            const tour = allTourCustomers[key];
            const tourBaseId = tour._base_tour_id || (tour.name || '').split(' ')[0];
            if (baseTourIds.has(tourBaseId)) {
                delete allTourCustomers[key];
            }
        });
        
        renderToursFromMatch(workflowResult);
        updateSubRouteButtonVisibility();
    } else if (Object.keys(allTourCustomers).length > 0) {
        // Nur wenn workflowResult leer ist, verwende allTourCustomers
        renderToursFromCustomers();
        updateSubRouteButtonVisibility();
    }
    
    // ... restlicher Code ...
}
```

**Vorteile:**
- ✅ Einfache Änderung
- ✅ Priorisiert Sub-Routen korrekt

**Risiko:** Niedrig

---

### Lösung 3: `renderToursFromMatch()` löscht ALLE alten Einträge

**Datei:** `frontend/index.html`, Funktion `renderToursFromMatch()`

**Änderung:** Lösche ALLE Einträge in `allTourCustomers`, nicht nur die mit 'workflow-' Prefix.

```javascript
function renderToursFromMatch(matchData) {
    console.log('renderToursFromMatch aufgerufen, matchData:', matchData);
    
    // WICHTIG: Lösche ALLE alten Einträge, nicht nur 'workflow-'!
    // Grund: Sub-Routen können andere Keys haben
    const toursToRender = matchData.tours || [];
    const baseTourIds = new Set();
    toursToRender.forEach(tour => {
        const baseId = tour._base_tour_id || tour.tour_id.split(' ')[0];
        baseTourIds.add(baseId);
    });
    
    // Lösche alle Einträge, die zu diesen Touren gehören
    Object.keys(allTourCustomers).forEach(key => {
        const tour = allTourCustomers[key];
        const tourBaseId = tour._base_tour_id || (tour.name || '').split(' ')[0];
        if (baseTourIds.has(tourBaseId)) {
            delete allTourCustomers[key];
        }
    });
    
    // ... restlicher Code ...
}
```

**Vorteile:**
- ✅ Löscht alle relevanten alten Einträge
- ✅ Funktioniert mit verschiedenen Key-Formaten

**Risiko:** Niedrig

---

## 🧪 Test-Plan

### Test 1: Sub-Routen bleiben nach Reload erhalten

**Setup:**
1. CSV mit W-Tour hochladen (z.B. W-07.00 mit 30 Kunden)
2. "Routen optimieren (W-Touren & >4 Kunden)" klicken
3. Warten bis Sub-Routen generiert sind
4. Browser-Konsole öffnen und prüfen:
   ```javascript
   console.log('workflowResult:', JSON.parse(localStorage.getItem('workflowResult')));
   console.log('allTourCustomers:', JSON.parse(localStorage.getItem('allTourCustomers')));
   ```

**Erwartung:**
- ✅ `workflowResult.tours` enthält Sub-Routen (W-07.00 A, W-07.00 B, ...)
- ✅ `allTourCustomers` enthält ebenfalls Sub-Routen
- ✅ Beide Strukturen sind synchron

**Nach Reload:**
- ✅ Sub-Routen sind noch sichtbar
- ✅ Keine Haupttouren mehr vorhanden

---

### Test 2: Sub-Routen bleiben nach Tab-Wechsel erhalten

**Setup:**
1. Sub-Routen generieren (wie Test 1)
2. Zu anderem Tab wechseln
3. Zurück zum Tab wechseln

**Erwartung:**
- ✅ Sub-Routen sind noch sichtbar
- ✅ Keine Haupttouren mehr vorhanden

---

### Test 3: Mehrere Touren mit Sub-Routen

**Setup:**
1. CSV mit mehreren W-Touren hochladen (W-07.00, W-08.00, W-09.00)
2. "Routen optimieren" klicken
3. Alle Sub-Routen generieren lassen

**Erwartung:**
- ✅ Alle Sub-Routen sind sichtbar
- ✅ Keine Haupttouren mehr vorhanden
- ✅ Nach Reload: Alle Sub-Routen noch vorhanden

---

## 📝 Implementierungs-Plan

### Phase 1: Sofort-Fix (Lösung 1 + 2)

**Priorität:** 🔴 HOCH

1. **Implementiere Lösung 1:** `updateToursWithSubRoutes()` aktualisiert auch `allTourCustomers`
2. **Implementiere Lösung 2:** `restoreToursFromStorage()` priorisiert `workflowResult`

**Zeitaufwand:** ~30 Minuten

**Dateien:**
- `frontend/index.html` (Zeile 5218-5310, Zeile 434-484)

---

### Phase 2: Robustheit (Lösung 3)

**Priorität:** 🟡 MITTEL

1. **Implementiere Lösung 3:** `renderToursFromMatch()` löscht alle relevanten Einträge

**Zeitaufwand:** ~15 Minuten

**Dateien:**
- `frontend/index.html` (Zeile 2104-2113)

---

### Phase 3: Tests

**Priorität:** 🟡 MITTEL

1. **Manuelle Tests durchführen** (Test 1-3)
2. **Browser-Konsole prüfen** (localStorage-Inhalte)
3. **Edge-Cases testen** (leere Touren, fehlende Koordinaten, etc.)

**Zeitaufwand:** ~30 Minuten

---

## 🔗 Verwandte Dokumente

- `Regeln/LESSONS_LOG.md` - Eintrag #3 (Sub-Routen-Generator)
- `Regeln/AUDIT_FLOW_ROUTING.md` - Audit-Flow für Routing
- `docs/SUB_ROUTES_GENERATOR_LOGIC.md` - Logik-Dokumentation

---

## ✅ Checkliste

**Vor Implementierung:**
- [ ] Git-Commit mit aktuellen Änderungen
- [ ] Backup von `frontend/index.html`
- [ ] Browser-Konsole öffnen für Debugging

**Während Implementierung:**
- [ ] Lösung 1 implementieren
- [ ] Lösung 2 implementieren
- [ ] Lösung 3 implementieren (optional)
- [ ] Code-Kommentare hinzufügen

**Nach Implementierung:**
- [ ] Test 1 durchführen (Sub-Routen bleiben nach Reload)
- [ ] Test 2 durchführen (Tab-Wechsel)
- [ ] Test 3 durchführen (mehrere Touren)
- [ ] Browser-Konsole prüfen (localStorage)
- [ ] LESSONS_LOG aktualisieren (falls neues Pattern)

---

**Ende des Audit-Reports**  
**Nächste Schritte:** Implementierung von Lösung 1 + 2

