# KI-CodeChecker: Benachrichtigungskonzept
**Datum:** 2025-01-10  
**Status:** 📋 KONZEPT  
**Priorität:** HOCH

---

## 🎯 Ziel

Ein umfassendes Benachrichtigungssystem, das Entwickler über alle KI-Code-Änderungen informiert und auf dem Laufenden hält.

---

## 📢 Benachrichtigungskanäle

### 1. Dashboard (Hauptkanal) ⭐ EMPFOHLEN

**Zweck:** Zentrale Übersicht aller Änderungen

#### Features:
- **Live-Updates** (WebSocket)
- **Änderungshistorie** (alle Verbesserungen)
- **Diff-Vorschau** (direkt im Browser)
- **Status-Anzeige** (erfolgreich, fehlgeschlagen, rollback)
- **Filter & Suche** (nach Datei, Datum, Status)
- **Metriken** (Verbesserungsrate, Anzahl Änderungen)

#### UI-Layout:
```
┌─────────────────────────────────────────────────────────┐
│  KI-CodeChecker Dashboard                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Status (Heute)                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Verbesserungen│  │ Erfolgreich │  │ Fehlgeschlagen│   │
│  │     3 / 5    │  │     3       │  │      0       │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                          │
│  📝 Letzte Verbesserungen                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ [14:30] routes/upload_csv.py                      │ │
│  │ ✅ Erfolgreich | 2 Issues behoben | Diff anzeigen │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ [12:15] frontend/index.html                       │ │
│  │ ✅ Erfolgreich | 1 Issue behoben | Diff anzeigen │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ [10:45] routes/workflow_api.py                    │ │
│  │ ⚠️ Rollback | Tests fehlgeschlagen | Details     │ │
│  └──────────────────────────────────────────────────┘ │
│                                                          │
│  🔔 Benachrichtigungen                                  │
│  ┌──────────────────────────────────────────────────┐ │
│  │ [14:30] Neue Verbesserung: routes/upload_csv.py  │ │
│  │ [12:15] Neue Verbesserung: frontend/index.html   │ │
│  │ [10:45] Rollback: routes/workflow_api.py         │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

### 2. E-Mail-Benachrichtigungen

**Zweck:** Wichtige Änderungen per E-Mail

#### E-Mail-Typen:

##### A. Code-Verbesserung (Erfolgreich)
```
Betreff: [KI-CodeChecker] ✅ Code-Verbesserung: routes/upload_csv.py

Hallo Entwickler,

die KI hat erfolgreich eine Code-Verbesserung vorgenommen:

📁 Datei: routes/upload_csv.py
🕐 Zeit: 2025-01-10 14:30:22
🔧 Issues behoben: 2
✅ Status: Erfolgreich
📊 Tests: Alle bestanden

Änderungen:
- Fehlendes Error-Handling hinzugefügt (Zeile 42-45)
- Hardcoded Pfad durch konfigurierbaren Pfad ersetzt (Zeile 48)

Diff-Vorschau:
--- original/routes/upload_csv.py
+++ fixed/routes/upload_csv.py
@@ -42,6 +42,9 @@
-    content = file.read()
+    try:
+        content = file.read()
+    except Exception as e:
+        raise IOError(f"Failed to read file: {e}")

💾 Backup: data/code_fixes_backup/upload_csv_20250110_143022.py
🔗 Dashboard: http://localhost:8111/admin/ki-improvements

---
KI-CodeChecker System
```

##### B. Rollback (Fehlgeschlagen)
```
Betreff: [KI-CodeChecker] ⚠️ Rollback: routes/workflow_api.py

Hallo Entwickler,

die KI hat versucht eine Code-Verbesserung vorzunehmen, 
aber die Tests nach der Änderung sind fehlgeschlagen.
Die Änderung wurde automatisch rückgängig gemacht.

📁 Datei: routes/workflow_api.py
🕐 Zeit: 2025-01-10 10:45:15
❌ Status: Rollback (Tests fehlgeschlagen)
🔧 Issues (nicht behoben): 1

Grund:
- Test "test_workflow_upload" ist fehlgeschlagen
- Fehler: AssertionError: Expected 200, got 500

