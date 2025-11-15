# KI-Checker Status & Troubleshooting
**Datum:** 2025-01-10

---

## ✅ Aktueller Status

- **config.env:** ✅ Existiert
- **OPENAI_API_KEY:** ✅ In config.env gesetzt
- **Background-Job:** ⚠️ Muss neu gestartet werden

---

## 🔧 Nächste Schritte

### 1. Server neu starten

Der Auto-Start-Code wurde hinzugefügt, aber der Server muss neu gestartet werden:

```bash
# Server stoppen (Ctrl+C)
# Dann neu starten:
python start_server.py
```

**Erwartete Ausgabe beim Start:**
```
[STARTUP] ✅ KI-CodeChecker Background-Job gestartet
```

### 2. Status prüfen

Nach dem Neustart:

```bash
# Status-Endpoint
curl http://localhost:8111/api/code-improvement-job/status

# Erwartete Antwort:
{
  "enabled": true,
  "is_running": true,
  "ai_checker_available": true
}
```

### 3. Dashboard prüfen

Öffne: http://127.0.0.1:8111/admin/ki-improvements

- Status-Karten sollten "KI-Checker verfügbar" anzeigen
- Background-Job sollte "Läuft" anzeigen

---

## 🔍 Wenn es nicht funktioniert

### Problem: "KI-Checker nicht verfügbar"

**Prüfe:**
1. Ist `OPENAI_API_KEY` in `config.env`?
2. Beginnt der Key mit `sk-`?
3. Ist der Key gültig (nicht abgelaufen)?

**Lösung:**
- Prüfe `config.env` Datei
- Teste Key manuell: `python -c "from backend.services.ai_code_checker import get_ai_code_checker; print(get_ai_code_checker())"`

### Problem: "Background-Job läuft nicht"

**Prüfe:**
1. Server-Logs beim Start
2. Status-Endpoint: `is_running` sollte `true` sein

**Lösung:**
- Job manuell starten: `POST /api/code-improvement-job/start`
- Prüfe ob `enabled: true` in Status

---

## 📊 Monitoring

### Kosten prüfen:
```bash
curl http://localhost:8111/api/ki-improvements/costs
```

### Performance prüfen:
```bash
curl http://localhost:8111/api/ki-improvements/performance
```

### Letzte Verbesserungen:
```bash
curl http://localhost:8111/api/ki-improvements/recent?limit=10
```

---

## ✅ Checkliste

- [x] config.env existiert
- [x] OPENAI_API_KEY in config.env gesetzt
- [ ] Server neu gestartet (nach Auto-Start-Implementierung)
- [ ] Startup-Log zeigt "✅ KI-CodeChecker Background-Job gestartet"
- [ ] Status-Endpoint zeigt `is_running: true`
- [ ] Dashboard zeigt "KI-Checker verfügbar"

