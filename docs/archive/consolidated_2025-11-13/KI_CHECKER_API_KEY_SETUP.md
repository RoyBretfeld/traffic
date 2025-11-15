# KI-Checker API-Key Setup
**Datum:** 2025-01-10  
**Status:** 📋 Anleitung

---

## 🔑 OPENAI_API_KEY konfigurieren

Der KI-CodeChecker benötigt einen OpenAI API-Key, um Code-Verbesserungen durchzuführen.

---

## 📋 Schritt 1: API-Key erhalten

1. Gehe zu https://platform.openai.com/api-keys
2. Erstelle einen neuen API-Key
3. Kopiere den Key (beginnt mit `sk-...`)

**Wichtig:** 
- Verwende GPT-4o-mini (günstig, schnell)
- Key sollte geheim bleiben (nicht in Git committen!)

---

## 📋 Schritt 2: API-Key in config.env setzen

### Option A: config.env bearbeiten

1. Öffne `config.env` im Projekt-Root
2. Füge folgende Zeile hinzu (oder aktualisiere, falls vorhanden):
   ```
   OPENAI_API_KEY=sk-dein-api-key-hier
   ```
3. Speichere die Datei

### Option B: Umgebungsvariable setzen (Windows)

```powershell
# Temporär (nur für diese Session)
$env:OPENAI_API_KEY="sk-dein-api-key-hier"

# Oder dauerhaft (System-Umgebungsvariable)
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-dein-api-key-hier", "User")
```

### Option C: Umgebungsvariable setzen (Linux/Mac)

```bash
# Temporär (nur für diese Session)
export OPENAI_API_KEY="sk-dein-api-key-hier"

# Oder dauerhaft (in ~/.bashrc oder ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-dein-api-key-hier"' >> ~/.bashrc
source ~/.bashrc
```

---

## 📋 Schritt 3: Server neu starten

1. **Server stoppen** (Ctrl+C im Terminal)
2. **Server neu starten:**
   ```bash
   python start_server.py
   ```

3. **Prüfe Startup-Log:**
   - ✅ Erfolg: `[STARTUP] ✅ KI-CodeChecker Background-Job gestartet`
   - ⚠️ Fehler: `[STARTUP] ⚠️ KI-CodeChecker nicht verfügbar (OPENAI_API_KEY fehlt)`

---

## 📋 Schritt 4: Status prüfen

### Über API:
```bash
curl http://localhost:8111/api/code-improvement-job/status
```

**Erwartete Antwort:**
```json
{
  "enabled": true,
  "is_running": true,
  "last_run": "2025-01-10T18:00:00",
  "total_improvements": 0,
  "total_failures": 0,
  "interval_seconds": 3600,
  "max_improvements_per_run": 3,
  "ai_checker_available": true
}
```

### Über Dashboard:
1. Öffne http://127.0.0.1:8111/admin/ki-improvements
2. Prüfe Status-Karten
3. Prüfe ob "KI-Checker verfügbar" angezeigt wird

---

## 🔍 Troubleshooting

### Problem: "OPENAI_API_KEY nicht gesetzt"

**Lösung:**
1. Prüfe ob `config.env` existiert
2. Prüfe ob Zeile `OPENAI_API_KEY=...` vorhanden ist
3. Prüfe ob kein Leerzeichen um `=` ist
4. Prüfe ob Key mit `sk-` beginnt

### Problem: "KI-Checker nicht verfügbar"

**Lösung:**
1. Prüfe ob API-Key gültig ist
2. Prüfe ob API-Key nicht abgelaufen ist
3. Prüfe ob OpenAI-Konto aktiv ist
4. Prüfe Server-Logs für Details

### Problem: "Background-Job läuft nicht"

**Lösung:**
1. Prüfe ob `enabled: true` in Status
2. Prüfe ob `ai_checker_available: true` in Status
3. Starte Job manuell: `POST /api/code-improvement-job/start`

---

## 🔒 Sicherheit

### ⚠️ WICHTIG: API-Key schützen

1. **NICHT in Git committen:**
   - `config.env` sollte in `.gitignore` sein
   - Prüfe: `git check-ignore config.env`

2. **NICHT in Logs ausgeben:**
   - API-Key wird nie in Logs geloggt
   - Nur Status (verfügbar/nicht verfügbar) wird geloggt

3. **NICHT in Frontend senden:**
   - API-Key bleibt im Backend
   - Frontend kommuniziert nur über API-Endpoints

---

## 📊 Kosten-Überwachung

Der KI-Checker verwendet **GPT-4o-mini** (günstig):
- Input: €0.00015 pro 1000 Tokens
- Output: €0.0006 pro 1000 Tokens

**Standard-Limits:**
- Tägliches Limit: €5.00
- Max. API-Calls/Tag: 50
- Max. Verbesserungen/Tag: 10

**Kosten prüfen:**
```bash
curl http://localhost:8111/api/ki-improvements/costs
```

---

## ✅ Checkliste

- [ ] API-Key von OpenAI erhalten
- [ ] API-Key in `config.env` gesetzt
- [ ] Server neu gestartet
- [ ] Startup-Log zeigt "✅ KI-CodeChecker Background-Job gestartet"
- [ ] Status-Endpoint zeigt `is_running: true`
- [ ] Dashboard zeigt "KI-Checker verfügbar"

---

## 📝 Notizen

- API-Key wird beim Server-Start aus `config.env` geladen
- Falls `config.env` nicht existiert, wird aus Umgebungsvariablen gelesen
- Falls beides fehlt, ist KI-Checker nicht verfügbar (aber System funktioniert weiterhin)

