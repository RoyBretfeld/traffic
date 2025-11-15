# Schutz der Original-Tourenpläne

## Problem

Die Original-Tourenpläne im Ordner `tourplaene`/`Tourenpläne` sind die Basis des gesamten Systems. Wenn diese Dateien verändert werden:

- Excel und Text-Editoren interpretieren sie unterschiedlich
- Die Adress-Erkennung wird inkonsistent
- Änderungen werden ständig überschrieben
- Die Grundlage für alle Verarbeitung geht verloren

## Lösung: Read-Only Schutz

### 1. Automatischer Schutz

Führe aus, um alle CSV-Dateien im Tourenpläne-Ordner Read-Only zu setzen:

```bash
python scripts/protect_tourplaene_originals.py
```

Dieses Script:
- Findet alle `tourplaene`/`Tourenpläne`-Verzeichnisse
- Setzt alle CSV-Dateien auf Read-Only
- Verhindert, dass Excel/Editoren die Dateien speichern können

### 2. Geschützte Verzeichnisse

Die folgenden Verzeichnisse sind **READ-ONLY** (Originale):

- `./tourplaene/`
- `./Tourenpläne/`
- `./Tourplaene/`

**NICHT** in diesen Verzeichnissen arbeiten!

### 3. Schreibbare Verzeichnisse für Verarbeitung

Alle Änderungen müssen in diesen Verzeichnissen gemacht werden:

- `./data/staging/` - Staging für UTF-8-Kopien
- `./data/temp/` - Temporäre Verarbeitung
- `./data/tmp/` - Weitere temporäre Dateien

### 4. Code-Integration

Das Modul `fs/protected_fs.py` bietet geschützte Filesystem-Operationen:

```python
from fs.protected_fs import protected_write, protected_save_csv, is_protected_path

# Automatische Umleitung zu staging
safe_path = protected_save_csv(Path("./tourplaene/test.csv"), df)
# Wird automatisch nach ./data/staging/test.csv umgeleitet

# Prüfung
if is_protected_path(some_path):
    print("Warnung: Geschütztes Verzeichnis!")
```

### 5. Workflow

**RICHTIG:**
1. Original-CSV lesen aus `tourplaene/`
2. Verarbeitung in `data/staging/` oder `data/temp/`
3. Ergebnisse in `data/staging/` speichern
4. Original bleibt unverändert

**FALSCH:**
1. ❌ Original-CSV direkt öffnen und speichern
2. ❌ Änderungen in `tourplaene/` machen
3. ❌ CSV-Dateien im Original-Ordner überschreiben

### 6. Excel/Editor-Verhalten

Wenn Excel oder ein Editor eine Read-Only-Datei öffnet:
- Datei kann gelesen werden
- Änderungen können nicht gespeichert werden
- Excel zeigt Warnung: "Die Datei ist schreibgeschützt"
- Benutzer muss "Speichern unter..." verwenden → sollte in `data/temp/` speichern

### 7. Backup-Strategie

Vor größeren Änderungen:
1. Backup-Ordner erstellen: `data/backup/Tourenpläne_YYYYMMDD/`
2. Originale dorthin kopieren
3. In Backup-Ordner arbeiten (nicht im Original!)

### 8. Integritätsprüfung

Das System prüft automatisch vor jedem Ingest:

```python
from tools.orig_integrity import verify

problems = verify()
if problems:
    print("WARNUNG: Originale wurden verändert!")
```

### 9. Manuelle Wiederherstellung

Falls doch etwas schief geht:

1. Read-Only entfernen (nur für Reparatur!):
   ```powershell
   # PowerShell
   Get-ChildItem ".\tourplaene\*.csv" | ForEach-Object {
       $_.IsReadOnly = $false
   }
   ```

2. Originale aus Backup wiederherstellen

3. Schutz wieder aktivieren:
   ```bash
   python scripts/protect_tourplaene_originals.py
   ```

## Zusammenfassung

- ✅ **Originale sind Read-Only**
- ✅ **Alle Änderungen in `data/staging/` oder `data/temp/`**
- ✅ **Automatische Umleitung bei Schreibversuchen**
- ✅ **Integritätsprüfung vor Verarbeitung**
- ✅ **Backup-Strategie für größere Änderungen**

**GOLDENE REGEL:** Die Originale im `tourplaene`-Ordner werden **NIEMALS** verändert!

