# Background-Job für kontinuierliche Code-Verbesserungen
**Datum:** 2025-01-10  
**Status:** ✅ IMPLEMENTIERT

---

## ✅ Implementierte Komponenten

### 1. CodeImprovementJob (`backend/services/code_improvement_job.py`)
- ✅ Kontinuierliche Code-Verbesserungen
- ✅ Rate-Limiting (max. X Verbesserungen pro Runde)
- ✅ Priorisierung von Dateien
- ✅ Integration mit allen Services (CostTracker, SafetyManager, etc.)
- ✅ Exclude-Patterns für ausgeschlossene Verzeichnisse

### 2. API-Endpoints (`routes/code_improvement_job_api.py`)
- ✅ `GET /api/code-improvement-job/status` - Status abfragen
- ✅ `POST /api/code-improvement-job/start` - Job starten
- ✅ `POST /api/code-improvement-job/stop` - Job stoppen
- ✅ `POST /api/code-improvement-job/run-once` - Einmalige Runde

### 3. Standalone-Script (`scripts/start_background_job.py`)
- ✅ Kann als eigenständiger Prozess laufen
- ✅ Für Systemd/Service-Integration geeignet

---

## 🔧 Konfiguration

### config/app.yaml

```yaml
ki_codechecker:
  background_job:
    enabled: true  # Background-Job aktivieren
    interval_seconds: 3600  # Intervall: 1 Stunde
    max_improvements_per_run: 3  # Max. 3 Verbesserungen pro Runde
    priority_files:  # Dateien die zuerst verbessert werden sollen
      - "routes/workflow_api.py"
      - "backend/app.py"
    exclude_patterns:  # Ausgeschlossene Patterns
      - "**/__pycache__/**"
      - "**/node_modules/**"
      - "**/.git/**"
      - "**/venv/**"
      - "**/env/**"
      - "**/tests/**"
      - "**/backups/**"
```

---

## 🚀 Verwendung

### 1. Über API starten

```bash
# Status abfragen
curl http://localhost:8111/api/code-improvement-job/status

# Job starten
curl -X POST http://localhost:8111/api/code-improvement-job/start

# Einmalige Runde ausführen
curl -X POST http://localhost:8111/api/code-improvement-job/run-once

# Job stoppen
curl -X POST http://localhost:8111/api/code-improvement-job/stop
```

### 2. Als Standalone-Script

```bash
# Direkt ausführen
python scripts/start_background_job.py

# Im Hintergrund
nohup python scripts/start_background_job.py > background_job.log 2>&1 &
```

### 3. Als Systemd-Service (Linux)

```ini
# /etc/systemd/system/code-improvement-job.service
[Unit]
Description=Code Improvement Background Job
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="OPENAI_API_KEY=sk-..."
ExecStart=/usr/bin/python3 /path/to/project/scripts/start_background_job.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 📊 Workflow

```
1. Background-Job startet
   ↓
2. Finde Dateien zum Verbessern (priorisiert)
   ↓
3. Prüfe Rate-Limits (Kosten, API-Calls, Verbesserungen)
   ↓
4. Für jede Datei (max. max_improvements_per_run):
   - Analysiere Code
   - Generiere Verbesserungen
   - Wende sicher an (mit Tests)
   - Benachrichtige bei Erfolg/Fehler
   ↓
5. Warte Intervall
   ↓
6. Wiederhole ab Schritt 2
```

---

## 🎯 Priorisierung

### 1. Priority-Dateien
- Dateien aus `priority_files` werden zuerst verbessert

### 2. Dateien mit vielen Issues
- Dateien werden nach Anzahl Issues sortiert
- Dateien mit mehr Issues werden zuerst verbessert

### 3. Ausgeschlossene Patterns
- `__pycache__`, `node_modules`, `.git`, `venv`, `tests`, `backups` werden ignoriert

---

## 🔒 Sicherheit

### Rate-Limiting
- **Max. Verbesserungen pro Runde:** 3 (konfigurierbar)
- **Tages-Limit:** 10 Verbesserungen (CostTracker)
- **Kosten-Limit:** 5€/Tag (CostTracker)
- **API-Call-Limit:** 50/Tag (CostTracker)

### Safety-Checks
- ✅ Validierung vor Anwendung
- ✅ Tests nach Anwendung
- ✅ Automatischer Rollback bei Fehlern
- ✅ Backup vor jeder Änderung

---

## 📊 Monitoring

### Status-Endpoint

```json
{
  "enabled": true,
  "is_running": true,
  "last_run": "2025-01-10T14:30:00",
  "total_improvements": 15,
  "total_failures": 2,
  "interval_seconds": 3600,
  "max_improvements_per_run": 3,
  "ai_checker_available": true
}
```

### Benachrichtigungen
- ✅ E-Mail bei jeder Verbesserung
- ✅ Dashboard-Updates (WebSocket)
- ✅ Log-Dateien

---

## 🎉 Status

**Background-Job:** ✅ **100% IMPLEMENTIERT**

**Features:**
- ✅ Kontinuierliche Verbesserungen
- ✅ Rate-Limiting
- ✅ Priorisierung
- ✅ Safety-Checks
- ✅ API-Endpoints
- ✅ Standalone-Script

---

**Das System ist einsatzbereit!** 🚀

