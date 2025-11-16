# Reload-Mode Problem: Server verschwindet nach Reload

**Datum:** 2025-11-16  
**Status:** ✅ GELÖST  
**Problem:** Server verschwindet nach Dateiänderungen (Reload)

---

## 🔍 Problem

**Symptom:**
- Server startet erfolgreich
- Nach Dateiänderungen (z.B. Code-Änderungen) verschwindet der Server
- Port 8111 ist nicht mehr erreichbar
- Keine Python-Prozesse laufen mehr
- Browser zeigt: "ERR_CONNECTION_REFUSED"

**Ursache:**
- Uvicorn's Reload-Mode (`reload=True`) startet einen Reloader-Prozess
- Reloader überwacht Dateien und startet Worker-Prozess neu
- Bei Fehlern oder Timing-Problemen kann der Reloader abstürzen
- Server "verschwindet" ohne Fehlermeldung

---

## ✅ Lösung

**Reload-Mode standardmäßig deaktiviert:**

**Datei:** `start_server.py`

```python
# Reload-Mode nur aktivieren wenn explizit gewünscht
reload_enabled = os.getenv("ENABLE_RELOAD", "0") == "1"  # Standard: deaktiviert
log.info(f"Reload-Mode: {'aktiviert' if reload_enabled else 'deaktiviert (Standard für Stabilität)'}")

uvicorn.run(
    "backend.app:create_app",
    factory=True,
    host="127.0.0.1",
    port=8111,
    reload=reload_enabled,
    reload_dirs=["backend", "services", "routes", "db"] if reload_enabled else None,
    log_level="info",
)
```

**Ergebnis:**
- ✅ Server läuft stabil ohne Reload
- ✅ Keine unerwarteten Abstürze nach Dateiänderungen
- ✅ Reload kann bei Bedarf aktiviert werden: `$env:ENABLE_RELOAD="1"`

---

## 📚 Lektionen

### 1. Reload-Mode ist instabil

**Warum:**
- Reloader-Prozess kann abstürzen
- Timing-Probleme zwischen Reloader und Worker
- Fehler beim Neustart werden nicht immer geloggt

**Empfehlung:**
- Reload-Mode nur für Entwicklung aktivieren
- Produktion: Immer ohne Reload
- Bei Problemen: Reload deaktivieren

### 2. Server-Neustart ist zuverlässiger

**Vorteile:**
- Keine Timing-Probleme
- Klare Fehlermeldungen
- Stabile Ausführung

**Nachteile:**
- Manueller Neustart nötig
- Kein automatisches Hot-Reload

### 3. Reload-Mode optional machen

**Implementierung:**
- Über Umgebungsvariable steuerbar
- Standard: deaktiviert (Stabilität)
- Aktivierung: `ENABLE_RELOAD=1`

---

## 🔄 Verwendung

### Server ohne Reload (Standard):
```powershell
python start_server.py
```

### Server mit Reload (Entwicklung):
```powershell
$env:ENABLE_RELOAD="1"
python start_server.py
```

---

**Status:** ✅ Problem gelöst, Server läuft stabil ohne Reload

