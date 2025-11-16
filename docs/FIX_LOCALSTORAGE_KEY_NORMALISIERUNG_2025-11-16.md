# 🔧 Fix: localStorage Key-Normalisierung

**Datum:** 2025-11-16  
**Status:** ✅ IMPLEMENTIERT  
**Problem:** Keys werden inkonsistent gespeichert und geladen

---

## 🎯 Problem-Identifikation

### Root Cause: Inkonsistente Key-Generierung beim Speichern

**Problem 1: Manuelle Key-Generierung in `processTour()` (Zeile 5020)**

```javascript
// VORHER (FALSCH):
const subRouteKey = `workflow-${tour.tour_id}-${subRouteLetter}`;
// tour.tour_id = "W-07.00 Uhr Tour"
// Ergebnis: "workflow-W-07.00 Uhr Tour-A" (mit Punkt und "Uhr Tour")
```

**Problem 2: Beim Laden aus localStorage**

- Alte Keys werden geladen: `workflow-W-07.00 Uhr Tour-A`
- `selectTour()` sucht nach normalisierten Keys: `workflow-W_07_00-A`
- **Mismatch → Tour nicht gefunden!**

**Problem 3: `activeTourKey` wird mit altem Format gespeichert**

- `localStorage.setItem('activeTourKey', 'workflow-W-07_00')`
- Beim Laden: Key existiert nicht in `allTourCustomers` (Keys sind `workflow-W-07.00 Uhr Tour-A`)

---

## 🔧 Lösung

### Fix 1: Vereinheitliche Key-Generierung beim Speichern

**Zeile 5020: `generateTourKey()` verwenden**

```javascript
// NACHHER (RICHTIG):
const tourMeta = {
    tour_id: tour.tour_id,
    _base_tour_id: tour._base_tour_id || extractBaseTourId(tour),
    _sub_route: subRouteLetter
};
const subRouteKey = generateTourKey(tourMeta);
// Ergebnis: "workflow-W_07_00-A" (normalisiert)
```

### Fix 2: Key-Normalisierung beim Laden

**`restoreToursFromStorage()`: Keys beim Laden normalisieren**

```javascript
// Beim Laden aus localStorage:
1. Prüfe ob Key bereits normalisiert ist
2. Wenn nicht: Konvertiere mit generateTourKey()
3. Speichere normalisierte Keys zurück
4. Normalisiere auch activeTourKey
```

**Vorteile:**
- ✅ Alte Daten werden automatisch migriert
- ✅ Konsistente Keys nach Reload
- ✅ Keine Datenverluste

### Fix 3: `activeTourKey` normalisieren

**Beim Laden: `activeTourKey` auch normalisieren**

```javascript
// Prüfe ob activeTourKey normalisiert ist
// Wenn nicht: Suche ähnlichen Key in allTourCustomers
// Speichere normalisierten Key zurück
```

---

## 📊 Vergleich: Vorher vs. Nachher

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| **Key-Format beim Speichern** | `workflow-W-07.00 Uhr Tour-A` | `workflow-W_07_00-A` |
| **Key-Format beim Laden** | `workflow-W-07.00 Uhr Tour-A` | `workflow-W_07_00-A` (normalisiert) |
| **Konsistenz** | ❌ Inkonsistent | ✅ Konsistent |
| **Migration alter Daten** | ❌ Nicht möglich | ✅ Automatisch |
| **`activeTourKey` Match** | ❌ Fehlschlag | ✅ Erfolgreich |

---

## 🧪 Test-Plan

1. **Alte Daten laden**
   - localStorage mit alten Keys: `workflow-W-07.00 Uhr Tour-A`
   - Seite neu laden
   - **Erwartung:** Keys werden automatisch normalisiert

2. **Sub-Routen generieren**
   - CSV hochladen, Sub-Routen generieren
   - **Erwartung:** Keys haben Format `workflow-W_XX_XX-A`

3. **Speichern und Laden**
   - Sub-Routen generieren
   - Seite neu laden
   - **Erwartung:** Keys bleiben konsistent, `activeTourKey` wird gefunden

4. **Console prüfen**
   - `Object.keys(allTourCustomers)` nach Reload
   - **Erwartung:** Alle Keys normalisiert

---

## 📝 Implementierung

**Dateien:**
- `frontend/index.html` - Zeile 5020 (Key-Generierung in `processTour()`)
- `frontend/index.html` - Zeile 482-485 (`restoreToursFromStorage()` - Key-Normalisierung)
- `frontend/index.html` - Zeile 550-554 (`activeTourKey` Normalisierung)

**Änderungen:**
1. ✅ Zeile 5020: `generateTourKey()` verwenden statt manueller String-Konkatenation
2. ✅ Zeile 482-485: Keys beim Laden normalisieren und zurück speichern
3. ✅ Zeile 550-554: `activeTourKey` normalisieren und zurück speichern

---

**Erstellt:** 2025-11-16  
**Status:** ✅ IMPLEMENTIERT

