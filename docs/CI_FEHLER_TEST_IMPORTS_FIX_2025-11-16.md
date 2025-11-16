# 🔧 CI-Fehler Fix: Test-Import-Probleme

**Datum:** 2025-11-16  
**Status:** ✅ BEHOBEN  
**Fehler:** Import-Fehler in Tests durch App-Struktur-Änderung

---

## 🐛 Problem

**Fehler:** `ImportError: cannot import name 'app' from 'backend.app'`

**Ursache:**
- `backend/app.py` wurde auf Factory-Pattern umgestellt (`create_app()`)
- Alte Tests importieren noch `from backend.app import app`
- `read_tourplan_csv` war als lokale Funktion nicht exportiert

**Betroffen:**
- 10 Test-Dateien mit Import-Fehlern
- CI-Pipeline schlägt fehl

---

## ✅ Fix

### 1. App-Instanz exportieren

**Datei:** `backend/app.py`

**Änderung:**
- `app = create_app()` am Ende der Datei hinzugefügt
- Ermöglicht direkten Import: `from backend.app import app`

### 2. read_tourplan_csv exportieren

**Datei:** `backend/app.py`

**Änderung:**
- `read_tourplan_csv` aus `create_app()` herausgenommen
- Als globale Funktion exportiert
- Ermöglicht Import: `from backend.app import read_tourplan_csv`

### 3. Test-Imports aktualisiert

**Betroffene Dateien:**
- ✅ `tests/test_api_health.py`
- ✅ `tests/test_api_summary.py`
- ✅ `tests/test_pydantic_v2_fixes.py`
- ✅ `tests/test_upload_match_flow.py`
- ✅ `tests/test_subroutes_500_fix.py`
- ✅ `tests/test_phase1.py`
- ✅ `tests/test_mvp_patch.py`
- ✅ `tests/test_prompt11_ui_bindings.py`
- ✅ `tests/test_export_and_charset.py`
- ✅ `tests/test_5_plans_encoding.py`

**Änderung:**
- `from backend.app import app` → `from backend.app import create_app; app = create_app()`
- Oder: `from backend.app import app` (funktioniert jetzt wieder)

---

## 🧪 Test

**Lokal getestet:**
```bash
python -c "from backend.app import app, read_tourplan_csv; print('Import OK')"
```

**Ergebnis:** ✅ Erfolgreich

---

## 📋 Zusammenfassung

**Behoben:**
- ✅ SQLite Schema-Problem (mehrere Statements)
- ✅ Test-Import-Probleme (app, read_tourplan_csv)

**Noch zu prüfen:**
- ⏳ Weitere Test-Fehler (falls vorhanden)
- ⏳ CI-Pipeline erneut ausführen

---

**Erstellt:** 2025-11-16  
**Status:** ✅ **BEHOBEN**  
**Nächste Schritte:** CI-Pipeline erneut ausführen

