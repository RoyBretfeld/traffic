# Troubleshooting: 500 Internal Server Error bei Tour-Optimierung

## Problem

**Fehler:** `500 Internal Server Error` bei `/api/tour/optimize`

**Symptome:**
- Alle Touren schlagen fehl mit "API-Fehler bei allen X Tour(en)"
- Konsole zeigt: `POST http://127.0.0.1:8111/api/tour/optimize 500 (Internal Server Error)`
- Trace-IDs werden generiert, aber die Optimierung schlägt fehl

---

## Ursachen

### 1. OSRM nicht erreichbar (Häufigste Ursache)

**Symptom:** `/health/osrm` gibt `503 Service Unavailable` zurück

**Ursache:** Docker Desktop läuft nicht oder OSRM-Container ist nicht gestartet

**Lösung:**
```bash
# 1. Docker Desktop starten
# 2. OSRM-Container starten
docker-compose up -d osrm

# 3. Status prüfen
docker ps | grep osrm
curl http://127.0.0.1:5000/nearest/v1/driving/13.7373,51.0504?number=1
```

### 2. Unerwarteter Fehler im Code

**Symptom:** Fehler tritt auf, bevor Fallback greift

**Lösung:** 
- Server-Logs prüfen: `logs/*.log`
- Trace-ID aus Konsole verwenden, um Fehler zu finden
- Server neu starten, damit Code-Änderungen wirksam werden

### 3. Datenbank-Fehler

**Symptom:** SQLite-Fehler in Logs

**Lösung:**
- Datenbank-Integrität prüfen: `PRAGMA integrity_check`
- Backup wiederherstellen falls nötig

---

## Debugging

### 1. Server-Logs prüfen

```bash
# Windows PowerShell
Get-Content logs\*.log -Tail 50 | Select-String -Pattern "TOUR-OPTIMIZE|error|Error|Exception"
```

### 2. Health-Checks prüfen

```bash
# OSRM-Status
curl http://127.0.0.1:8111/health/osrm

# Metrics (zeigt 5xx-Fehler)
curl http://127.0.0.1:8111/metrics/simple
```

### 3. Trace-ID verwenden

Die Trace-ID wird in der Konsole angezeigt. Suche in den Logs nach dieser ID:

```bash
Get-Content logs\*.log | Select-String -Pattern "b6734bb0"
```

---

## Fallback-Verhalten

Der Code sollte **immer** einen Fallback verwenden:

1. **OSRM** (wenn verfügbar)
2. **Nearest Neighbor** (lokale Haversine-Matrix)
3. **Identität** (als letzter Fallback)

**WICHTIG:** Der Endpoint gibt **NIE** 500 zurück, sondern immer 200 mit `success: false` bei Fehlern.

---

## Schnell-Fix

```bash
# 1. Docker Desktop starten
# 2. OSRM starten
docker-compose up -d osrm

# 3. Server neu starten (damit Code-Änderungen wirksam werden)
# Stoppe laufenden Server (Ctrl+C) und starte neu:
python start_server.py
```

---

**Letzte Aktualisierung:** 2025-11-13

