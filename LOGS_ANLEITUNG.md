# 📋 Wo finde ich die Debug-Logs?

## 🖥️ OPTION 1: Console/CMD (EMPFOHLEN)

Die Logs erscheinen **direkt in der Console**, wo Sie den Server starten!

### Schritt-für-Schritt:

#### 1️⃣ Server starten

```powershell
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
python start_server.py
```

#### 2️⃣ Server läuft → Console zeigt Start-Logs

```
INFO:     Uvicorn running on http://127.0.0.1:8111 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
[OSRM] Client initialisiert: base_url=http://127.0.0.1:5000, available=True
INFO:     Application startup complete.
```

#### 3️⃣ Request senden → **Detaillierte Logs erscheinen!**

Wenn Sie jetzt eine Tour optimieren lassen, sehen Sie:

```
================================================================================
[TOUR-OPTIMIZE] 🚀 START - Trace-ID: abc123de
================================================================================
[TOUR-OPTIMIZE] 📥 Request empfangen:
  • Tour ID: W-07.00
  • BAR Tour: false
  • Anzahl Stopps: 45
  • Trace-ID: abc123de

[TOUR-OPTIMIZE] 📍 Koordinaten-Check:
  • Gesamt Stopps: 45
  • Mit Koordinaten: 42
  • Ohne Koordinaten: 3

[TOUR-OPTIMIZE] 🔄 Starte Optimierung für Tour W-07.00...
[TOUR-OPTIMIZE] 📊 Verwende 42 valide Stopps
[TOUR-OPTIMIZE] 🎯 Methode: optimize_tour_stops() (Backup-Version)
[TOUR-OPTIMIZE] ⚙️ Versuche Optimierung...

[TOUR-OPTIMIZE] ℹ️ LLM ist DEAKTIVIERT
[TOUR-OPTIMIZE] 🔄 Verwende Nearest-Neighbor direkt...
[TOUR-OPTIMIZE] ✅ Nearest-Neighbor abgeschlossen: 42 Stopps

[TOUR-OPTIMIZE] 📋 Erstelle Stopps-Kopien...
[TOUR-OPTIMIZE] 📦 Optimierte Stopps: 42

[TOUR-OPTIMIZE] ⏱️ Berechne Zeitbudget...
  • Fahrzeit: 45.3 Min
  • Servicezeit: 84 Min
  • Gesamtzeit: 129.3 Min

[TOUR-OPTIMIZE] 🔍 Validiere Variablen...
[TOUR-OPTIMIZE] ✅ Alle Variablen validiert

[TOUR-OPTIMIZE] ℹ️ Keine Aufteilung nötig (is_split=false)

================================================================================
[TOUR-OPTIMIZE] ✅ ERFOLGREICH ABGESCHLOSSEN - Trace-ID: abc123de
  • Tour ID: W-07.00
  • Optimierte Stopps: 42
  • Methode: nearest_neighbor
  • Gesamtzeit: 129.3 Min
  • Aufgeteilt: false
================================================================================
```

### 💡 TIPPS für Console-Logs:

1. **Console-Fenster maximieren**
   - Damit Sie alle Logs sehen können

2. **Scrollen Sie nach oben**
   - Falls viele Logs kommen

3. **Logs bleiben in der Console**
   - Auch nach dem Request

4. **Bei Fehler:**
   - Screenshot machen ODER
   - Text markieren → Rechtsklick → Copy (oder Strg+C)
   - Hier einfügen

---

## 📄 OPTION 2: Logs in Datei umleiten (Optional)

Falls Sie die Logs dauerhaft speichern möchten:

### PowerShell:

```powershell
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
python start_server.py 2>&1 | Tee-Object -FilePath server_logs.txt
```

**Was passiert:**
- Logs erscheinen **sowohl** in der Console **als auch** in `server_logs.txt`
- Datei wird live mitgeschrieben

**Datei öffnen:**
```powershell
notepad server_logs.txt
```

### CMD (Alternative):

```cmd
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
python start_server.py > server_logs.txt 2>&1
```

**Achtung bei CMD:**
- Logs erscheinen **nur** in der Datei, **nicht** in der Console

---

## 🎯 EMPFEHLUNG

**Für Debugging: OPTION 1 (Console)**

**Warum?**
- ✅ Echtzeit-Feedback
- ✅ Sofort sichtbar
- ✅ Kein Extra-Schritt (Datei öffnen)
- ✅ Farbige Ausgabe (falls Terminal unterstützt)

**Für längere Test-Sessions: OPTION 2 (Datei)**

**Warum?**
- ✅ Logs bleiben gespeichert
- ✅ Kann später analysiert werden
- ✅ Gut für mehrere Requests

---

## 📸 Bei Fehler - So gehen Sie vor:

### 1. Screenshot machen

**Windows:**
- `Win + Shift + S` → Bereich auswählen → Screenshot erstellt
- Oder: `Win + PrtScr` → Screenshot gespeichert

### 2. Text kopieren

**Aus PowerShell/CMD:**
1. Text markieren (mit Maus ziehen)
2. Rechtsklick → "Copy" ODER
3. Strg + C (in neueren PowerShell-Versionen)
4. Hier einfügen

### 3. Relevante Logs identifizieren

Suchen Sie nach:
- ❌ `[TOUR-OPTIMIZE] ❌❌❌ KRITISCHER FEHLER`
- 🔴 `[TOUR-OPTIMIZE] 🔴 DATENBANK-FEHLER`
- ⚠️ `[TOUR-OPTIMIZE] ⚠️` (Warnungen)

Kopieren Sie:
- Die gesamte `================` Sektion
- Den Traceback (falls vorhanden)
- Die Trace-ID (z.B. `Trace-ID: abc123de`)

---

## 🔍 Beispiel: So sieht ein FEHLER aus

```
================================================================================
[TOUR-OPTIMIZE] ❌❌❌ KRITISCHER FEHLER bei Optimierung ❌❌❌
  • Exception-Typ: ValueError
  • Fehlermeldung: invalid coordinates: lat=None
  • Tour ID: W-07.00
  • Anzahl valid_stops: 42
[TOUR-OPTIMIZE] 📋 Vollständiger Traceback:
Traceback (most recent call last):
  File "E:\...\workflow_api.py", line 2095, in optimize_tour_with_ai
    result = llm_optimizer.optimize_route(valid_stops, region="Dresden")
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid coordinates: lat=None

[TOUR-OPTIMIZE] 🚨 KRITISCHER FALLBACK: Verwende Identität (Original-Reihenfolge)
  • Fallback Stopps: 42
================================================================================
```

**Das ist genau das, was wir brauchen!** 👆

---

## 🚀 JETZT: Server starten und testen!

```powershell
python start_server.py
```

Dann:
1. CSV hochladen
2. Sub-Routen generieren
3. **Logs in der Console lesen**
4. Bei Fehler: Kopieren/Screenshot → Hier posten

**Viel Erfolg!** 🎯

