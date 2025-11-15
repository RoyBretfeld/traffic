# 📦 Cloud-Synchronisation Liste

**Zweck:** Diese Dateien sollten mit Cloud synchronisiert werden  
**Cloud-Pfad:** `G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0`

---

## 🚀 **Schnellstart für morgen:**

### 1. Dateien synchronisieren:
```powershell
# Aus Projekt-Root ausführen:
powershell -ExecutionPolicy Bypass -File scripts\sync_to_cloud.ps1
```

### 2. Dokument öffnen:
- **START HIER:** `docs\START_HIER_MORGEN.md` ⭐
- **Status:** `docs\STATUS_HEUTE_2025.md`

---

## 📁 **Dateien für Cloud-Sync:**

### ✅ Backend (Code):
1. `routes\workflow_api.py`
   - Automatische Sektor-Planung für W-Touren
   - Automatisches PIRNA-Clustering
   - BAR-Flag-Erhaltung

2. `routes\engine_api.py`
   - Touren Engine API
   - Endpoints für Sektor-Planung & PIRNA-Clustering

3. `services\sector_planner.py`
   - Sektor-Planung Logik (N/O/S/W)
   - Zeitbox 07:00 → 09:00

4. `services\pirna_clusterer.py`
   - PIRNA-Clustering Logik
   - Parameter: 15 Stopps, 120 Min

### ✅ Frontend (Code):
5. `frontend\index.html`
   - Buttons entfernt (Sektor-Planung, PIRNA-Clustering)
   - BAR-Flag-Erhaltung in Sub-Routen
   - KI-Begründung bereinigt (nur reasoning)

### ✅ Dokumentation (Neu):
6. `docs\STATUS_HEUTE_2025.md` ⭐ **WICHTIG**
   - Vollständiger Status
   - Was wurde heute gemacht?
   - Welche Dateien wurden geändert?

7. `docs\START_HIER_MORGEN.md` ⭐ **START HIER**
   - Schnellstart-Checkliste
   - Wichtigste Links
   - Cloud-Sync Anweisungen

8. `docs\CLOUD_SYNC_LISTE.md` (dieses Dokument)
   - Liste aller zu synchronisierenden Dateien

### ✅ Skripte (Neu):
9. `scripts\sync_to_cloud.ps1`
   - Synchronisiert Projekt → Cloud

10. `scripts\sync_from_cloud.ps1`
    - Synchronisiert Cloud → Projekt (rückwärts)

---

## 🔄 **Sync-Prozess:**

### Projekt → Cloud (normal):
```powershell
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
powershell -ExecutionPolicy Bypass -File scripts\sync_to_cloud.ps1
```

### Cloud → Projekt (rückwärts):
```powershell
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
powershell -ExecutionPolicy Bypass -File scripts\sync_from_cloud.ps1
```

---

## 📋 **Manuelle Sync (falls Skript nicht funktioniert):**

### Einzelne Dateien kopieren:
1. Öffne: `G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0`
2. Kopiere manuell die Dateien aus der Liste oben
3. Achte auf Ordnerstruktur:
   - `routes\` → `routes\`
   - `services\` → `services\`
   - `frontend\` → `frontend\`
   - `docs\` → `docs\`
   - `scripts\` → `scripts\`

---

## ✅ **Verifikation nach Sync:**

### Prüfen ob Dateien existieren:
```powershell
# Im Cloud-Ordner:
cd "G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"

# Prüfe wichtige Dateien:
Test-Path "docs\START_HIER_MORGEN.md"
Test-Path "docs\STATUS_HEUTE_2025.md"
Test-Path "routes\workflow_api.py"
Test-Path "frontend\index.html"
```

---

## 🎯 **Für morgen:**

1. **Cloud-Ordner öffnen:**
   - `G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0`

2. **Dokument öffnen:**
   - `docs\START_HIER_MORGEN.md` ⭐

3. **Weiter zu:**
   - `docs\STATUS_HEUTE_2025.md` für Details

4. **Server starten:**
   - `python start_server.py`
   - Frontend: http://127.0.0.1:8111/ui/

---

**Erstellt:** Heute  
**Version:** 1.0