💾 Backup: data/code_fixes_backup/workflow_api_20250110_104515.py
🔗 Dashboard: http://localhost:8111/admin/ki-improvements

---
KI-CodeChecker System
```

##### C. Tages-Zusammenfassung
```
Betreff: [KI-CodeChecker] 📊 Tages-Zusammenfassung: 2025-01-10

Hallo Entwickler,

hier ist die Zusammenfassung der KI-Code-Verbesserungen für heute:

📊 Statistiken:
- Verbesserungen: 5 / 5 (Limit erreicht)
- Erfolgreich: 4
- Fehlgeschlagen: 1
- Erfolgsrate: 80%

📝 Verbesserungen:
1. routes/upload_csv.py - ✅ Erfolgreich (2 Issues)
2. frontend/index.html - ✅ Erfolgreich (1 Issue)
3. routes/health_check.py - ✅ Erfolgreich (1 Issue)
4. common/normalize.py - ✅ Erfolgreich (1 Issue)
5. routes/workflow_api.py - ⚠️ Rollback (Tests fehlgeschlagen)

🔗 Dashboard: http://localhost:8111/admin/ki-improvements

---
KI-CodeChecker System
```

---

### 3. In-App-Benachrichtigungen

**Zweck:** Sofortige Benachrichtigung während der Arbeit

#### Toast-Notifications (oben rechts)
```javascript
// Beispiel: Toast-Notification
function showImprovementNotification(improvement) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-robot"></i> KI-CodeChecker
        </div>
        <div class="toast-body">
            <strong>Code-Verbesserung:</strong> ${improvement.file}
            <br>
            <small>${improvement.issues_fixed} Issues behoben</small>
        </div>
        <div class="toast-actions">
            <button onclick="showDiff('${improvement.file}')">Diff anzeigen</button>
            <button onclick="dismissToast()">Schließen</button>
        </div>
    `;
    document.body.appendChild(toast);
    
    // Auto-close nach 10 Sekunden
    setTimeout(() => toast.remove(), 10000);
}
```

#### Sidebar-Widget
```html
<!-- In der Sidebar -->
<div class="ki-improvements-widget">
    <h5><i class="fas fa-robot"></i> KI-Verbesserungen</h5>
    <div class="improvement-badge" id="improvement-badge">
        <span class="badge bg-success">3 heute</span>
    </div>
    <div class="improvement-list" id="improvement-list">
        <!-- Wird per WebSocket aktualisiert -->
    </div>
</div>
```

---

### 4. Log-Dateien

**Zweck:** Persistente Historie aller Änderungen

#### Format: JSONL (eine Zeile pro Änderung)
```json
{"timestamp": "2025-01-10T14:30:22", "file": "routes/upload_csv.py", "action": "improved", "issues_fixed": 2, "tests_passed": true, "backup": "upload_csv_20250110_143022.py", "diff_preview": "...", "improvement_score": 85}
{"timestamp": "2025-01-10T12:15:10", "file": "frontend/index.html", "action": "improved", "issues_fixed": 1, "tests_passed": true, "backup": "index_20250110_121510.html", "diff_preview": "...", "improvement_score": 90}
{"timestamp": "2025-01-10T10:45:05", "file": "routes/workflow_api.py", "action": "rollback", "reason": "tests_failed", "backup": "workflow_api_20250110_104505.py", "test_errors": ["test_workflow_upload failed"]}
```

#### Datei-Struktur:
```
data/
  code_fixes_log/
    2025-01-10.jsonl
    2025-01-09.jsonl
    2025-01-08.jsonl
    ...
```

---

### 5. WebSocket (Live-Updates)

**Zweck:** Echtzeit-Benachrichtigungen ohne Seiten-Reload

