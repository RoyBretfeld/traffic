# Audit: Upload-Funktionalität Fehleranalyse
**Datum:** 2025-01-10  
**Status:** 🔴 KRITISCH - Upload funktioniert nicht  
**Priorität:** HOCH

---

## Problembeschreibung

Der CSV-Upload funktioniert nicht mehr. Benutzer berichtet: "Upload geht nicht, so schlimm war es lange nicht."

---

## Betroffene Komponenten

### Frontend (`frontend/index.html`)
- `handleFileChange()` - Wird beim Datei-Auswählen aufgerufen
- `uploadCsvFile(file)` - Haupt-Upload-Funktion
- `apiUploadCsv(file)` - API-Call zum Backend
- `runWorkflow()` - Workflow-Start nach Upload
- `loadMatchForFile(filePath)` - Match nach Upload

### Backend (`routes/upload_csv.py`)
- `POST /api/upload/csv` - Upload-Endpoint
- `cleanup_old_staging_files()` - Cleanup-Funktion
- `_heuristic_decode()` - Encoding-Erkennung

### Backend (`routes/workflow_api.py`)
- `POST /api/workflow/upload` - Workflow-Upload-Endpoint

---

## Mögliche Fehlerquellen

### 1. **Frontend: DOM-Elemente fehlen**
**Datei:** `frontend/index.html`  
**Zeile:** 628-639

```javascript
const uploadInfo = document.getElementById('uploadInfo');
const status = document.getElementById('workflowStatus');

if (!uploadInfo) {
    console.error('[UPLOAD] uploadInfo Element nicht gefunden!');
    return;  // ❌ FRÜHES RETURN - Upload wird abgebrochen!
}
```

**Problem:** Wenn `uploadInfo` oder `workflowStatus` nicht gefunden werden, wird der Upload abgebrochen.

**Lösung:** 
- Prüfen ob Elemente im HTML vorhanden sind
- Fallback-Logging implementieren
- Fehlerbehandlung verbessern

---

### 2. **Backend: Cleanup könnte Dateien löschen**
**Datei:** `routes/upload_csv.py`  
**Zeile:** 23-72

```python
def cleanup_old_staging_files():
    # Lösche Dateien älter als STAGING_RETENTION_HOURS
    # Lösche älteste Dateien wenn mehr als STAGING_MAX_FILES vorhanden
```

**Problem:** Cleanup wird VOR dem Speichern aufgerufen (Zeile 246). Wenn zu viele Dateien vorhanden sind, könnte die neue Datei sofort gelöscht werden.

**Lösung:**
- Cleanup NACH dem Speichern aufrufen
- Oder: Cleanup nur wenn Platz benötigt wird

---

### 3. **Backend: Encoding-Erkennung könnte fehlschlagen**
**Datei:** `routes/upload_csv.py`  
**Zeile:** 85-100

```python
def _heuristic_decode(raw: bytes, skip_mojibake_check: bool = False) -> tuple[str, str]:
    for enc in ("cp850", "utf-8-sig", "latin-1"):
        try:
            decoded = raw.decode(enc)
            assert_no_mojibake(decoded)  # ❌ Könnte Exception werfen
```

**Problem:** `assert_no_mojibake()` könnte eine Exception werfen, wenn Mojibake erkannt wird.

**Lösung:**
- Fehlerbehandlung verbessern
- Mojibake-Reparatur vor Assertion

---

### 4. **Frontend: Response-Parsing könnte fehlschlagen**
**Datei:** `frontend/index.html`  
**Zeile:** 606-618

```javascript
const responseText = await response.text();
let payload;
try {
    payload = JSON.parse(responseText);
} catch (e) {
    console.error('[UPLOAD] JSON Parsing Fehler:', e);
    throw new Error(`Ungültige Server-Antwort: ${responseText.substring(0, 100)}...`);
}
```

**Problem:** Wenn der Server keine JSON-Antwort zurückgibt, schlägt das Parsing fehl.

**Lösung:**
- Bessere Fehlerbehandlung
- Prüfen ob Response JSON ist (Content-Type)

---

### 5. **Frontend: Pfad-Extraktion könnte fehlschlagen**
**Datei:** `frontend/index.html`  
**Zeile:** 650-676

```javascript
const stagedPath = result.stored_path || result.staged_path || result.staging_file || result.filename || null;

if (stagedPath && stagedPath !== 'undefined' && stagedPath !== 'null' && typeof stagedPath === 'string' && stagedPath.trim() !== '') {
    // OK
} else {
    // ⚠️ Warnung, aber Upload wird als erfolgreich angezeigt
    updateWorkflowStatus('⚠ Upload erfolgreich, aber Match konnte nicht gestartet werden');
}
```

**Problem:** Wenn `stagedPath` fehlt, wird der Upload als erfolgreich angezeigt, aber Match funktioniert nicht.

**Lösung:**
- Klarere Fehlermeldung
- Upload als fehlgeschlagen markieren wenn Pfad fehlt

---

### 6. **Backend: Pfad-Rückgabe könnte inkonsistent sein**
**Datei:** `routes/upload_csv.py`  
**Zeile:** 260-272

