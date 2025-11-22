# Aufräumplan - FAMO TrafficApp 3.0
**Datum:** 2025-11-20  
**Ziel:** Alte, nicht gebrauchte Dateien identifizieren und organisieren

---

## 📊 Analyse-Ergebnis

### 🔴 SOFORT VERSCHIEBEN/LÖSCHEN

#### 1. **Extrahierte Backup-Dateien** (417 Dateien!)
- **Pfad:** `backups/extracted_backup/`
- **Größe:** ~344 Python-Dateien, 29 JSON, 14 PS1, etc.
- **Aktion:** **LÖSCHEN** (sind bereits in ZIP-Archiven gesichert)
- **Grund:** Duplikate, veraltet, nehmen viel Platz ein

#### 2. **Temporäre Extrakt-Verzeichnisse**
- **Pfad:** `temp_zip_extract/` (30 Dateien)
- **Aktion:** **LÖSCHEN**
- **Grund:** Temporäre Dateien, nicht mehr benötigt

#### 3. **Alte Audit-Verzeichnisse**
- **Pfad:** `audit_sub_routen_2025-11-15/` (7 Dateien)
- **Pfad:** `audit_sub_routen_2025-11-15.zip`
- **Aktion:** **VERSCHIEBEN** nach `ZIP/archive/`
- **Grund:** Alte Audits, sollten archiviert werden

#### 4. **Root-Level Test-Dateien** (sollten in `tests/` sein)
- `test_w07_splitting.py`
- `test_split_direct.py`
- `comprehensive_test_suite.py`
- `check_syntax.py`
- **Aktion:** **VERSCHIEBEN** nach `tests/` oder `scripts/test/`
- **Grund:** Bessere Organisation

#### 5. **Deprecated Admin-Dateien**
- `admin/address_admin_app_deprecated.py` (nur Error-Raise)
- `admin/address_admin_app_fixed.py` (wenn nicht mehr verwendet)
- **Aktion:** **LÖSCHEN** (deprecated) oder **VERSCHIEBEN** nach `archive/`
- **Grund:** Explizit als deprecated markiert

#### 6. **Alte ZIP-Archive im Root**
- `archive_old_audits_20251115_155826.zip`
- **Aktion:** **VERSCHIEBEN** nach `ZIP/archive/`
- **Grund:** Sollte in Archiv-Ordner

---

### 🟡 VERSCHIEBEN NACH `archive/` ODER `docs/archive/`

#### 7. **Test-HTML-Dateien im Frontend** (wenn nicht mehr verwendet)
- `frontend/ai-test.html`
- `frontend/test-dashboard.html`
- `frontend/tourplan-visual-test.html`
- `frontend/tourplan-management.html`
- `frontend/multi-tour-generator.html`
- **Aktion:** **PRÜFEN** ob noch verwendet, dann **VERSCHIEBEN** nach `frontend/archive/` oder löschen
- **Grund:** Test-Dateien, sollten nicht in Produktion sein

#### 8. **Alte Start-Scripts** (wenn Duplikate)
- `START_SERVER_ROBUST.bat` (wenn `tools/scripts/start_robust.bat` existiert)
- `START_SERVER_ROBUST.ps1` (wenn `tools/scripts/start_robust.ps1` existiert)
- `START_SERVER_WITH_LOGS.ps1`
- `START_SERVER.ps1`
- `start_server_venv.ps1`
- **Aktion:** **PRÜFEN** ob Duplikate, dann **LÖSCHEN** oder **VERSCHIEBEN**
- **Grund:** Mehrere Start-Scripts können verwirrend sein

#### 9. **Alte Backup-Dateien** (wenn zu alt)
- `backups/backup_vor_umbau_20251108_141746.zip` (vom 08.11.)
- `backups/backup_vollstaendig_2025-11-18_18-36-42.zip` (vom 18.11.)
- `backups/backup_vollstaendig_2025-11-18_19-02-46.zip` (vom 18.11.)
- `backups/Sub-Routen_Generator_20251116_141852.zip`
- `backups/Sub-Routen_Generator_20251116_141906.zip`
- **Aktion:** **VERSCHIEBEN** nach `ZIP/archive/` (wenn älter als 7 Tage)
- **Grund:** Alte Backups sollten archiviert werden

