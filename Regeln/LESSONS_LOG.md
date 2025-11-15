# Lessons Learned – FAMO TrafficApp

**Projekt:** FAMO TrafficApp 3.0  
**Zweck:** Dokumentation aller kritischen Fehler und deren Lösungen als Lernbasis für zukünftige Audits

---

## Einleitung

Dieses Dokument sammelt alle echten Störungen und Fehler, die während der Entwicklung aufgetreten sind. Jeder Eintrag folgt einem festen Schema:

- **Symptom:** Was wurde beobachtet?
- **Ursache:** Was war die Root Cause?
- **Fix:** Wie wurde es behoben?
- **Was die KI künftig tun soll:** Welche Lehren ziehen wir daraus?

---

## 2025-11-14 – Panel IPC: Syntax-Fehler + Memory Leak

**Kategorie:** Frontend (JavaScript)  
**Schweregrad:** 🔴 KRITISCH  
**Dateien:** `frontend/js/panel-ipc.js`, `frontend/panel-map.html`, `frontend/panel-tours.html`

### Symptom

- Panel-Kommunikation funktioniert nicht
- JavaScript-Fehler: `SyntaxError: Unexpected token` in `panel-ipc.js`
- Browser-Konsole zeigt: `Uncaught SyntaxError` bei Zeile 7
- Panel-Fenster können nicht mit Hauptfenster kommunizieren

### Ursache

1. **Syntax-Fehler (Zeile 7):**
   ```javascript
   constructor(channelName = trafficapp-panels') {  // ❌ Fehlendes öffnendes '
   ```
   - Tippfehler: `trafficapp-panels'` statt `'trafficapp-panels'`
   - JavaScript-Datei wird nicht ausgeführt

2. **Fehlende Defensive Programmierung:**
   - Keine Validierung von `event.data` in Message-Handler
   - Keine Type-Checks in `on()`, `off()`, `postMessage()`
   - Keine Browser-Kompatibilitätsprüfung für `BroadcastChannel`

3. **Memory Leak:**
   - Event Listener wurde in `close()` nicht entfernt
   - Bei wiederholtem Öffnen/Schließen von Panels: Speicherleck

4. **Fehlende Null-Checks in HTML-Dateien:**
   - `window.panelIPC.postMessage()` ohne Prüfung, ob `panelIPC` existiert
   - TypeError bei Browsern ohne BroadcastChannel-Support

### Fix

**1. Syntax-Fehler korrigiert:**
```javascript
// Vorher
constructor(channelName = trafficapp-panels') {

// Nachher
constructor(channelName = 'trafficapp-panels') {
```

**2. Defensive Message-Validierung:**
```javascript
setupListeners() {
    this.messageHandler = (event) => {
        // Validierung hinzugefügt
        if (!event || !event.data || typeof event.data !== 'object') {
            console.warn('[PanelIPC] Ungültige Nachricht erhalten:', event);
            return;
        }
        
        const { type, data } = event.data;
        
        if (!type || typeof type !== 'string') {
            console.warn('[PanelIPC] Nachricht ohne gültigen Typ erhalten:', event.data);
            return;
        }
        // ...
    };
}
```

**3. Parameter-Validierung in allen Methoden:**
```javascript
on(type, handler) {
    if (typeof type !== 'string' || !type) {
        console.error('[PanelIPC] on(): type muss ein nicht-leerer String sein');
        return;
    }
    if (typeof handler !== 'function') {
        console.error('[PanelIPC] on(): handler muss eine Funktion sein');
        return;
    }
    // ...
}
```

**4. Memory Leak behoben:**
```javascript
close() {
    // Event Listener entfernen
    if (this.messageHandler) {
        this.channel.removeEventListener('message', this.messageHandler);
        this.messageHandler = null;
    }
    this.channel.close();
    this.listeners.clear();
}
```

**5. Browser-Kompatibilität:**
```javascript
// Globale Instanz nur erstellen, wenn BroadcastChannel verfügbar
if (window.BroadcastChannel) {
    try {
        window.panelIPC = new PanelIPC();
    } catch (e) {
        console.error('[PanelIPC] Fehler beim Initialisieren:', e);
        window.panelIPC = null;
    }
} else {
    console.error('[PanelIPC] BroadcastChannel API nicht verfügbar');
    window.panelIPC = null;
}
```

**6. Null-Checks in HTML-Dateien:**
```javascript
// In panel-map.html und panel-tours.html
if (window.panelIPC) {
    window.panelIPC.on('route-update', (data) => { ... });
} else {
    console.error('[PANEL] panelIPC nicht verfügbar');
}
```

### Ergebnis

**Code-Qualität:**

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| Syntax-Fehler | 1 🔴 | 0 ✅ |
| Defensive Checks | 0 🔴 | 8 ✅ |
| Memory Leaks | 1 🔴 | 0 ✅ |
| JSDoc Coverage | 40% 🟡 | 100% ✅ |
| Browser Compat. | ❌ 🔴 | ✅ ✅ |

