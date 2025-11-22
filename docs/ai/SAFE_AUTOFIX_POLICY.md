# Safe-Autofix Policy – TrafficApp 3.0

**Zweck:** Definiert, welche Änderungen KI automatisch vornehmen darf (Safe-Autofix) und welche niemals automatisch geändert werden dürfen.

**Status:** Phase 1 (Advisor only) aktiv, Phase 2 (Safe-Autofix) geplant

---

## ✅ Allow-List (Auto-Fix erlaubt)

### Formatierung & Code-Style
- ✅ Whitespace, Einrückung, Zeilenumbrüche
- ✅ Typo-Korrekturen in Kommentaren
- ✅ Dead Code Removal (nur wenn keine public API betroffen)
- ✅ Linter-Fixes (ruff/flake8) – automatische Formatierung

### Type Annotations
- ✅ mypy-Annotationen hinzufügen (keine Logikänderung)
- ✅ Type Hints ergänzen (ohne Verhalten zu ändern)

### Security Headers (nur mit Feature-Flag)
- ✅ Security-Header setzen (nur wenn `APP_ENV=production` Feature-Flag geschützt)
- ✅ CORS-Konfiguration (nur wenn Zielwerte in Feature-Flag definiert)

### Upload-Schutz (nur Guards)
- ✅ Dateiname-Whitelist hinzufügen
- ✅ `resolve()`-Guard hinzufügen
- ❌ **NICHT:** Pfad-Konstanten ändern

---

## ❌ Block-List (niemals auto)

### Authentication & Authorization
- ❌ Auth/Session-Logik ändern
- ❌ RBAC-Implementierung
- ❌ Password-Hashing ändern
- ❌ Login-Flows ändern

### Database & Migrations
- ❌ DB-Schema-Änderungen
- ❌ Migrations erstellen/ändern
- ❌ SQL-Queries ändern (außer Formatierung)

### Business Logic (kritisch)
- ❌ Zahlungs-/Kostenlogik
- ❌ OSRM/Geocode-Algorithmik
- ❌ Routing-Optimierung
- ❌ Tour-Berechnungen

### Infrastructure & Deployment
- ❌ Build-Pipelines ändern
- ❌ Deploy-Skripte ändern
- ❌ Docker-Konfiguration
- ❌ CI/CD-Workflows (außer Kommentare)

### Configuration & Secrets
- ❌ Secrets-Management ändern
- ❌ Environment-Variablen ändern
- ❌ Feature-Flags ändern

---

## 🛡️ Guardrails

### Write-Fence
**KI darf nur ändern:**
- `frontend/**` (HTML, JS, CSS)
- `backend/routes/**` (API-Endpoints, nur Formatierung)
- `backend/services/**` (Business-Logik, nur Formatierung)

**KI darf NICHT ändern (read-only):**
- `backend/routes/auth_api.py` (Auth-Logik)
- `db/schema.py`, `db/migrations/**`
- `backend/services/geocode.py` (Algorithmik)
- `backend/services/cost_tracker.py` (Kostenlogik)
- `infra/**`, `.github/workflows/**` (außer Kommentare)

### Test-Gate
- Jeder Auto-Fix → `pytest -q` muss grün sein
- Linter muss grün sein
- Sonst: PR wird nicht erstellt

### Diff-Budget
- **Max. 200 Zeilen** pro Auto-Fix-PR
- Größere Änderungen → Advisor-Modus

### Policy-Gate
- Änderungen an sensiblen Dateien benötigen Label `requires-owner-approval`
- Sensible Dateien: `auth_api.py`, `cost_tracker.py`, `geocode.py`, `schema.py`

---

## 📋 Entscheidungsmatrix

| Änderung | Auto-Fix? | Bedingung |
|----------|-----------|-----------|
| Formatierung (ruff) | ✅ Ja | Keine Logikänderung |
| Typo in Kommentar | ✅ Ja | Keine Code-Änderung |
| Dead Code entfernen | ✅ Ja | Keine public API betroffen |
| mypy-Annotation | ✅ Ja | Keine Logikänderung |
| Security-Header | ⚠️ Nur mit Flag | Feature-Flag geschützt |
| Upload-Guard | ⚠️ Nur Guards | Keine Pfad-Änderung |
| Auth-Logik | ❌ Nein | Immer Advisor |
| DB-Schema | ❌ Nein | Immer Advisor |
| Kostenlogik | ❌ Nein | Immer Advisor |
| Routing-Algorithmik | ❌ Nein | Immer Advisor |

---

## 🔄 Workflow

1. **KI erkennt Änderung**
2. **Prüft Allow-List** → Erlaubt?
3. **Prüft Write-Fence** → Datei erlaubt?
4. **Prüft Diff-Budget** → < 200 Zeilen?
5. **Erstellt Patch** → Tests laufen
6. **Tests grün?** → PR erstellen
7. **Tests rot?** → Advisor-Modus (nur Kommentar)

---

**Letzte Aktualisierung:** 2025-11-22

