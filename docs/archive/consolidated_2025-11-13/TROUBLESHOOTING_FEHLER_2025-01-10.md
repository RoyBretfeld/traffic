# Troubleshooting - Fehler treten weiterhin auf

## Problem

Trotz aller Fixes treten weiterhin folgende Fehler auf:
1. `/health/db` gibt 500 (sollte 503 sein)
2. `file=undefined` im Match-Request
3. `body stream already read` in `runWorkflow`

## Mögliche Ursachen

### 1. Server wurde nicht neu gestartet
**Problem:** Alter Code läuft noch im Server-Prozess.

**Lösung:**
```powershell
# Alle Python-Prozesse beenden
taskkill /F /IM python.exe

# Server neu starten
python start_server.py
```

### 2. Browser-Cache lädt alte Version
**Problem:** Browser verwendet gecachte Version von `frontend/index.html`.

**Lösung:**
- **Strg+F5** (Hard Refresh) im Browser
- Oder: Browser-Entwicklertools öffnen → Netzwerk-Tab → "Cache deaktivieren" aktivieren
- Oder: Inkognito-Modus verwenden

### 3. Dateien wurden nicht korrekt gespeichert
**Problem:** Änderungen wurden nicht in die Dateien geschrieben.

**Lösung:**
- Prüfe, ob die Änderungen in den Dateien sind:
  - `frontend/index.html` - Zeile 846: `const responseText = await response.text();`
  - `frontend/index.html` - Zeile 674: `const responseText = await response.text();`
  - `backend/app.py` - Zeile 707: Endpunkt entfernt (nur Kommentar)
  - `routes/health_check.py` - Zeile 55: `status_code=503`

## Checkliste

### Server-Neustart
- [ ] Alle Python-Prozesse beendet (`taskkill /F /IM python.exe`)
- [ ] Server neu gestartet (`python start_server.py`)
- [ ] Server läuft auf Port 8111
- [ ] Keine Fehler in Server-Konsole

### Browser-Cache
- [ ] Hard Refresh durchgeführt (Strg+F5)
- [ ] Browser-Entwicklertools geöffnet
- [ ] "Cache deaktivieren" aktiviert (Netzwerk-Tab)
- [ ] Seite neu geladen

### Code-Verifikation
- [ ] `frontend/index.html` Zeile 846: `response.text()` vorhanden
- [ ] `frontend/index.html` Zeile 674: `response.text()` vorhanden
- [ ] `frontend/index.html` Zeile 617: `stagedPath` Extraktion korrekt
- [ ] `backend/app.py` Zeile 707: `/health/db` Endpunkt entfernt
- [ ] `routes/health_check.py` Zeile 55: `status_code=503`

## Debug-Schritte

### 1. Server-Logs prüfen
```powershell
# Server sollte folgende Meldung zeigen:
# "INFO:     Application startup complete."
# Keine Import-Fehler oder Syntax-Fehler
```

### 2. Browser-Konsole prüfen
- Öffne Browser-Entwicklertools (F12)
- Gehe zu "Konsole"-Tab
- Prüfe, ob Fehler noch auftreten
- Prüfe Netzwerk-Tab: Welche Requests schlagen fehl?

### 3. Endpunkt direkt testen
```powershell
# Teste /health/db direkt
Invoke-WebRequest -Uri "http://localhost:8111/health/db" -Method GET

# Sollte 200 oder 503 zurückgeben (nicht 500!)
```

### 4. Frontend-Version prüfen
- Öffne Browser-Entwicklertools
- Gehe zu "Quellcode"-Tab
- Öffne `frontend/index.html`
- Suche nach `response.text()` - sollte mehrfach vorkommen
- Suche nach `response.json()` - sollte NUR in `startGeocodingProgress` vorkommen (Zeile 729)

## Bekannte Probleme

### Problem: `/health/db` gibt immer noch 500
**Ursache:** Alter Server-Prozess läuft noch oder Endpunkt wurde nicht korrekt entfernt.

**Lösung:**
1. Prüfe `backend/app.py` Zeile 707 - sollte nur Kommentar sein
2. Prüfe `routes/health_check.py` Zeile 38-55 - sollte `status_code=503` haben
3. Server neu starten

### Problem: `file=undefined` tritt weiterhin auf
**Ursache:** Browser-Cache oder `uploadCsvFile` wird nicht korrekt aufgerufen.

**Lösung:**
1. Hard Refresh (Strg+F5)
2. Prüfe Browser-Konsole: Wird `apiUploadCsv` korrekt aufgerufen?
3. Prüfe `uploadCsvFile` Zeile 617: `stagedPath` Extraktion

### Problem: `body stream already read` tritt weiterhin auf
**Ursache:** Browser-Cache oder es gibt noch eine weitere Stelle.

**Lösung:**
1. Hard Refresh (Strg+F5)
2. Prüfe alle Stellen, die `response.text()` oder `response.json()` aufrufen
3. Suche nach doppelten Aufrufen

## Notfall-Rollback

Falls nichts funktioniert:

1. **Backup wiederherstellen:**
   ```powershell
   # Falls Backup vorhanden
   Copy-Item "backups\extracted_backup\*" -Destination "." -Recurse -Force
   ```

2. **Git-Reset (falls Git verwendet wird):**
   ```powershell
   git checkout HEAD -- frontend/index.html
   git checkout HEAD -- backend/app.py
   ```

3. **Manuelle Korrekturen:**
   - Siehe `docs/FIXES_2025-01-10.md` für alle Änderungen
   - Wende Änderungen manuell an

## Nächste Schritte

1. ✅ Server komplett neu starten
2. ✅ Browser-Cache leeren (Strg+F5)
3. ✅ Endpunkte testen
4. ✅ Browser-Konsole prüfen
5. ✅ Falls Fehler weiterhin auftreten: Debug-Schritte durchführen

---

**Erstellt:** 2025-01-10  
**Status:** Troubleshooting-Guide

