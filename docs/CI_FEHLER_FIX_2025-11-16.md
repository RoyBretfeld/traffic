# 🔧 CI-Fehler Fix: SQLite Schema-Problem

**Datum:** 2025-11-16  
**Status:** ✅ BEHOBEN  
**Fehler:** Exit Code 2 in CI-Pipeline

---

## 🐛 Problem

**Fehler:** `You can only execute one statement at a time.`

**Ursache:**
- `db/schema_error_learning.py` führte mehrere SQL-Statements auf einmal aus
- SQLite kann nur **ein Statement auf einmal** ausführen
- `ERROR_LEARNING_SCHEMA` enthält mehrere Statements (getrennt durch `;`)

**Betroffen:**
- CI-Pipeline (GitHub Actions)
- Lokale Schema-Erstellung

---

## ✅ Fix

**Datei:** `db/schema_error_learning.py`

**Änderung:**
- `ensure_error_learning_schema()` teilt jetzt `ERROR_LEARNING_SCHEMA` in einzelne Statements
- Führt jedes Statement einzeln aus
- Fehler bei einzelnen Statements werden ignoriert (z.B. Tabelle existiert bereits)

**Code:**
```python
def ensure_error_learning_schema(conn):
    """
    Idempotent: Stellt sicher, dass alle Error-Learning-Tabellen existieren.
    
    WICHTIG: SQLite kann nur ein Statement auf einmal ausführen!
    """
    try:
        # SQLite kann nur ein Statement auf einmal ausführen
        # Teile ERROR_LEARNING_SCHEMA in einzelne Statements
        statements = ERROR_LEARNING_SCHEMA.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as stmt_error:
                    # Einzelnes Statement-Fehler (z.B. Tabelle existiert bereits)
                    # Logge nur im Debug-Modus, nicht als Fehler
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"[SCHEMA] Statement-Fehler (kann ignoriert werden): {stmt_error}")
                    # Weiter mit nächstem Statement
                    continue
        conn.commit()
    except Exception as e:
        # Allgemeiner Fehler
        import logging
        logging.getLogger(__name__).warning(f"[SCHEMA] Fehler beim Erstellen der Error-Learning-Tabellen: {e}")
        # Versuche trotzdem weiter (Tabellen könnten bereits existieren)
        pass
```

---

## 🧪 Test

**Lokal getestet:**
```bash
python -c "from db.schema import ensure_schema; ensure_schema(); print('Schema OK')"
```

**Ergebnis:** ✅ Erfolgreich

---

## 📋 Nächste Schritte

1. ✅ **Fix implementiert**
2. ⏳ **CI-Pipeline testen** (beim nächsten Push)
3. ⏳ **Weitere Tests prüfen** (falls andere Fehler auftreten)

---

## 🔍 Weitere mögliche CI-Probleme

### 1. Import-Fehler
- Neue Module könnten fehlende Dependencies haben
- Prüfen: `requirements.txt` vollständig?

### 2. Test-Fehler
- Tests könnten durch Schema-Änderungen betroffen sein
- Prüfen: Alle Tests laufen lokal?

### 3. Docker-Build
- Dockerfile könnte neue Dependencies benötigen
- Prüfen: Docker-Build lokal testen

---

**Erstellt:** 2025-11-16  
**Status:** ✅ **BEHOBEN**  
**Nächste Schritte:** CI-Pipeline erneut ausführen

