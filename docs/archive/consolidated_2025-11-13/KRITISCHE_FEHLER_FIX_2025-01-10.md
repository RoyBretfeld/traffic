# Kritische Fehler - Fix-Plan
**Datum:** 2025-01-10  
**Status:** 🔴 KRITISCH - System instabil

---

## 🔴 Identifizierte Probleme

### 1. KI-Checker läuft nicht
**Symptom:**
- Background-Job ist aktiviert (`enabled: True`)
- Aber läuft nicht (`is_running: False`)
- Keine Verbesserungen (`last_run: None`)

**Ursache:**
- Job muss manuell gestartet werden
- Kein Auto-Start beim Server-Start

**Fix:**
- Background-Job beim Server-Start automatisch starten
- Oder manuell über API starten: `POST /api/code-improvement-job/start`

---

### 2. Sub-Routen-Generierung zu langsam
**Symptom:**
- Generierung dauert sehr lange
- Verarbeitet Touren sequenziell (eine nach der anderen)
- Keine Parallelisierung

**Ursache:**
- `generateSubRoutes()` verarbeitet Touren in einer `for`-Schleife
- Jede Tour wartet auf die vorherige

**Fix:**
- Parallelisierung mit `Promise.all()` oder `Promise.allSettled()`
- Batch-Verarbeitung (z.B. 3 Touren gleichzeitig)

---

### 3. Tour-Switching funktioniert nicht
**Symptom:**
- Man kann nicht mehr zwischen Unterrouten switchen
- `selectTour(key)` findet Sub-Routen nicht

**Ursache:**
- Sub-Routen werden möglicherweise nicht korrekt in `allTourCustomers` gespeichert
- Keys stimmen nicht überein

**Fix:**
- Prüfe wie Sub-Routen in `allTourCustomers` gespeichert werden
- Stelle sicher, dass Keys konsistent sind

---

### 4. Unterrouten werden rechts nicht angezeigt
**Symptom:**
- Sub-Routen werden nicht in der Tour-Details-Ansicht angezeigt
- `renderTourDetails()` zeigt nichts an

**Ursache:**
- Möglicherweise falsche Datenstruktur
- `tourData.customers` ist leer oder undefined

**Fix:**
- Prüfe Datenstruktur von Sub-Routen
- Stelle sicher, dass `customers` Array vorhanden ist

---

### 5. Upload/Verarbeitung geht nicht
**Symptom:**
- Upload funktioniert vielleicht
- Aber Verarbeitung schlägt fehl

**Ursache:**
- Möglicherweise Fehler in der Workflow-Pipeline
- Oder Match-Endpoint gibt Fehler zurück

**Fix:**
- Prüfe Upload → Match → Workflow Pipeline
- Prüfe Server-Logs für Fehler

---

## 🔧 Implementierte Fixes

### Fix 1: Background-Job Auto-Start
```python
# backend/app.py - In create_app()
@app.on_event("startup")
async def startup_event():
    """Startet Background-Job beim Server-Start."""
    from backend.services.code_improvement_job import get_background_job
    job = get_background_job()
    if job.enabled and not job.is_running:
        asyncio.create_task(job.run_continuously())
        print("[STARTUP] KI-CodeChecker Background-Job gestartet")
```

### Fix 2: Sub-Routen Parallelisierung
```javascript
// frontend/index.html - generateSubRoutes()
// Statt sequenziell:
for (let tourIndex = 0; tourIndex < toursToOptimize.length; tourIndex++) {
    // ...
}

// Parallel (Batch von 3):
const BATCH_SIZE = 3;
for (let batchStart = 0; batchStart < toursToOptimize.length; batchStart += BATCH_SIZE) {
    const batch = toursToOptimize.slice(batchStart, batchStart + BATCH_SIZE);
    await Promise.allSettled(batch.map(tour => processTour(tour)));
}
```

### Fix 3: Tour-Switching Debugging
```javascript
// frontend/index.html - selectTour()
function selectTour(key) {
    console.log('[SELECT-TOUR] Key:', key);
    console.log('[SELECT-TOUR] allTourCustomers keys:', Object.keys(allTourCustomers));
    console.log('[SELECT-TOUR] Tour data:', allTourCustomers[key]);
    
    if (!key || !allTourCustomers[key]) {
        console.error('[SELECT-TOUR] Tour nicht gefunden:', key);
        return;
    }
    // ...
}
```

### Fix 4: Tour-Details-Rendering
```javascript
// frontend/index.html - renderTourDetails()
function renderTourDetails(tourData) {
    console.log('[RENDER-DETAILS] Tour data:', tourData);
    console.log('[RENDER-DETAILS] Customers:', tourData.customers);
    
    if (!tourData || !tourData.customers || tourData.customers.length === 0) {
        console.error('[RENDER-DETAILS] Keine Kunden-Daten');
        // Fallback: Versuche stops zu verwenden
        if (tourData.stops) {
            tourData.customers = tourData.stops.map(s => ({
                name: s.name || s.customer,
                // ...
            }));
        }
    }
    // ...
}
```

---

## 📋 Nächste Schritte

1. **Background-Job starten**
   - Automatisch beim Server-Start
   - Oder manuell: `POST /api/code-improvement-job/start`

2. **Sub-Routen-Generierung optimieren**
   - Parallelisierung implementieren
   - Batch-Verarbeitung

3. **Tour-Switching reparieren**
   - Debugging-Logs hinzufügen
   - Keys konsistent machen

4. **Tour-Details-Anzeige reparieren**
   - Datenstruktur prüfen
   - Fallback für fehlende Daten

5. **Upload/Verarbeitung prüfen**
   - Server-Logs analysieren
   - Pipeline testen

---

## 🎯 Priorität

1. **KRITISCH:** Background-Job starten (KI-Checker)
2. **HOCH:** Sub-Routen-Generierung optimieren (Performance)
3. **HOCH:** Tour-Switching reparieren (Funktionalität)
4. **HOCH:** Tour-Details-Anzeige reparieren (Funktionalität)
5. **MITTEL:** Upload/Verarbeitung prüfen (Stabilität)

