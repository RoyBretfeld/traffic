# 🔴 Problem: App lässt sich nicht bedienen

**Datum:** 2025-11-16  
**Zeit:** ~16:40 Uhr  
**Status:** 🔴 **PROBLEM**  
**Schweregrad:** 🔴 KRITISCH

---

## 🐛 Symptom

**Problem:** App lässt sich nicht bedienen  
**Server:** ✅ Läuft (Port 8111 erreichbar)  
**Health-Check:** ✅ Funktioniert  
**Frontend:** ❓ Unklar

---

## 🔍 Mögliche Ursachen

### 1. JavaScript-Fehler
- Syntax-Fehler in `frontend/index.html`
- Fehler in `generateTourKey()` (letzte Änderung)
- Fehler in `selectTour()` (letzte Änderung)

### 2. Frontend lädt nicht
- HTML wird nicht ausgeliefert
- JavaScript-Dateien fehlen
- CSS-Dateien fehlen

### 3. API-Endpoints nicht erreichbar
- CORS-Probleme
- API-Endpoints antworten nicht
- Backend-Fehler

### 4. Browser-Console-Fehler
- JavaScript-Runtime-Fehler
- Network-Fehler
- CORS-Fehler

---

## 🔧 Diagnose-Schritte

### Schritt 1: Browser-Console prüfen
1. Öffne Browser-Entwicklertools (F12)
2. Prüfe Console-Tab auf Fehler
3. Prüfe Network-Tab auf fehlgeschlagene Requests

### Schritt 2: Server-Logs prüfen
```bash
# Prüfe Server-Logs auf Fehler
Get-ChildItem logs/*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50
```

### Schritt 3: API-Endpoints testen
```bash
# Teste Health-Endpoint
curl http://127.0.0.1:8111/health

# Teste Tourplaene-List
curl http://127.0.0.1:8111/api/tourplaene/list
```

### Schritt 4: Frontend-HTML prüfen
```bash
# Prüfe ob HTML korrekt ausgeliefert wird
curl http://127.0.0.1:8111/ | Select-String -Pattern "script|error" -Context 2
```

---

## 🔍 Letzte Änderungen (mögliche Ursache)

### 1. `generateTourKey()` angepasst (Zeile 2280-2299)
**Änderung:** Behält Punkt (.) für Zeit-Format

**Mögliches Problem:**
- Syntax-Fehler?
- `normalizedBaseId` Variable?

**Prüfung:**
```javascript
// Zeile 2286: Sollte funktionieren
let normalizedBaseId = baseId.replace(/[^a-zA-Z0-9.\-]/g, '_');
```

### 2. `selectTour()` Fallback verbessert (Zeile 3465-3525)
**Änderung:** Behält Punkt bei Normalisierung

**Mögliches Problem:**
- Syntax-Fehler?
- Variable-Scope?

**Prüfung:**
```javascript
// Zeile 3467-3468: Sollte funktionieren
let normalizedKey = key.replace(/[^a-zA-Z0-9.\-]/g, '_');
normalizedKey = normalizedKey.replace(/_+/g, '_').replace(/^_+|_+$/g, '');
```

---

## 🔧 Sofort-Maßnahmen

### 1. Browser-Console prüfen
**Wichtig:** Öffne Browser-Entwicklertools (F12) und prüfe Console auf Fehler!

### 2. Server-Logs prüfen
```bash
Get-ChildItem logs/*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50
```

### 3. Frontend-HTML validieren
```bash
# Prüfe ob HTML korrekt ist
curl http://127.0.0.1:8111/ > test.html
# Öffne test.html im Browser und prüfe Console
```

### 4. JavaScript-Syntax prüfen
```bash
# Prüfe JavaScript-Syntax (falls Node.js verfügbar)
node -c frontend/index.html 2>&1
```

---

## 📋 Checkliste

- [ ] Browser-Console geöffnet?
- [ ] JavaScript-Fehler in Console?
- [ ] Network-Fehler in Console?
- [ ] Server-Logs geprüft?
- [ ] API-Endpoints getestet?
- [ ] Frontend-HTML korrekt?
- [ ] Letzte Änderungen rückgängig gemacht?

---

## 🔧 Notfall-Fix

### Falls JavaScript-Fehler in `generateTourKey()`:

**Rückgängig machen:**
```javascript
// Zurück zu alter Version (ersetzt Punkt durch Unterstrich)
function generateTourKey(tour) {
    const baseId = extractBaseTourId(tour);
    const subRoute = tour._sub_route || '';
    const normalizedBaseId = baseId.replace(/[^a-zA-Z0-9-]/g, '_');
    return subRoute 
        ? `workflow-${normalizedBaseId}-${subRoute}`
        : `workflow-${normalizedBaseId}`;
}
```

### Falls JavaScript-Fehler in `selectTour()`:

**Rückgängig machen:**
```javascript
// Zurück zu alter Version
const normalizedKey = key.replace(/[^a-zA-Z0-9-]/g, '_');
const similarKey = Object.keys(allTourCustomers).find(k => {
    const normalizedK = k.replace(/[^a-zA-Z0-9-]/g, '_');
    return normalizedK === normalizedKey || 
           normalizedK.includes(normalizedKey) || 
           normalizedKey.includes(normalizedK);
});
```

---

## 📊 Status

**Server:** ✅ Läuft  
**Port:** ✅ Erreichbar  
**Health-Check:** ✅ Funktioniert  
**Frontend:** ❓ Unklar (muss geprüft werden)

---

**Erstellt:** 2025-11-16  
**Status:** 🔴 **PROBLEM**  
**Nächster Schritt:** Browser-Console prüfen!