```python
return JSONResponse({
    "stored_path": staged_path_str,  # Hauptfeld
    "staged_path": staged_path_str,    # Kompatibilität
    "staging_file": staged_path_str,  # Kompatibilität
    # ...
})
```

**Problem:** Mehrere Felder für den gleichen Wert - könnte zu Verwirrung führen.

**Lösung:**
- Standardisiertes Feld verwenden
- Dokumentation verbessern

---

## Debugging-Schritte

### 1. Browser-Konsole prüfen
- Öffne Browser-Entwicklertools (F12)
- Prüfe Console-Tab auf Fehler
- Prüfe Network-Tab auf fehlgeschlagene Requests

### 2. Server-Logs prüfen
- Prüfe Server-Output auf `[UPLOAD ERROR]` oder `[UPLOAD WARNING]`
- Prüfe auf Exceptions beim Upload

### 3. API-Endpoint testen
```bash
curl -X POST http://localhost:8111/api/upload/csv \
  -F "file=@test.csv" \
  -v
```

### 4. Staging-Verzeichnis prüfen
- Prüfe ob `./data/staging` existiert
- Prüfe ob Dateien dort gespeichert werden
- Prüfe Berechtigungen

---

## Empfohlene Fixes

### Fix 1: DOM-Element-Prüfung verbessern
**Datei:** `frontend/index.html`

```javascript
async function uploadCsvFile(file) {
    const uploadInfo = document.getElementById('uploadInfo');
    const status = document.getElementById('workflowStatus');
    
    // Fallback: Erstelle Elemente wenn sie fehlen
    if (!uploadInfo) {
        console.warn('[UPLOAD] uploadInfo Element nicht gefunden, erstelle Fallback');
        const container = document.querySelector('#workflowSidebar');
        if (container) {
            const fallback = document.createElement('div');
            fallback.id = 'uploadInfo';
            fallback.className = 'small text-muted mt-2';
            container.appendChild(fallback);
        }
    }
    
    // ... rest of function
}
```

### Fix 2: Cleanup nach Upload
**Datei:** `routes/upload_csv.py`

```python
# Cleanup NACH dem Speichern (nicht vorher)
staged_path.write_text(decoded_content, encoding='utf-8')

# Cleanup nur wenn nötig (nicht bei jedem Upload)
if len(list(STAGING.glob("*.csv"))) > STAGING_MAX_FILES:
    cleanup_old_staging_files()
```

### Fix 3: Bessere Fehlerbehandlung
**Datei:** `routes/upload_csv.py`

```python
try:
    decoded_content, encoding = _heuristic_decode(content)
except Exception as e:
    print(f"[UPLOAD ERROR] Encoding-Erkennung fehlgeschlagen: {e}")
    # Fallback: UTF-8 mit Fehlerbehandlung
    decoded_content = content.decode('utf-8', errors='replace')
    encoding = 'utf-8-fallback'
```

### Fix 4: Response-Validierung
**Datei:** `frontend/index.html`

```javascript
if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload fehlgeschlagen: ${response.status} ${errorText}`);
}

// Prüfe Content-Type
const contentType = response.headers.get('content-type');
if (!contentType || !contentType.includes('application/json')) {
    console.warn('[UPLOAD] Response ist nicht JSON:', contentType);
}
```

---

## Test-Plan

### Test 1: Einfacher Upload
1. Öffne Frontend
2. Wähle CSV-Datei aus
3. Prüfe ob Upload-Status angezeigt wird
4. Prüfe Browser-Konsole auf Fehler
5. Prüfe ob Datei in `./data/staging` gespeichert wird

### Test 2: Upload mit fehlenden DOM-Elementen
1. Entferne `uploadInfo` Element aus HTML
2. Versuche Upload
3. Prüfe ob Fallback funktioniert

### Test 3: Upload mit vielen vorhandenen Dateien
1. Erstelle 150 CSV-Dateien in `./data/staging`
2. Versuche neuen Upload
3. Prüfe ob Cleanup korrekt funktioniert

### Test 4: Upload mit verschiedenen Encodings
1. Teste mit cp850-encoded CSV
2. Teste mit UTF-8 CSV
3. Teste mit latin-1 CSV
4. Prüfe ob alle korrekt verarbeitet werden

---

## Status-Tracking

- [x] Fix 1: DOM-Element-Prüfung verbessern ✅ **IMPLEMENTIERT**
- [x] Fix 2: Cleanup nach Upload ✅ **IMPLEMENTIERT**
- [x] Fix 3: Bessere Fehlerbehandlung ✅ **IMPLEMENTIERT**
- [x] Fix 4: Response-Validierung ✅ **IMPLEMENTIERT**
- [ ] Test 1: Einfacher Upload (Benutzer-Test erforderlich)
- [ ] Test 2: Upload mit fehlenden DOM-Elementen (Benutzer-Test erforderlich)
- [ ] Test 3: Upload mit vielen vorhandenen Dateien (Benutzer-Test erforderlich)
- [ ] Test 4: Upload mit verschiedenen Encodings (Benutzer-Test erforderlich)

---

## Implementierte Fixes (2025-01-10)

### ✅ Fix 1: DOM-Element-Prüfung verbessert
**Datei:** `frontend/index.html` (Zeilen 631-660)

**Änderungen:**
- Fallback-Erstellung von `uploadInfo` und `workflowStatus` Elementen wenn sie fehlen
- Bessere Fehlermeldungen mit `alert()` wenn Container nicht gefunden wird
- Upload wird nicht mehr abgebrochen wenn Elemente fehlen

**Code:**
```javascript
// Fallback: Erstelle Elemente wenn sie fehlen (für Robustheit)
if (!uploadInfo) {
    console.warn('[UPLOAD] uploadInfo Element nicht gefunden, erstelle Fallback');
    const container = document.querySelector('#workflowSidebar');
    if (container) {
        const fallback = document.createElement('div');
        fallback.id = 'uploadInfo';
        fallback.className = 'small text-muted mt-2';
        container.appendChild(fallback);
    }
}
```

---

### ✅ Fix 2: Cleanup nach Upload verschoben
**Datei:** `routes/upload_csv.py` (Zeilen 252-259)

**Änderungen:**
- Cleanup wird NACH dem Speichern aufgerufen (nicht vorher)
- Cleanup wird nur ausgeführt wenn mehr als `STAGING_MAX_FILES` Dateien vorhanden sind
- Verhindert dass neue Dateien sofort gelöscht werden

**Code:**
```python
# In Staging-Verzeichnis speichern (UTF-8)
staged_path.write_text(decoded_content, encoding='utf-8')