```javascript
// Frontend: WebSocket-Client
const ws = new WebSocket('ws://localhost:8111/ws/ki-improvements');

ws.onmessage = (event) => {
    const improvement = JSON.parse(event.data);
    
    // Toast-Notification anzeigen
    showImprovementNotification(improvement);
    
    // Dashboard aktualisieren
    updateDashboard(improvement);
    
    // Sidebar-Widget aktualisieren
    updateSidebarWidget(improvement);
};

// Backend: WebSocket-Server
@router.websocket("/ws/ki-improvements")
async def websocket_improvements(websocket: WebSocket):
    await websocket.accept()
    
    # Sende Updates bei neuen Verbesserungen
    while True:
        new_improvement = await check_for_new_improvement()
        if new_improvement:
            await websocket.send_json(new_improvement)
        
        await asyncio.sleep(5)
```

---

## 🎨 UI-Design-Vorschläge

### Option 1: Minimalistisch (Empfohlen)
- **Toast-Notifications** (oben rechts, auto-close)
- **Sidebar-Widget** (klein, unaufdringlich)
- **Dashboard** (separate Seite, auf Wunsch)

### Option 2: Umfassend
- **Banner** (oben, bei wichtigen Änderungen)
- **Sidebar-Panel** (ausklappbar, detailliert)
- **Dashboard** (separate Seite, vollständig)

### Option 3: Hybrid (Beste Lösung)
- **Toast-Notifications** für sofortige Benachrichtigung
- **Sidebar-Widget** für schnellen Überblick
- **Dashboard** für detaillierte Ansicht
- **E-Mail** für wichtige Änderungen

---

## 📋 Benachrichtigungs-Einstellungen

### Konfiguration

```json
{
  "notifications": {
    "dashboard": {
      "enabled": true,
      "live_updates": true,
      "show_toast": true,
      "show_sidebar_widget": true
    },
    "email": {
      "enabled": true,
      "on_success": true,
      "on_failure": true,
      "on_rollback": true,
      "daily_summary": true,
      "recipients": ["developer@example.com"]
    },
    "log": {
      "enabled": true,
      "file": "data/code_fixes_log/{date}.jsonl",
      "retention_days": 30
    },
    "websocket": {
      "enabled": true,
      "reconnect_interval": 5
    }
  }
}
```

---

## 🔔 Benachrichtigungs-Prioritäten

### Kritisch (immer benachrichtigen)
- ❌ Rollback (Tests fehlgeschlagen)
- ❌ Kritische Fehler gefunden
- ❌ Software nicht mehr funktionsfähig

### Wichtig (standardmäßig benachrichtigen)
- ✅ Code-Verbesserung erfolgreich
- ⚠️ Warnungen gefunden
- 📊 Tages-Zusammenfassung

### Informativ (optional)
- 🔍 Code-Scan abgeschlossen
- 📈 Metriken-Update
- 🔄 Background-Job gestartet

---

## 📱 Beispiel-Implementierung

### Dashboard-Komponente