**Erwartete Userwirkung:**
- ✅ Panel-Kommunikation funktioniert jetzt korrekt
- ✅ Keine TypeErrors mehr bei ungültigen Nachrichten
- ✅ Graceful Degradation in älteren Browsern
- ✅ Keine Memory Leaks beim Schließen von Panels

### Was die KI künftig tun soll

1. **Syntax-Checks sind Pflicht:**
   - Vor jedem Commit: Syntax validieren
   - Niemals Code mit offensichtlichen Tippfehlern ausliefern
   - Linter nutzen (ESLint für JavaScript)

2. **Defensive Programmierung immer:**
   - Alle Inputs validieren (Type-Checks, Null-Checks)
   - Niemals davon ausgehen, dass Daten "schon richtig sein werden"
   - Bei jedem `forEach()`, `.map()` etc.: Array-Check davor

3. **Browser-Kompatibilität prüfen:**
   - Moderne APIs (BroadcastChannel, Fetch, etc.) haben Feature Detection
   - Fallback-Strategien oder klare Fehlermeldungen
   - Graceful Degradation statt komplettem Ausfall

4. **Memory Management:**
   - Event Listener immer aufräumen (removeEventListener)
   - Ressourcen freigeben (close(), clear())
   - Bei wiederholten Operationen: auf Leaks achten

5. **JSDoc für alle Public Methods:**
   - Bessere IDE-Unterstützung
   - Selbstdokumentierender Code
   - Fehler werden früher erkannt

6. **Null-Checks bei globalen Objekten:**
   - `if (window.X)` vor `window.X.method()`
   - Besonders wichtig bei Optional Features

---

## 2025-11-10 – geo_fail / next_attempt – Schema-Drift

**Kategorie:** Backend (Python) + Datenbank (SQLite)  
**Schweregrad:** 🔴 KRITISCH  
**Dateien:** `db/schema.py`, `data/traffic.db`

### Symptom

- Serverstart bricht ab mit: `sqlite3.OperationalError: no such column: next_attempt`
- App startet nicht, keine Fehlerbehandlung
- Logs zeigen Stacktrace in `ensure_schema()`

### Ursache

- **Schema-Drift:** Alte Datenbankstruktur, aber neue Schema-Definition in `db/schema.py`
- Code versucht, Index auf Spalte `next_attempt` zu erstellen, die in bestehender DB noch nicht existiert
- `CREATE INDEX idx_geo_fail_next_attempt ON geo_fail(next_attempt)` schlägt fehl
- Keine Migrations-Logik für Schema-Updates in Production

### Fix

1. **Härtung in `ensure_schema()` für `geo_fail` eingebaut:**
   ```python
   # Prüfe, ob Spalte existiert, bevor Index erstellt wird
   cursor.execute("PRAGMA table_info(geo_fail)")
   columns = [col[1] for col in cursor.fetchall()]
   
   if 'next_attempt' not in columns:
       cursor.execute("ALTER TABLE geo_fail ADD COLUMN next_attempt INTEGER DEFAULT NULL")
   
   # Jetzt sicher: Index erstellen
   cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_fail_next_attempt ON geo_fail(next_attempt)")
   ```

2. **In Dev: Alte `traffic.db` gelöscht:**
   - Schema wird sauber neu aufgebaut
   - Entwicklungsdaten gehen verloren (aber kein Problem in Dev)

3. **Migration-Script erstellt:**
   - `db/migrations/2025-11-10_add_next_attempt.sql`
   - Für Production-Deployments

### Ergebnis

- ✅ App startet wieder
- ✅ Schema-Updates funktionieren auch bei existierenden DBs
- ✅ Migration-Prozess etabliert

### Was die KI künftig tun soll

1. **Immer Schema-Konsistenz prüfen:**
   - Bei Schema-Änderungen: Code vs. DB vergleichen
   - Tool: `sqlite3 data/traffic.db ".schema"` vs. `db/schema.py`

2. **Schema-Änderungen nie ohne Migration:**
   - Neue Spalten → ALTER TABLE in Migration-Script
   - Neue Indizes → CREATE INDEX IF NOT EXISTS
   - Backup vor Schema-Änderungen (in Production)

3. **Defensive Schema-Updates:**
   - Prüfe, ob Spalte/Index bereits existiert
   - `IF NOT EXISTS` bei CREATE-Statements
   - PRAGMA table_info() für Spalten-Checks

4. **Klare Empfehlung bei Schema-Fehlern:**
   - In Dev: "DB löschen und neu erstellen ist OK"
   - In Production: "Migration-Script schreiben und testen"
   - Niemals stillschweigend Fehler verschlucken

5. **Migrations-Ordner nutzen:**
   - Alle Schema-Updates in `db/migrations/`
   - Dateiname: `YYYY-MM-DD_beschreibung.sql`
   - Versionierung für Reproduzierbarkeit

---

## 2025-XX-XX – Sub-Routen-Generator: HTTP 500 / TypeError

**Kategorie:** Backend + Frontend  
**Schweregrad:** 🟡 MEDIUM  
**Dateien:** [Ausfüllen bei Bedarf]

### Symptom

