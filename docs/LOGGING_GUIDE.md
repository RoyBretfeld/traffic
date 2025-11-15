# Logging-Leitfaden für FAMO TrafficApp

## Wo finde ich die Logs?

### 1. Browser-Konsole (Frontend-Logs)

**Öffnen:**
- Drücke **F12** im Browser
- Oder Rechtsklick → "Untersuchen" / "Inspect"
- Gehe zum Tab **"Console"**

**Was du siehst:**
- Frontend-Fehler
- API-Aufrufe
- Debug-Meldungen mit `[SUB-ROUTES]` oder `[TOUR-OPTIMIZE]`

**Filter:**
- Suche nach: `SUB-ROUTES`, `TOUR-OPTIMIZE`, `Fehler`, `ERROR`

**Beispiel:**
```
[SUB-ROUTES] Verarbeite Tour W-07.00: 5/5 Stopps mit Koordinaten
[SUB-ROUTES] API-Fehler für Tour W-07.00: {...}
```

---

### 2. Server-Terminal (Backend-Logs)

**Wo:**
- Das Terminal, in dem der Server läuft
- Normalerweise gestartet mit:
  ```bash
  python start_server.py
  ```
  oder
  ```bash
  python backend/app.py
  ```

**Was du siehst:**
- Alle Backend-Logs in Echtzeit
- Zeilen mit `[TOUR-OPTIMIZE]` zeigen Optimierungs-Details

**Beispiel:**
```
[TOUR-OPTIMIZE] Anfrage für Tour: W-07.00, 5 Stopps
[TOUR-OPTIMIZE] Tour W-07.00: 5/5 Stopps mit Koordinaten
[TOUR-OPTIMIZE] LLM-Optimizer Status: enabled=True, api_key=gesetzt
[TOUR-OPTIMIZE] Versuche LLM-Optimizer für Tour W-07.00
[TOUR-OPTIMIZE] LLM-Optimierung erfolgreich für Tour W-07.00 (Methode: gpt-4o-mini)
```

**Fehler-Beispiel:**
```
[TOUR-OPTIMIZE] LLM nicht verfügbar/Fehler für Tour W-07.00, verwende Nearest-Neighbor: ...
[TOUR-OPTIMIZE] LLM-Fehler Traceback:
  ...
[TOUR-OPTIMIZE] Nearest-Neighbor zurückgegeben: 5 Stops
[TOUR-OPTIMIZE] Index-Mapping: 5/5 Indizes gefunden
```

---

### 3. Log-Dateien (falls vorhanden)

**Verzeichnis:** `logs/`

**Dateien:**
- `logs/csv_import_debug.log` - CSV-Import-Debug-Logs
- `logs/csv_import_run_latest.log` - Letzte CSV-Import-Läufe

**Ansehen:**
```bash
# PowerShell
Get-Content logs/csv_import_debug.log -Tail 50

# CMD
type logs\csv_import_debug.log | more
```

---

## Häufige Fehler-Meldungen

### "API-Fehler bei allen X Tour(en)"

**Wo anschauen:**
1. Browser-Konsole (F12) → Suche nach `[SUB-ROUTES] API-Fehler`
2. Server-Terminal → Suche nach `[TOUR-OPTIMIZE] FEHLER`

**Was suchen:**
- HTTP-Status-Code (z.B. `500`, `400`)
- Fehlermeldung (z.B. `Optimierung fehlgeschlagen`)
- Details zur Tour (Anzahl Stopps, Koordinaten)

**Beispiel-Problem:**
```
[SUB-ROUTES] API-Fehler für Tour W-07.00: {
  status: 500,
  error: "Optimierung fehlgeschlagen: Index-Mapping unvollständig"
}
```

---

### "Keine Sub-Routen konnten generiert werden"

**Prüfen:**
1. Browser-Konsole → Suche nach `errorCount`
2. Server-Terminal → Prüfe ob API-Aufrufe ankommen

**Häufige Ursachen:**
- Keine Koordinaten für Stopps
- LLM-API-Fehler (ohne Fallback)
- Index-Mapping-Problem

---

## Debug-Modus aktivieren

**Backend:**
```bash
# Log-Level erhöhen
set LOG_LEVEL=DEBUG
python start_server.py
```

**Frontend:**
- Browser-Konsole ist standardmäßig aktiv
- Für mehr Details: Filter auf `DEBUG` setzen

---

## Logs speichern (optional)

**Browser-Konsole speichern:**
1. F12 öffnen
2. Rechtsklick in Konsole
3. "Save as..." oder Strg+S

**Server-Logs speichern:**
```bash
# PowerShell
python start_server.py | Tee-Object -FilePath "server.log"

# CMD
python start_server.py > server.log 2>&1
```

---

## Nächste Schritte bei Problemen

1. **Browser-Konsole prüfen** → Siehst du `[SUB-ROUTES]` Fehler?
2. **Server-Terminal prüfen** → Siehst du `[TOUR-OPTIMIZE]` Meldungen?
3. **Fehler-Meldung kopieren** → Schicke sie für weitere Hilfe
4. **Tour-Details notieren** → Welche Tour-ID? Wie viele Stopps?