#### 10. **DB-Repair-Backups** (wenn zu alt)
- `backups/db_repairs/` (6 DB-Dateien)
- **Aktion:** **LÖSCHEN** (wenn älter als 7 Tage) oder **VERSCHIEBEN**
- **Grund:** Temporäre Repair-Backups, nicht langfristig nötig

---

### 🟢 PRÜFEN & ORGANISIEREN

#### 11. **Viele Test-Dateien** (299 Test-Dateien gefunden)
- **Pfad:** `tests/` (149 Dateien)
- **Pfad:** `scripts/test/` (viele Test-Dateien)
- **Aktion:** **PRÜFEN** ob alle noch relevant, dann **ORGANISIEREN**
- **Grund:** Viele Tests können veraltet sein

#### 12. **Alte Konfigurations-Dateien**
- `config/address_analysis_*.json` (vom 07.10.)
- `config/mapping_suggestions_*.json` (vom 07.10.)
- **Aktion:** **VERSCHIEBEN** nach `config/archive/` (wenn nicht mehr verwendet)
- **Grund:** Alte Analysen, sollten archiviert werden

#### 13. **Alte Audit-Verzeichnisse**
- `audit/csv_parsing/` (11 Dateien)
- **Aktion:** **PRÜFEN** ob noch relevant, dann **VERSCHIEBEN** nach `ZIP/archive/`
- **Grund:** Alte Audits sollten archiviert werden

#### 14. **Temporäre Verzeichnisse**
- `temp_tour/` (1 CSV)
- **Aktion:** **LÖSCHEN** (wenn temporär)
- **Grund:** Temporäre Dateien

---

## 📋 Vorgeschlagene Aktionen

### Phase 1: Sofort löschen (sicher)
1. ✅ `backups/extracted_backup/` → **LÖSCHEN** (417 Dateien)
2. ✅ `temp_zip_extract/` → **LÖSCHEN** (30 Dateien)
3. ✅ `admin/address_admin_app_deprecated.py` → **LÖSCHEN** (nur Error-Raise)

### Phase 2: Verschieben nach Archive
4. ✅ `audit_sub_routen_2025-11-15/` → `ZIP/archive/`
5. ✅ `audit_sub_routen_2025-11-15.zip` → `ZIP/archive/`
6. ✅ `archive_old_audits_20251115_155826.zip` → `ZIP/archive/`
7. ✅ Root-Level Test-Dateien → `tests/` oder `scripts/test/`

### Phase 3: Prüfen & Organisieren
8. ⚠️ Test-HTML-Dateien prüfen → `frontend/archive/` oder löschen
9. ⚠️ Alte Backup-Dateien prüfen → `ZIP/archive/` (wenn älter als 7 Tage)
10. ⚠️ DB-Repair-Backups prüfen → löschen (wenn älter als 7 Tage)
11. ⚠️ Alte Start-Scripts prüfen → löschen oder verschieben

---

## 🎯 Geschätzter Platzgewinn

- **Extrahierte Backups:** ~417 Dateien
- **Temporäre Dateien:** ~30 Dateien
- **Alte Audits:** ~20 Dateien
- **Gesamt:** ~467 Dateien könnten entfernt/verschoben werden

---

## ⚠️ WICHTIG: Vor dem Löschen

1. **Backup erstellen** (wird gerade gemacht)
2. **Git-Status prüfen** (uncommitted Änderungen?)
3. **Wichtige Dateien identifizieren** (nicht löschen!)
4. **Schrittweise vorgehen** (nicht alles auf einmal)

---

## 📝 Nächste Schritte

1. ✅ Backup von heute erstellen (läuft gerade)
2. ⏭️ Phase 1 ausführen (sichere Löschungen)
3. ⏭️ Phase 2 ausführen (Verschiebungen)
4. ⏭️ Phase 3 ausführen (Prüfungen)

---

**Erstellt:** 2025-11-20  
**Status:** Bereit zur Ausführung