- Frontend meldet Fehler beim Erzeugen von Subrouten
- Button "Routen optimieren (W-Touren & >4 Kunden)" → 500 Internal Server Error
- Browser-Konsole: `TypeError: Cannot read properties of undefined`

### Ursache

[Ausfüllen, sobald endgültig geklärt]

- Vermutung 1: Response-Format Backend ↔ Frontend inkonsistent
- Vermutung 2: Missing Validation im Backend
- Vermutung 3: OSRM-Timeout bei großen Touren

### Fix

[Konkrete Codeänderungen und Files verlinken, wenn Fix implementiert ist]

### Was die KI künftig tun soll

- Immer Frontend + Backend gemeinsam prüfen (API-Kontrakt!)
- Tests ergänzen, die Subrouten für kleine Beispieltouren abdecken
- Timeout-Handling bei OSRM-Calls verbessern
- Defensive Checks im Frontend bei API-Responses

---

## Template für neue Einträge

```md
## YYYY-MM-DD – [Kurzbeschreibung]

**Kategorie:** Backend/Frontend/DB/Infrastruktur  
**Schweregrad:** 🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW  
**Dateien:** [Liste]

### Symptom

- [Was wurde beobachtet?]
- [Fehlermeldungen, Logs]

### Ursache

- [Root Cause identifizieren]
- [Warum ist das passiert?]

### Fix

- [Konkrete Codeänderungen]
- [Dateinamen, Zeilen, Funktionen]

### Ergebnis

- [Code-Qualität Vorher/Nachher]
- [Erwartete Userwirkung]

### Was die KI künftig tun soll

1. [Lehre 1]
2. [Lehre 2]
3. [Lehre 3]
```

---

## Statistiken

**Gesamt-Audits:** 2  
**Kritische Fehler:** 2 (behoben)  
**Medium Fehler:** 0  
**Low Fehler:** 0

**Häufigste Fehlertypen:**

1. Schema-Drift (DB) – 1x
2. Syntax-Fehler (Frontend) – 1x
3. Missing Defensive Checks – 1x
4. Memory Leaks – 1x

**Lessons Learned (Top 3):**

1. ✅ Defensive Programmierung ist Pflicht (nicht optional)
2. ✅ Schema-Änderungen immer mit Migration-Script
3. ✅ API-Kontrakt zwischen Backend und Frontend dokumentieren

---

## 2025-11-14 – Sub-Routen-Generator – API-Kontrakt-Bruch ⚙️

### Kategorie
Backend ↔ Frontend Schnittstellen-Fehler (kritisches Feature)

### Symptom

- Sub-Routen-Generator Button funktioniert nicht
- HTTP-Fehler beim API-Call (4xx/5xx)
- JavaScript-Fehler: `TypeError: Cannot read properties of undefined`
- Leere oder falsch strukturierte Response-Daten

### Typische Root Causes

1. **API-Kontrakt-Bruch:**
   - Backend sendet `subRoutes` (camelCase), Frontend erwartet `sub_routes` (snake_case) oder umgekehrt

2. **Fehlendes Response-Schema:**
   - Backend gibt nur `{ success: true }` zurück
   - Frontend erwartet `{ sub_routes: [...], tours: [...] }`

3. **Fehlende Defensive Checks im Frontend:**
   - `data.sub_routes.forEach()` ohne zu prüfen, ob `sub_routes` existiert oder ein Array ist

4. **OSRM-Timeout nicht behandelt:**
   - Sub-Routen-Berechnung bricht ab, keine Fehlermeldung, kein Fallback

5. **Falsche HTTP-Methode:**
   - Frontend sendet GET, Backend erwartet POST (oder umgekehrt)

### Fix

**Backend: API-Kontrakt dokumentieren**
```python
@router.post("/api/tour/subroutes")
async def generate_subroutes(request: SubRouteRequest) -> SubRouteResponse:
    """
    Response-Schema:
    {
        "sub_routes": [{"id": "W01-1", "name": "...", "customers": [...], ...}],
        "tours": [...],
        "status": "success"
    }
    """
```

**Frontend: Defensive Validierung**
```javascript
const data = await response.json();
if (!Array.isArray(data.sub_routes)) {
    console.error('sub_routes ist kein Array:', data);
    showError('Keine Subrouten erhalten');
    return;
}
renderSubRoutes(data.sub_routes);
```

**Backend: OSRM-Fehler behandeln**
```python
try:
    route = await osrm_client.get_route(coords)
except OSRMTimeout:
    distance_km = calculate_haversine_distance(coords)
    geometry = create_simple_line(coords)
```

### Was die KI künftig tun soll

**Bei Sub-Routen-Generator Problemen:**

1. **IMMER Backend + Frontend gemeinsam prüfen**
2. **API-Kontrakt explizit dokumentieren** (Response-Schema als Kommentar)
3. **Defensive Programmierung erzwingen** (Array-Checks, Try-Catch)
4. **Golden Tests für Sub-Routen pflegen** (W01 Beispiel-Tour)
5. **Spezielle Template nutzen:** `docs/ki/CURSOR_PROMPT_TEMPLATE.md` → Template #10

---

**Ende des LESSONS_LOG**  
**Letzte Aktualisierung:** 2025-11-14