```html
<!-- frontend/admin/ki-improvements.html -->
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>KI-CodeChecker Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        .improvement-card {
            border-left: 4px solid #28a745;
            margin-bottom: 1rem;
        }
        .improvement-card.rollback {
            border-left-color: #dc3545;
        }
        .diff-preview {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1><i class="fas fa-robot"></i> KI-CodeChecker Dashboard</h1>
        
        <!-- Status-Karten -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5>Verbesserungen heute</h5>
                        <h2 id="improvements-today">0</h2>
                        <small>/ 5 (Limit)</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5>Erfolgreich</h5>
                        <h2 id="successful-count" class="text-success">0</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5>Fehlgeschlagen</h5>
                        <h2 id="failed-count" class="text-danger">0</h2>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Verbesserungs-Liste -->
        <div class="card">
            <div class="card-header">
                <h5>Letzte Verbesserungen</h5>
            </div>
            <div class="card-body">
                <div id="improvements-list">
                    <!-- Wird per WebSocket gefüllt -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket-Verbindung
        const ws = new WebSocket('ws://localhost:8111/ws/ki-improvements');
        
        ws.onmessage = (event) => {
            const improvement = JSON.parse(event.data);
            addImprovementToList(improvement);
            updateStats();
        };
        
        function addImprovementToList(improvement) {
            const list = document.getElementById('improvements-list');
            const card = document.createElement('div');
            card.className = `improvement-card card ${improvement.action === 'rollback' ? 'rollback' : ''}`;
            
            const statusIcon = improvement.action === 'improved' ? '✅' : '⚠️';
            const statusText = improvement.action === 'improved' ? 'Erfolgreich' : 'Rollback';
            
            card.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h6>${statusIcon} ${improvement.file}</h6>
                            <small class="text-muted">${new Date(improvement.timestamp).toLocaleString('de-DE')}</small>
                        </div>
                        <div>
                            <span class="badge bg-${improvement.action === 'improved' ? 'success' : 'danger'}">${statusText}</span>
                        </div>
                    </div>
                    <p class="mb-2">Issues behoben: ${improvement.issues_fixed || 0}</p>
                    ${improvement.diff ? `
                        <details>
                            <summary>Diff anzeigen</summary>
                            <pre class="diff-preview">${improvement.diff}</pre>
                        </details>
                    ` : ''}
                    ${improvement.backup ? `
                        <small>Backup: ${improvement.backup}</small>
                    ` : ''}
                </div>
            `;
            
            list.insertBefore(card, list.firstChild);
        }
        
        function updateStats() {
            // Statistiken aktualisieren
            fetch('/api/ki-improvements/stats')
                .then(r => r.json())
                .then(stats => {
                    document.getElementById('improvements-today').textContent = stats.improvements_today;
                    document.getElementById('successful-count').textContent = stats.successful_count;
                    document.getElementById('failed-count').textContent = stats.failed_count;
                });
        }
        
        // Initial laden
        fetch('/api/ki-improvements/recent?limit=10')
            .then(r => r.json())
            .then(improvements => {
                improvements.forEach(addImprovementToList);
                updateStats();
            });
    </script>
</body>
</html>
```

---

## 🎯 Empfohlene Lösung

### Hybrid-Ansatz (Beste Lösung)

1. **Toast-Notifications** (sofortige Benachrichtigung)
   - Erscheint oben rechts
   - Auto-close nach 10 Sekunden
   - Klickbar für Details

2. **Sidebar-Widget** (schneller Überblick)
   - Badge mit Anzahl
   - Liste der letzten 3 Verbesserungen
   - Klick öffnet Dashboard

3. **Dashboard** (detaillierte Ansicht)
   - Separate Seite (`/admin/ki-improvements`)
   - Vollständige Historie
   - Filter & Suche
   - Diff-Vorschau

4. **E-Mail** (wichtige Änderungen)
   - Bei Rollback (immer)
   - Tages-Zusammenfassung (optional)
   - Wichtige Verbesserungen (optional)

5. **Log-Dateien** (persistente Historie)
   - JSONL-Format
   - 30 Tage Retention
   - Für Analyse und Audit

---

## 📊 Benachrichtigungs-Flow

```
KI verbessert Code
    ↓
Backup erstellen
    ↓
Änderung anwenden
    ↓
Tests ausführen
    ↓
┌─────────────────┬──────────────────┐
│ Tests OK        │ Tests fehlgeschlagen │
│                 │                    │
│ ✅ Erfolg       │ ⚠️ Rollback        │
│                 │                    │
│ Benachrichtigungen:                  │
│ - Toast ✅      │ - Toast ⚠️          │
│ - Dashboard ✅  │ - Dashboard ⚠️    │
│ - E-Mail ✅     │ - E-Mail ⚠️        │
│ - Log ✅        │ - Log ⚠️           │
└─────────────────┴──────────────────┘
```

---

## 🔧 Implementierungs-Priorität

### Phase 1 (Sofort)
- [ ] Log-Dateien (einfach, wichtig)
- [ ] Dashboard (Grundversion)
- [ ] Toast-Notifications (einfach)

### Phase 2 (Kurzfristig)
- [ ] E-Mail-Benachrichtigungen
- [ ] WebSocket (Live-Updates)
- [ ] Sidebar-Widget

### Phase 3 (Mittelfristig)
- [ ] Erweiterte Dashboard-Features
- [ ] Filter & Suche
- [ ] Metriken & Trends

---

**Erstellt:** 2025-01-10  
**Status:** 📋 KONZEPT  
**Nächster Schritt:** Implementierung starten

