# ☁️ Cloud-Integration & Google Drive Synchronisierung

## 📋 Übersicht

Die FAMO TrafficApp unterstützt automatische Synchronisierung zwischen dem lokalen ZIP-Archiv und Google Drive:

- **Quelle (Lokal):** `C:\Workflow\TrafficApp\ZIP`
- **Ziel (Google Drive):** `Meine Ablage\FAMO_TrafficApp_Archives\ZIP`

## 🚀 Schnellstart

### 1. Google Drive Mount-Point konfigurieren

**Option A: Umgebungsvariable (empfohlen)**
```powershell
# In PowerShell vor dem Server-Start:
$env:GOOGLE_DRIVE_PATH = "C:\Users\Bretfeld\Meine Ablage"

# Server starten
python start_server.py --port 8111
```

**Option B: API nach Server-Start**
```bash
POST http://127.0.0.1:8111/api/configure-drive?mount_point=C:/Users/Bretfeld/Meine%20Ablage
```

### 2. ZIP-Archiv synchronisieren

```bash
POST http://127.0.0.1:8111/api/sync-to-drive
```

**Response:**
```json
{
  "success": true,
  "method": "robocopy",
  "file_count": 36,
  "total_size_mb": 0.5,
  "drive_path": "C:\\Users\\Bretfeld\\Meine Ablage\\FAMO_TrafficApp_Archives\\ZIP"
}
```

### 3. Status anzeigen

```bash
GET http://127.0.0.1:8111/api/archive-status
```

## 📁 Archivierter Inhalt

### Was wird ins ZIP gepacked?

Alle relevanten Parsing-Dateien mit **Timestamp-Präfix** (YYYYMMDD_HHMMSS):

| Dateitype | Format | Inhalt |
|---|---|---|
| **CSV-Dateien** | `YYYYMMDD_HHMMSS_tourplan.csv` | Originale Tour-Pläne |
| **Geparste Touren** | `YYYYMMDD_HHMMSS_parsed_tours.json` | Strukturierte Tour-Daten |
| **Geocoding** | `YYYYMMDD_HHMMSS_geocoding_results.json` | Koordinaten & Resultate |
| **Processing-Log** | `YYYYMMDD_HHMMSS_processing_log.txt` | Statistiken & Verarbeitungsinfo |

### Beispiel-Struktur

```
FAMO_TrafficApp_Archives/
└── ZIP/
    ├── 20251022_081032_Tourenplan 01.10.2025.csv
    ├── 20251022_081032_Tourenplan 02.10.2025.csv
    ├── 20251022_081032_parsed_tours.json
    ├── 20251022_081032_geocoding_results.json
    └── 20251022_081032_processing_log.txt
```

## ⚙️ Automatisches Syncing

Beim Server-Start mit gesetzter `GOOGLE_DRIVE_PATH`:

```
[STARTUP] Google Drive konfiguriert: C:\Users\Bretfeld\Meine Ablage
[STARTUP] Synchronisiere ZIP zu Google Drive...
[STARTUP] ✅ Drive-Sync erfolgreich: 36 Dateien, 0.50 MB
```

## 🔄 Workflow

```
CSV-Upload (data/staging/)
    ↓
CSV Parsing → ZIP/YYYYMMDD_*.csv
    ↓
Tour-Parsing → ZIP/YYYYMMDD_parsed_tours.json
    ↓
Geocoding → ZIP/YYYYMMDD_geocoding_results.json
    ↓
Auto-Sync → Google Drive
```

## 📊 API-Referenz

### Archive Status
```
GET /api/archive-status
```
Zeigt ZIP-Verzeichnis Status mit Dateiliste.

### Synchronisieren
```
POST /api/sync-to-drive
```
Synchronisiert ZIP zu Google Drive.

### Drive konfigurieren
```
POST /api/configure-drive?mount_point=<PFAD>
```
Setzt den Google Drive Mount-Point.

### Temp-Status
```
GET /api/temp-status
```
Zeigt temporäre Dateien Status.

## 🛡️ Fehlerbehandlung

| Fehler | Lösung |
|---|---|
| `Mount-Point nicht konfiguriert` | GOOGLE_DRIVE_PATH setzen |
| `Pfad existiert nicht` | Drive-Pfad prüfen |
| `Permission denied` | Drive-Zugriff prüfen |
| `Encoding error` | Ignorierbar (robocopy-Warnung) |

## 📝 Wartung

### Alte Archive löschen

Temporary Dateien werden automatisch nach **40 Tagen** gelöscht:

```
GET /api/temp-status  # Status anzeigen
POST /api/temp-cleanup  # Manuell löschen
```

### Drive bereinigen

Sync mit `/MIR` Flag (Mirror) - löscht alte Dateien auf Drive:

```bash
POST /api/sync-to-drive  # Sync mit Cleanup
```

## 🔐 Sicherheit

- ✅ UTF-8 Only (keine Encoding-Probleme)
- ✅ Pfad-Validierung (kein Directory-Traversal)
- ✅ Automatic Backups (ZIP = Archiv)
- ✅ Multi-threaded (robocopy mit 8 Threads)
