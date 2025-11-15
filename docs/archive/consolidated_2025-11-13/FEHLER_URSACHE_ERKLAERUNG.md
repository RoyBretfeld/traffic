# Wie kommen diese Fehler zustande?
**Datum:** 2025-01-10

---

## 🔴 Die 3 Fehler im Detail

### 1. SyntaxError: Identifier 'key' has already been declared

**Was passiert:**
```javascript
// Zeile 405: key wird als Parameter deklariert
tourEntries.map(([key, tour], index) => {
    // Zeile 406: key wird NOCHMAL deklariert → FEHLER!
    const key = `restored-${index}`;
```

**Warum:** JavaScript erlaubt keine doppelte Deklaration im selben Scope.

**Fix:** Parameter umbenennen → `originalKey` statt `key`

---

### 2. ReferenceError: handleFileChange is not defined

**Was passiert:**

1. **Browser lädt HTML** (Zeile 123):
   ```html
   <input onchange="handleFileChange()">
   ```
   → Browser registriert: "Wenn jemand eine Datei auswählt, rufe `handleFileChange()` auf"

2. **Browser lädt JavaScript** (Zeile 719+):
   ```javascript
   window.handleFileChange = function() { ... }
   ```
   → Funktion wird definiert

3. **Benutzer wählt Datei aus:**
   → Browser sucht `handleFileChange()` im globalen Scope
   → **Problem:** Wenn das Script noch nicht vollständig geladen ist, existiert die Funktion noch nicht!

**Warum:** HTML wird **sofort** geparst, JavaScript wird **später** ausgeführt. Wenn der Benutzer zu schnell klickt, ist die Funktion noch nicht da.

**Fix:** Funktion **am Anfang** des Scripts definieren (vor allen anderen Code)

---

### 3. ReferenceError: runWorkflow is not defined

**Gleiches Problem wie bei `handleFileChange`:**
- HTML wird zuerst geparst → `onclick="runWorkflow()"` wird registriert
- JavaScript wird später ausgeführt → Funktion wird später definiert
- Benutzer klickt → Funktion existiert noch nicht

**Fix:** Funktion **am Anfang** des Scripts definieren

---

## 📋 Zusammenfassung

**Hauptproblem:** **Reihenfolge der Code-Ausführung**

```
1. Browser parst HTML
   ↓
2. onclick/onchange Handler werden registriert
   ↓
3. Browser führt JavaScript aus
   ↓
4. Funktionen werden definiert
   ↓
5. Benutzer klickt → Browser sucht Funktion
   ❌ Problem: Wenn Schritt 3-4 noch nicht fertig sind, existiert die Funktion nicht!
```

**Lösung:** Funktionen **sofort** am Anfang des Scripts definieren, damit sie beim Klick verfügbar sind.

---

## ✅ Was wurde behoben?

1. ✅ Syntax-Fehler (doppelte `key`-Deklaration)
2. ✅ `handleFileChange` wird jetzt am Anfang definiert
3. ✅ `runWorkflow` wird jetzt am Anfang definiert (mit Weiterleitung zu vollständiger Funktion)

---

**Erstellt von:** KI-Assistent (Auto)  
**Datum:** 2025-01-10

