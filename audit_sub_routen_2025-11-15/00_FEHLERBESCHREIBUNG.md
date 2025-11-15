# 🔴 DETAILLIERTE FEHLERBESCHREIBUNG: Sub-Routen verschwinden nach Generierung

**Datum:** 2025-11-15  
**Status:** ❌ NICHT GELÖST  
**Schweregrad:** 🔴 KRITISCH  
**Wiederholungen:** 8+ mal über 3 Tage

---

## 📋 EXAKTE PROBLEM-BESCHREIBUNG

### Symptom (User-Report)

**User-Zitat:**
> "Es ist jedes Mal dasselbe. Die Touren werden gerendert. Und zum Schluss, wenn der fertig ist, ist mit der W16-Tour fertig. Bumm, stehen wieder die Haupttouren da und alles andere ist weg."

**Konkrete Schritte:**
1. User lädt CSV-Datei mit W-Touren hoch (z.B. W-07.00, W-08.00, W-16.00)
2. User klickt auf "Routen optimieren (W-Touren & >4 Kunden)"
3. System generiert Sub-Routen (z.B. W-07.00 A, W-07.00 B, W-08.00 A, W-16.00 A, W-16.00 B)
4. **Während der Generierung:** Sub-Routen werden korrekt angezeigt ✅
5. **Nach Abschluss der letzten Tour (z.B. W-16.00):** ALLE Sub-Routen verschwinden ❌
6. **Ergebnis:** Nur noch Haupttouren sichtbar (W-07.00, W-08.00, W-16.00) ❌

### Technische Details

**Betroffene Komponenten:**
- Frontend: `frontend/index.html`
- Backend: `backend/routes/workflow_api.py`
- State-Management: `localStorage` (workflowResult, allTourCustomers)

**Betroffene Funktionen:**
1. `generateSubRoutes()` - Startet Sub-Routen-Generierung
2. `processTour()` - Verarbeitet einzelne Tour
3. `updateToursWithSubRoutes()` - Aktualisiert Tour-Liste mit Sub-Routen
4. `renderToursFromMatch()` - Rendert Touren aus workflowResult
5. `restoreToursFromStorage()` - Lädt Touren beim Seiten-Reload
6. `renderToursFromCustomers()` - Rendert Touren aus allTourCustomers

---

## 🔬 ROOT CAUSE ANALYSIS

### Problem 1: Zwei parallele Datenstrukturen

**Struktur A: `workflowResult`**
```javascript
workflowResult = {
    tours: [
        { tour_id: "W-07.00 A", stops: [...], customers: [...] },
        { tour_id: "W-07.00 B", stops: [...], customers: [...] }
    ]
}
```
- ✅ Wird korrekt mit Sub-Routen aktualisiert
- ✅ Wird in localStorage gespeichert

**Struktur B: `allTourCustomers`**
```javascript
allTourCustomers = {
    "workflow-0": { name: "W-07.00", customers: [...] },  // ❌ Alte Haupttour!
    "workflow-1": { name: "W-08.00", customers: [...] }   // ❌ Alte Haupttour!
}
```
- ❌ Wird NICHT mit Sub-Routen aktualisiert
- ❌ Enthält noch alte Haupttouren
- ✅ Wird in localStorage gespeichert

**Problem:** Beide Strukturen werden parallel verwendet, aber nicht synchron gehalten!

### Problem 2: Rendering-Pfad-Konflikt

**Pfad A: `processTour()` → `renderToursFromCustomers()`**
- Wird nach jeder Tour aufgerufen (ENTFERNT in Zeile 4750)
- Rendert aus `allTourCustomers` (enthält alte Haupttouren)
- **Ergebnis:** Überschreibt Sub-Routen mit alten Haupttouren ❌

**Pfad B: `updateToursWithSubRoutes()` → `renderToursFromMatch()`**
- Wird am Ende der Generierung aufgerufen
- Rendert aus `workflowResult` (enthält Sub-Routen)
- **Ergebnis:** Zeigt Sub-Routen korrekt ✅

**Konflikt:** Beide Pfade überschreiben sich gegenseitig!

### Problem 3: State-Wiederherstellung beim Reload

**Ablauf beim Seiten-Reload:**
1. `restoreToursFromStorage()` wird aufgerufen
2. `workflowResult` wird aus localStorage geladen (enthält Sub-Routen) ✅
3. `allTourCustomers` wird aus localStorage geladen (enthält alte Haupttouren) ❌
4. **Problem:** `restoreToursFromStorage()` priorisiert `allTourCustomers` über `workflowResult`!
5. **Ergebnis:** `renderToursFromCustomers()` wird aufgerufen → alte Haupttouren werden gerendert ❌

