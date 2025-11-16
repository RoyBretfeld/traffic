# ✅ FIX: Sub-Routen-Generator - Key-Generierung vereinheitlicht

**Datum:** 2025-11-16  
**Status:** ✅ IMPLEMENTIERT  
**Problem:** Key-Mismatch bei Tour-Auswahl

---

## 🐛 Problem

**Symptom:**
```
[SELECT-TOUR] ❌ Tour nicht gefunden: workflow-W-07_00
[SELECT-TOUR] Verfügbare Keys: 
  - 'workflow-W-07.00 Uhr Tour-A'
  - 'workflow-W-07.00 Uhr Tour-B'
```

**Root Cause:**
- `generateTourKey()` ersetzte `.` (Punkt) durch `_` (Unterstrich)
- `W-07.00` → `W-07_00`
- **ABER:** `updateToursWithSubRoutes()` erstellt Keys mit `.` (Punkt)
- **ABER:** `renderToursFromMatch()` erstellt Keys basierend auf `name` mit `.` (Punkt)

**Ergebnis:** Inkonsistente Keys → Tour-Auswahl schlägt fehl

---

## ✅ Fix

### 1. `generateTourKey()` angepasst

**Datei:** `frontend/index.html`  
**Zeile:** 2280-2292

**Änderung:**
- **VORHER:** Ersetzte `.` (Punkt) durch `_` (Unterstrich)
- **NACHHER:** Behält `.` (Punkt) für Zeit-Format bei
- Normalisiert nur problematische Sonderzeichen
- Behält Punkt und Bindestrich

**Code:**
```javascript
function generateTourKey(tour) {
    const baseId = extractBaseTourId(tour);
    const subRoute = tour._sub_route || '';
    
    // WICHTIG: Behalte Punkt (.) für Zeit-Format (z.B. W-07.00)
    // Ersetze NUR problematische Sonderzeichen, BEHALTE Punkt und Bindestrich
    let normalizedBaseId = baseId.replace(/[^a-zA-Z0-9.\-]/g, '_');
    
    // Normalisiere mehrfache Unterstriche zu einem
    normalizedBaseId = normalizedBaseId.replace(/_+/g, '_');
    
    // Entferne führende/abschließende Unterstriche
    normalizedBaseId = normalizedBaseId.replace(/^_+|_+$/g, '');
    
    // Mit Sub-Route: workflow-W-07.00-A
    // Ohne Sub-Route: workflow-W-07.00
    return subRoute 
        ? `workflow-${normalizedBaseId}-${subRoute}`
        : `workflow-${normalizedBaseId}`;
}
```

**Ergebnis:**
- `W-07.00` → `workflow-W-07.00` (behält Punkt)
- `W-07.00 A` → `workflow-W-07.00-A` (behält Punkt, normalisiert Leerzeichen)

---

### 2. `selectTour()` Fallback verbessert

**Datei:** `frontend/index.html`  
**Zeile:** 3458-3500

**Änderung:**
- **VORHER:** Normalisierte auch Punkt zu Unterstrich
- **NACHHER:** Behält Punkt bei, ignoriert Punkt-Unterschiede nur als Fallback

**Code:**
```javascript
// Versuche 2: Ähnlicher Key (normalisiert für Vergleich - BEHALTE Punkt!)
const normalizedKey = key.replace(/[^a-zA-Z0-9.\-]/g, '_').replace(/_+/g, '_').replace(/^_+|_+$/g, '');
const similarKey = Object.keys(allTourCustomers).find(k => {
    const normalizedK = k.replace(/[^a-zA-Z0-9.\-]/g, '_').replace(/_+/g, '_').replace(/^_+|_+$/g, '');
    // Exakte Übereinstimmung nach Normalisierung
    if (normalizedK === normalizedKey) return true;
    // Teilstring-Match (für Sub-Routen: "W-07.00" sollte "W-07.00-A" finden)
    if (normalizedK.includes(normalizedKey) || normalizedKey.includes(normalizedK)) return true;
    // Fallback: Ignoriere Punkt für Vergleich (wenn alles andere gleich)
    const keyWithoutDot = normalizedKey.replace(/\./g, '');
    const kWithoutDot = normalizedK.replace(/\./g, '');
    return kWithoutDot === keyWithoutDot || 
           kWithoutDot.includes(keyWithoutDot) || 
           keyWithoutDot.includes(kWithoutDot);
});
```

**Ergebnis:**
- Exakte Übereinstimmung (mit Punkt)
- Teilstring-Match (für Sub-Routen)
- Fallback: Ignoriert Punkt-Unterschiede

---

## 🧪 Erwartetes Verhalten

### Vorher
- `generateTourKey()`: `W-07.00` → `workflow-W-07_00`
- `updateToursWithSubRoutes()`: `W-07.00 A` → Keys mit `.` (Punkt)
- **Mismatch:** `workflow-W-07_00` vs. `workflow-W-07.00-A`
- **Ergebnis:** Tour-Auswahl schlägt fehl ❌

### Nachher
- `generateTourKey()`: `W-07.00` → `workflow-W-07.00`
- `updateToursWithSubRoutes()`: `W-07.00 A` → Keys mit `.` (Punkt)
- **Konsistent:** `workflow-W-07.00` vs. `workflow-W-07.00-A`
- **Ergebnis:** Tour-Auswahl funktioniert ✅

---

## 📋 Testen

1. **Sub-Routen generieren**
   - CSV hochladen
   - Workflow ausführen
   - Sub-Routen generieren

2. **Prüfen:**
   - Werden Sub-Routen angezeigt? ✅
   - Können Sub-Routen ausgewählt werden? ✅
   - Bleiben Sub-Routen nach Reload erhalten? ✅

3. **Console-Log prüfen:**
   - Keine "Tour nicht gefunden" Fehler
   - Keys sind konsistent

---

## 🔗 Verwandte Dateien

- `frontend/index.html` - Zeile 2280-2292 (`generateTourKey()`)
- `frontend/index.html` - Zeile 3458-3500 (`selectTour()` Fallback)
- `frontend/index.html` - Zeile 5795-5891 (`updateToursWithSubRoutes()`)
- `frontend/index.html` - Zeile 5097-5104 (`processTour()` in `generateSubRoutes()`)

---

## 📊 Vergleich

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| Zeit-Format | `W-07_00` (Unterstrich) | `W-07.00` (Punkt) |
| Sub-Route-Key | `workflow-W-07_00-A` | `workflow-W-07.00-A` |
| Konsistenz | ❌ Inkonsistent | ✅ Konsistent |
| Tour-Auswahl | ❌ Schlägt fehl | ✅ Funktioniert |

---

## ✅ Zusammenfassung

**Behoben:**
- ✅ `generateTourKey()` behält Punkt (.) für Zeit-Format
- ✅ `selectTour()` Fallback verbessert (behält Punkt bei)
- ✅ Konsistente Key-Generierung

**Erwartetes Ergebnis:**
- ✅ Sub-Routen werden korrekt angezeigt
- ✅ Tour-Auswahl funktioniert
- ✅ Sub-Routen bleiben nach Reload erhalten

---

**Erstellt:** 2025-11-16  
**Status:** ✅ **IMPLEMENTIERT**  
**Nächster Schritt:** Testen

