# Phase 2 Schema Migration - Anleitung

**Erstellt:** 2025-11-09  
**Zweck:** Schritt-für-Schritt Anleitung zur Aktivierung des Phase 2 Schemas

---

## 📋 Übersicht

Das Phase 2 Schema fügt folgende Tabellen hinzu:
- `stats_monthly` - Monatliche Statistiken
- `routes` - Optimierte Routen
- `route_legs` - Einzelne Route-Segmente
- `osrm_cache` - Route-Geometrie-Caching

---

## ✅ Voraussetzungen

1. ✅ Migration-Script vorhanden: `scripts/migrate_schema_phase2.py`
2. ✅ Tests vorhanden: `tests/test_phase2_schema.py`
3. ✅ Backup-Funktionalität vorhanden

---

## 🔍 Schritt 1: Prüfen welche Tabellen bereits existieren

```bash
python scripts/migrate_schema_phase2.py --check
```

**Erwartete Ausgabe:**
```
🔍 Prüfe existierende Tabellen...
  ❌ stats_monthly
  ❌ routes
  ❌ route_legs
  ❌ osrm_cache
```

---

## 🔍 Schritt 2: Dry-Run (Test ohne Änderungen)

```bash
python scripts/migrate_schema_phase2.py --dry-run
```

**Erwartete Ausgabe:**
```
🔍 DRY-RUN: Würde folgende Tabellen erstellen:
  - stats_monthly
  - routes
  - route_legs
  - osrm_cache
✅ Dry-Run erfolgreich. Keine Änderungen vorgenommen.
```

---

## 📦 Schritt 3: Backup erstellen (automatisch)

Das Migration-Script erstellt automatisch ein Backup vor der Migration:

```bash
python scripts/migrate_schema_phase2.py
```

**Erwartete Ausgabe:**
```
📦 Erstelle Backup vor Migration...
✅ Backup erstellt: pre_phase2_migration_20251109_143022.db (2.45 MB)
🔄 Führe Migration durch...
✅ Validiere Migration...
✅ Migration erfolgreich!
   Erstellt: 4 Tabellen, 8 Indizes
   Backup: pre_phase2_migration_20251109_143022.db
```

**Backup-Speicherort:** `data/backups/migrations/`

---

## ✅ Schritt 4: Migration validieren

```bash
# Tests ausführen
pytest tests/test_phase2_schema.py -v
```

**Erwartete Ausgabe:**
```
tests/test_phase2_schema.py::test_phase2_tables_exist PASSED
tests/test_phase2_schema.py::test_stats_monthly_structure PASSED
tests/test_phase2_schema.py::test_routes_structure PASSED
tests/test_phase2_schema.py::test_route_legs_structure PASSED
tests/test_phase2_schema.py::test_osrm_cache_structure PASSED
tests/test_phase2_schema.py::test_indexes_exist PASSED
tests/test_phase2_schema.py::test_foreign_key_constraint PASSED
tests/test_phase2_schema.py::test_insert_sample_data PASSED
tests/test_phase2_schema.py::test_unique_constraints PASSED
tests/test_phase2_schema.py::test_cascade_delete PASSED
```

---

## ⚙️ Schritt 5: Feature-Flag aktivieren

Nach erfolgreicher Migration und Tests:

1. Öffne `config/app.yaml`
2. Ändere:
   ```yaml
   new_schema_enabled: false  # Phase 2: Neue Tabellen
   ```
   zu:
   ```yaml
   new_schema_enabled: true  # Phase 2: Neue Tabellen
   ```

3. Server neu starten

---

## 🔄 Rollback (falls nötig)

Falls die Migration Probleme verursacht:

```bash
python scripts/migrate_schema_phase2.py --rollback pre_phase2_migration_20251109_143022.db
```

**Erwartete Ausgabe:**
```
🔄 Stelle Datenbank aus Backup wieder her: pre_phase2_migration_20251109_143022.db
✅ Rollback erfolgreich!
```

**Wichtig:** Rollback löscht alle Phase 2 Tabellen und deren Daten!

---

## 📊 Migration-Script Optionen

```bash
# Prüfen welche Tabellen existieren
python scripts/migrate_schema_phase2.py --check

# Dry-Run (nur prüfen, nichts ändern)
python scripts/migrate_schema_phase2.py --dry-run

# Migration durchführen
python scripts/migrate_schema_phase2.py

# Rollback aus Backup
python scripts/migrate_schema_phase2.py --rollback <backup_filename>
```

---

## ⚠️ Wichtige Hinweise

1. **Backup:** Das Script erstellt automatisch ein Backup vor der Migration
2. **Idempotent:** Die Migration kann mehrfach ausgeführt werden (verwendet `CREATE TABLE IF NOT EXISTS`)
3. **Foreign Keys:** Foreign Keys müssen aktiviert sein (wird automatisch durch `db/core.py` gesetzt)
4. **Tests:** Führe immer Tests nach der Migration aus
5. **Feature-Flag:** Aktivierung des Feature-Flags ist optional (Schema wird auch ohne aktiviert)

---

## 🐛 Troubleshooting

### Problem: "Backup fehlgeschlagen"
**Lösung:** Prüfe ob Datenbank-Datei existiert und nicht von anderem Prozess gesperrt ist

### Problem: "Foreign Keys sind nicht aktiviert"
**Lösung:** Prüfe `db/core.py` - Foreign Keys sollten automatisch aktiviert werden

### Problem: "Tabelle bereits existiert"
**Lösung:** Normal - Migration ist idempotent. Prüfe mit `--check` ob alle Tabellen existieren.

### Problem: "Migration unvollständig"
**Lösung:** Prüfe Logs, führe Rollback durch und versuche erneut

---

## 📝 Checkliste

Vor Migration:
- [ ] Backup-Verzeichnis existiert (`data/backups/migrations/`)
- [ ] Datenbank ist nicht von anderem Prozess gesperrt
- [ ] Dry-Run erfolgreich

Nach Migration:
- [ ] Alle Tests bestehen (`pytest tests/test_phase2_schema.py`)
- [ ] Tabellen existieren (prüfen mit `--check`)
- [ ] Feature-Flag aktiviert (optional)
- [ ] Server neu gestartet (wenn Feature-Flag aktiviert)

---

**Stand:** 2025-11-09  
**Nächste Aktualisierung:** Nach erfolgreicher Migration in Produktion