# Cleanup alter Dateien NACH dem Speichern (nur wenn nötig)
staging_files = list(STAGING.glob("*.csv"))
if len(staging_files) > STAGING_MAX_FILES:
    print(f"[UPLOAD] Zu viele Staging-Dateien ({len(staging_files)} > {STAGING_MAX_FILES}), starte Cleanup...")
    cleanup_old_staging_files()
```

---

### ✅ Fix 3: Bessere Fehlerbehandlung bei Encoding
**Datei:** `routes/upload_csv.py` (Zeilen 241-250)

**Änderungen:**
- Try-Catch um `_heuristic_decode()` und `repair_cp_mojibake()`
- UTF-8 Fallback wenn Encoding-Erkennung fehlschlägt
- Besseres Logging von Fehlern

**Code:**
```python
try:
    decoded_content, encoding = _heuristic_decode(content)
    decoded_content = repair_cp_mojibake(decoded_content)
except Exception as e:
    print(f"[UPLOAD ERROR] Encoding-Erkennung fehlgeschlagen: {e}, verwende UTF-8 Fallback")
    # Fallback: UTF-8 mit Fehlerbehandlung
    decoded_content = content.decode('utf-8', errors='replace')
    encoding = 'utf-8-fallback'
    decoded_content = repair_cp_mojibake(decoded_content)
```

---

### ✅ Fix 4: Response-Validierung verbessert
**Datei:** `frontend/index.html` (Zeilen 605-631, 707-716)

**Änderungen:**
- Content-Type Prüfung vor JSON-Parsing
- Response-Struktur-Validierung
- Bessere Fehlermeldungen wenn Pfad fehlt
- Upload wird als fehlgeschlagen markiert wenn Pfad fehlt (nicht nur Warnung)

**Code:**
```javascript
// Prüfe Content-Type
const contentType = response.headers.get('content-type') || '';
if (!contentType.includes('application/json') && !contentType.includes('text/')) {
    console.warn('[UPLOAD] Response ist möglicherweise nicht JSON:', contentType);
}

// Validiere Response-Struktur
if (!payload || typeof payload !== 'object') {
    console.error('[UPLOAD] Ungültige Response-Struktur:', payload);
    throw new Error('Ungültige Server-Antwort: Kein Objekt erhalten');
}

// Bessere Fehlerbehandlung wenn Pfad fehlt
if (!stagedPath || ...) {
    console.error('[UPLOAD] Kein gültiger Pfad gefunden in Response:', result);
    uploadInfo.innerHTML = `<i class="fas fa-exclamation-triangle text-warning"></i> Upload unvollständig...`;
    throw new Error('Upload unvollständig: Server hat keinen gültigen Pfad zurückgegeben');
}
```

---

## Zusätzliche Informationen

### Relevante Dateien
- `frontend/index.html` (Zeilen 572-686)
- `routes/upload_csv.py` (Zeilen 199-279)
- `routes/workflow_api.py` (Zeilen 1099-1200)

### Änderungen seit letztem funktionierenden Upload
- Cleanup-Funktion wurde hinzugefügt (2025-01-10)
- DOM-Element-Prüfung wurde hinzugefügt (2025-01-10)
- Response-Parsing wurde verbessert (2025-01-10)

### Bekannte Probleme
- Keine bekannten Probleme vor diesem Audit

---

**Erstellt:** 2025-01-10  
**Letzte Aktualisierung:** 2025-01-10

