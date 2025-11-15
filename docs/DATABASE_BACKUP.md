# Datenbank-Backup-System

## Übersicht

Automatisches tägliches Backup der `traffic.db` Datenbank um **16:00 Uhr (4 PM)**.

Die Backups werden in `data/backups/` gespeichert und enthalten alle Geocoding-Daten, Synonyme und andere wichtige Informationen.

## Speicherorte

- **Datenbank**: `data/traffic.db`
- **Backups**: `data/backups/`
- **Backup-Format**: `traffic_backup_YYYYMMDD_HHMMSS.db`

## Automatisches Backup einrichten

### Windows (Task Scheduler)

**Option 1: PowerShell-Script (Empfohlen)**
```powershell
# Als Administrator ausführen
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
.\scripts\schedule_backup_windows.ps1
```

**Option 2: Batch-Script**
```batch
REM Als Administrator ausführen
cd "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0"
scripts\schedule_backup_windows.bat
```

**Option 3: Manuell im Task Scheduler**
1. Öffne "Aufgabenplanung" (Task Scheduler)
2. "Einfache Aufgabe erstellen"
3. Name: `FAMO_TrafficApp_DB_Backup`
4. Trigger: **Täglich um 16:00 Uhr**
5. Aktion: Programm starten
   - Programm: `python`
   - Argumente: `"E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0\scripts\db_backup.py"`
6. Abschließen

### Linux/Mac (Cron)

```bash
# Crontab bearbeiten
crontab -e

# Zeile hinzufügen (täglich um 16:00 Uhr):
0 16 * * * cd /pfad/zum/projekt && python scripts/db_backup.py >> logs/backup.log 2>&1
```

## Manuelles Backup

### Kommandozeile

```bash
# Backup erstellen
python scripts/db_backup.py

# Backups auflisten
python scripts/db_backup.py --list

# Backup wiederherstellen
python scripts/db_backup.py --restore traffic_backup_20250115_160000.db
```

### API-Endpunkt

```bash
# Backup erstellen
POST /api/backup/create

# Backups auflisten
GET /api/backup/list

# Backup wiederherstellen
POST /api/backup/restore?backup_filename=traffic_backup_20250115_160000.db

# Alte Backups bereinigen
POST /api/backup/cleanup
```

## Backup-Retention

- **Aufbewahrungszeit**: 30 Tage
- **Automatische Bereinigung**: Alte Backups (> 30 Tage) werden automatisch gelöscht
- **Manuelle Bereinigung**: `python scripts/db_backup.py` oder API `/api/backup/cleanup`

## Backup-Wiederherstellung

### Sicherheitshinweise

⚠️ **WICHTIG**: Vor jeder Wiederherstellung wird automatisch ein Safety-Backup der aktuellen DB erstellt!

### Schritt-für-Schritt

1. **Backup auflisten**:
   ```bash
   python scripts/db_backup.py --list
   ```

2. **Backup wiederherstellen**:
   ```bash
   python scripts/db_backup.py --restore traffic_backup_20250115_160000.db
   ```

3. **Oder über API**:
   ```bash
   curl -X POST "http://localhost:8111/api/backup/restore?backup_filename=traffic_backup_20250115_160000.db"
   ```

## Technische Details

### Backup-Methode

- **SQLite Native Backup**: Verwendet `sqlite3.backup()` für konsistente Backups
- **WAL-Mode kompatibel**: Funktioniert auch bei aktivem WAL-Journal-Mode
- **Sichere Kopie**: Auch während laufender Transaktionen möglich

### Backup-Format

```
traffic_backup_YYYYMMDD_HHMMSS.db

Beispiele:
- traffic_backup_20250115_160000.db  (15.01.2025, 16:00:00)
- traffic_backup_20250115_160001.db  (15.01.2025, 16:00:01)
```

### Größe

Typische Backup-Größe: ~10-50 MB (abhängig von Anzahl der geocodierten Adressen)

## Monitoring

### Log-Dateien

Backups werden in der Konsole/Log geloggt:
```
[BACKUP] Starte Backup um 2025-01-15 16:00:00...
[BACKUP] Backup erfolgreich erstellt: traffic_backup_20250115_160000.db (15.23 MB)
[BACKUP CLEANUP] 3 alte Backups gelöscht (> 30 Tage)
```

### Fehlerbehandlung

Bei Fehlern wird eine Fehlermeldung ausgegeben:
```
[BACKUP ERROR] Backup-Fehler: Datenbank nicht gefunden
```

## Notfall-Wiederherstellung

Falls die Datenbank beschädigt ist:

1. **Neuestes Backup finden**:
   ```bash
   python scripts/db_backup.py --list
   ```

2. **Backup wiederherstellen**:
   ```bash
   python scripts/db_backup.py --restore traffic_backup_YYYYMMDD_HHMMSS.db
   ```

3. **Server neu starten**

## Integration

Das Backup-System ist automatisch in die App integriert:

- **Script**: `scripts/db_backup.py`
- **API**: `routes/backup_api.py`
- **Scheduler-Scripts**: 
  - Windows: `scripts/schedule_backup_windows.ps1` (PowerShell)
  - Windows: `scripts/schedule_backup_windows.bat` (Batch)

## Wartung

### Regelmäßige Prüfung

- Überprüfe monatlich, ob Backups erstellt werden
- Prüfe Backup-Größe (sollte konsistent sein)
- Teste Wiederherstellung einmal pro Quartal

### Troubleshooting

**Problem**: Task läuft nicht
- Prüfe Task Scheduler: `Get-ScheduledTask -TaskName "FAMO_TrafficApp_DB_Backup"`
- Prüfe Python-Pfad im Task
- Prüfe Logs: `logs/backup.log` (falls konfiguriert)

**Problem**: Backup zu groß/zu klein
- Prüfe Datenbank-Größe: `data/traffic.db`
- Prüfe ob WAL-Dateien vorhanden sind
- Prüfe ob VACUUM nötig ist

---

**Erstellt**: 2025-01-XX
**Autor**: AI Assistant (Cursor)