**Code-Stelle:** `frontend/index.html`, Zeile 506-512
```javascript
} else if (Object.keys(allTourCustomers).length > 0) {
    // Nur wenn workflowResult leer ist, verwende allTourCustomers
    console.log('[RESTORE] workflowResult leer, verwende allTourCustomers');
    renderToursFromCustomers();  // ❌ Rendert alte Haupttouren!
    updateSubRouteButtonVisibility();
}
```

**ABER:** Die Priorisierung wurde bereits geändert (Zeile 455-503), aber das Problem besteht weiterhin!

### Problem 4: `renderToursFromMatch()` löscht nicht alle alten Einträge

**Code-Stelle:** `frontend/index.html`, Zeile 2249-2288

**Aktueller Code:**
```javascript
function renderToursFromMatch(matchData) {
    // Lösche ALLE relevanten Einträge in allTourCustomers
    const toursToRender = matchData.tours || [];
    const baseTourIds = new Set();
    toursToRender.forEach(tour => {
        let baseId = tour._base_tour_id;
        if (!baseId && tour.tour_id) {
            baseId = tour.tour_id.replace(/\s+[A-Z]$/, '').replace(/\s*(Uhr\s*)?(Tour|BAR)$/i, '').trim();
        }
        if (baseId) {
            baseTourIds.add(baseId);
        }
    });
    
    // Lösche alle Einträge, die zu diesen Touren gehören
    Object.keys(allTourCustomers).forEach(key => {
        const tour = allTourCustomers[key];
        let tourBaseId = tour._base_tour_id;
        if (!tourBaseId && tour.name) {
            tourBaseId = tour.name.replace(/\s+[A-Z]$/, '').replace(/\s*(Uhr\s*)?(Tour|BAR)$/i, '').trim();
        }
        if (!tourBaseId) {
            tourBaseId = (tour.name || '').split(' ')[0];
        }
        
        if (tourBaseId && baseTourIds.has(tourBaseId)) {
            delete allTourCustomers[key];
        }
    });
    
    // ... rendert neue Touren ...
}
```

**Problem:** Die Base-ID-Extraktion funktioniert möglicherweise nicht korrekt für alle Tour-Formate!

### Problem 5: Timing-Problem während der Generierung

**Ablauf während der Generierung:**
1. Tour 1 (W-07.00) wird verarbeitet → Sub-Routen in `allTourCustomers` gespeichert ✅
2. Tour 2 (W-08.00) wird verarbeitet → Sub-Routen in `allTourCustomers` gespeichert ✅
3. Tour 3 (W-16.00) wird verarbeitet → Sub-Routen in `allTourCustomers` gespeichert ✅
4. **ABER:** `updateToursWithSubRoutes()` wird aufgerufen → aktualisiert `workflowResult.tours` ✅
5. `renderToursFromMatch()` wird aufgerufen → löscht alte Einträge in `allTourCustomers` ✅
6. **ABER:** Neue Einträge werden in `allTourCustomers` erstellt (Zeile 5536-5553) ✅
7. **PROBLEM:** Vielleicht werden die neuen Einträge nicht korrekt erstellt oder überschrieben?

**Code-Stelle:** `frontend/index.html`, Zeile 5536-5553
```javascript
// Erstelle neue Einträge für Sub-Routen in allTourCustomers
workflowResult.tours.forEach((tour, index) => {
    const key = `workflow-${index}`;
    allTourCustomers[key] = {
        name: tour.tour_id,
        customers: tour.customers || [],
        stops: tour.stops || [],
        // ... Metadaten ...
    };
    console.log(`[UPDATE-TOURS] Erstelle neuen Eintrag: ${key} (Tour: ${tour.tour_id})`);
});
```

**Problem:** Die Keys werden mit `workflow-${index}` erstellt, aber vielleicht werden sie später überschrieben?

---

## 🎯 HYPOTHESEN

### Hypothese 1: `renderToursFromMatch()` überschreibt `allTourCustomers` neu

**Vermutung:** `renderToursFromMatch()` erstellt neue Einträge in `allTourCustomers` (Zeile 2536-2547), aber diese überschreiben die Sub-Routen-Einträge, die in `updateToursWithSubRoutes()` erstellt wurden.

