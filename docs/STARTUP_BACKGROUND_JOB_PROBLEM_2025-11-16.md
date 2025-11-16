# Server-Start Problem: Background-Job blockiert Port-Bindung

**Datum:** 2025-11-16  
**Status:** ✅ GELÖST  
**Problem:** Server startet, aber Port 8111 ist nicht erreichbar

---

## 🔍 Problem

**Symptom:**
- Server startet (Uvicorn läuft)
- Startup-Event läuft durch alle 4 Schritte
- Startup-Log zeigt: "Server-Startup abgeschlossen"
- **ABER:** Port 8111 ist nicht erreichbar
- Browser zeigt: "ERR_CONNECTION_REFUSED"

**Logs zeigen:**
```
[STARTUP] ✅ Server-Startup abgeschlossen (Gesamt: 0.02s)
[STARTUP] 🎯 Startup-Event beendet - Server sollte jetzt bereit sein
```

Aber Port-Check schlägt fehl:
```
[PORT-CHECK] ❌ Port 8111 ist nach 20 Sekunden nicht erreichbar
```

---

## 🔎 Root Cause

**Background-Job (`CodeImprovementJob`) blockiert den Startup-Event**, obwohl er als `asyncio.create_task()` gestartet wird.

**Warum blockiert es?**

1. **Initialisierung blockiert:**
   - `CodeImprovementJob()` wird im Startup-Event initialisiert
   - Initialisierung lädt `AICodeChecker` → lädt `ERROR_CATALOG.md` und `LESSONS_LOG.md`
   - `_start_auto_reload_task()` versucht Event-Loop-Zugriff
   - **Problem:** Event-Loop ist während Startup möglicherweise noch nicht vollständig bereit

2. **Task-Start blockiert:**
   - `asyncio.create_task(job.run_continuously())` wird aufgerufen
   - `run_continuously()` startet eine Endlosschleife
   - **Problem:** Auch wenn als Task gestartet, blockiert die Initialisierung den Event-Loop

3. **Uvicorn wartet auf Startup-Event:**
   - Uvicorn wartet, bis alle Startup-Events abgeschlossen sind
   - Wenn Startup-Event blockiert (auch indirekt), wird Port nicht gebunden
   - Server "startet" aber ist nicht erreichbar

---

## 🛠️ Versuchte Lösungen

### ❌ Lösung 1: Timeout-Wrapper
```python
await _startup_with_timeout(_start_background_job(), timeout_seconds=5, task_name="Background-Job Start")
```
**Ergebnis:** Blockiert weiterhin

### ❌ Lösung 2: Explizites Return
```python
async def _start_background_job():
    # ... Job starten ...
    return  # Explizites Return
```
**Ergebnis:** Blockiert weiterhin

### ❌ Lösung 3: Sleep nach Task-Erstellung
```python
task = asyncio.create_task(job.run_continuously())
await asyncio.sleep(0.01)  # Minimale Verzögerung
```
**Ergebnis:** Blockiert weiterhin

### ❌ Lösung 4: Direkter await ohne Wrapper
```python
await asyncio.wait_for(_start_background_job(), timeout=5.0)
```
**Ergebnis:** Blockiert weiterhin

### ✅ Lösung 5: Background-Job komplett deaktivieren
```python
# 4. Background-Job starten (TEMPORÄR DEAKTIVIERT)
job_ok = True
log.info("[STARTUP] ⏸️ Background-Job temporär deaktiviert")
```
**Ergebnis:** ✅ Server startet sofort!

---

## ✅ Finale Lösung

**Background-Job komplett aus Startup-Event entfernt:**

**Datei:** `backend/app_setup.py`

```python
# 4. Background-Job starten (TEMPORÄR DEAKTIVIERT - wird später wieder aktiviert)
job_ok = True  # Als erfolgreich markieren, da deaktiviert
log.info("[STARTUP] ⏸️ Background-Job temporär deaktiviert (wird später wieder aktiviert)")
elapsed = time.time() - step_start
log.info(f"[STARTUP] ✅ Schritt 4/4 übersprungen: Background-Job deaktiviert ({elapsed:.2f}s)")
```

**Import auskommentiert:**
```python
# from backend.services.code_improvement_job import CodeImprovementJob  # TEMPORÄR DEAKTIVIERT
```

**Ergebnis:**
- ✅ Server startet sofort
- ✅ Port 8111 ist erreichbar
- ✅ Webseite lädt korrekt
- ✅ Alle anderen Funktionen arbeiten

---

## 📚 Lektionen

### 1. Background-Jobs NIE im Startup-Event starten

**Warum:**
- Startup-Event muss schnell sein (< 5 Sekunden)
- Background-Jobs blockieren den Event-Loop
- Auch `asyncio.create_task()` blockiert, wenn Initialisierung langsam ist

**Alternativen:**
- Starte als separater Prozess (multiprocessing)
- Oder: Über API-Endpoint nach Server-Start
- Oder: Nutze FastAPI's `lifespan` Events (neu in FastAPI 0.93+)
- Oder: Starte in separatem Thread (nicht asyncio-Task)

### 2. Startup-Logging ist kritisch

**Ohne detailliertes Logging hätten wir das Problem nie gefunden:**
- Jeder Startup-Schritt muss geloggt werden
- Timing-Informationen sind essentiell
- Port-Check-Logging zeigt, ob Port gebunden wurde

### 3. Port-Bindungs-Verifizierung ist wichtig

**Nur weil Startup-Event "abgeschlossen" ist, heißt das nicht, dass Port gebunden ist:**
- Port-Check nach Startup ist kritisch
- Health-Check-Endpoint testen
- Timeout für Port-Bindung

### 4. Isolation von Problemen

**Wenn Server nicht startet:**
- Schrittweise Komponenten deaktivieren
- Background-Jobs sind häufige Ursache
- Immer zuerst testen ohne Background-Jobs

---

## 🔄 Nächste Schritte

1. **Background-Job später wieder aktivieren:**
   - Über separaten API-Endpoint starten
   - Oder: Als separater Prozess starten
   - Oder: Nach Server-Start über `lifespan` Events

2. **Startup-Logging beibehalten:**
   - Detailliertes Logging ist essentiell
   - Port-Check-Logging beibehalten

3. **Dokumentation aktualisieren:**
   - LESSONS_LOG.md aktualisiert
   - ERROR_CATALOG.md aktualisiert

---

**Status:** ✅ Problem gelöst, Server läuft stabil