**Code-Stelle:** `frontend/index.html`, Zeile 2536-2547
```javascript
allTourCustomers[key] = {
    name: tourMeta.tour_id || `Tour ${tourMeta.index + 1}`,
    // ... aber tourMeta.tour_id könnte die Haupttour-ID sein, nicht die Sub-Route-ID!
};
```

**Problem:** Wenn `tourMeta.tour_id` die Haupttour-ID ist (z.B. "W-07.00"), wird die Sub-Route-ID (z.B. "W-07.00 A") überschrieben!

### Hypothese 2: Base-ID-Extraktion funktioniert nicht für alle Formate

**Vermutung:** Die Base-ID-Extraktion in `renderToursFromMatch()` und `updateToursWithSubRoutes()` funktioniert nicht korrekt für alle Tour-Formate.

**Beispiele:**
- "W-07.00 Uhr Tour" → Base-ID sollte "W-07.00" sein
- "W-07.00 Uhr Tour A" → Base-ID sollte "W-07.00" sein
- "W-07.00 Uhr BAR" → Base-ID sollte "W-07.00" sein
- "W-07.00 Uhr BAR A" → Base-ID sollte "W-07.00" sein

**Problem:** Wenn die Base-ID-Extraktion fehlschlägt, werden alte Einträge nicht gelöscht!

### Hypothese 3: Race Condition zwischen `updateToursWithSubRoutes()` und `renderToursFromMatch()`

**Vermutung:** `updateToursWithSubRoutes()` erstellt neue Einträge in `allTourCustomers`, aber `renderToursFromMatch()` wird danach aufgerufen und überschreibt diese Einträge mit falschen Daten.

**Ablauf:**
1. `updateToursWithSubRoutes()` erstellt Einträge für Sub-Routen ✅
2. `renderToursFromMatch()` wird aufgerufen
3. `renderToursFromMatch()` löscht alte Einträge ✅
4. `renderToursFromMatch()` erstellt neue Einträge ❌ (aber mit falschen Daten?)

---

## 📊 BEKANNTE FEHLER-PATTERNS

### Pattern 1: Doppelte Variablen-Deklaration
**Datum:** 2025-11-15  
**Fehler:** `baseTourId` wurde doppelt deklariert (Zeile 2441, 2484)  
**Status:** ✅ BEHOBEN

### Pattern 2: renderToursFromCustomers() zu früh
**Datum:** 2025-11-15  
**Fehler:** `renderToursFromCustomers()` wurde nach jeder Tour aufgerufen  
**Status:** ✅ BEHOBEN (entfernt in Zeile 4750)

### Pattern 3: State-Inkonsistenz
**Datum:** 2025-11-15  
**Fehler:** `workflowResult` und `allTourCustomers` nicht synchron  
**Status:** ⏳ IN BEARBEITUNG (mehrfache Fixes, funktioniert aber nicht)

---

## 🔍 DEBUG-LOGGING (aktuell aktiv)

**Code-Stelle:** `frontend/index.html`, Zeile 5557-5591

**Logs:**
- `[UPDATE-TOURS] workflowResult.tours hat Sub-Routen: true/false, Anzahl: X`
- `[UPDATE-TOURS] Nach Rendering: X Sub-Routen in allTourCustomers`
- `[UPDATE-TOURS] ✅ Finale Prüfung: X Sub-Routen noch vorhanden` ODER
- `[UPDATE-TOURS] ❌ KRITISCH: Sub-Routen sind nach 100ms verschwunden!`

**Was die Logs zeigen sollten:**
- Wann verschwinden die Sub-Routen? (BEIM Rendering oder NACH Rendering?)
- Sind Sub-Routen in `workflowResult.tours` vorhanden, aber nicht in `allTourCustomers`?
- Oder verschwinden sie aus beiden Strukturen?

---

## 🎯 NÄCHSTE SCHRITTE

1. **Debug-Logs analysieren:** Browser-Konsole öffnen, Sub-Routen generieren, Logs kopieren
2. **State-Snapshot erstellen:** Vor/Nach `renderToursFromMatch()` prüfen
3. **Root Cause identifizieren:** Basierend auf Logs, nicht raten!
4. **Gezielte Lösung implementieren:** Nicht "ich probiere mal", sondern systematisch!

---

**Ende der Fehlerbeschreibung**  
**Stand:** 2025-11-15 (abends)  
**Status:** Problem besteht weiterhin, Debug-Logging aktiv

