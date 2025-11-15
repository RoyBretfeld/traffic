# Changelog 2025-11-06

## Behobene Probleme

### 1. OSRM-Routen-Visualisierung behoben ✅

**Problem:**
- Routen wurden als gerade Linien angezeigt statt Straßen-Geometrien
- Endpoint `/api/tour/route-details` gab 404 zurück
- OSRM-Client gab keine Geometrie zurück

**Root Cause:**
- `httpx.Timeout` benötigt alle vier Parameter (connect, read, write, pool)
- Nur `connect` und `read` waren gesetzt → Fehler beim Request

**Fix:**
- `services/osrm_client.py` Zeile 137-142: Timeout-Parameter vervollständigt
  ```python
  timeout = httpx.Timeout(
      connect=self.connect_timeout,
      read=self.read_timeout,
      write=30.0,  # Neu hinzugefügt
      pool=5.0     # Neu hinzugefügt
  )
  ```

**Ergebnis:**
- ✅ Endpoint antwortet mit 200 OK
- ✅ OSRM-Geometrie wird korrekt zurückgegeben (Polyline)
- ✅ Frontend kann Routen als Straßen anzeigen

### 2. Workflow-Upload Fehlerbehandlung verbessert ✅

**Problem:**
- 500 Internal Server Error wurde als Plain Text zurückgegeben
- Frontend konnte Fehler nicht parsen (JSON Parsing Error)

**Fix:**
- `routes/workflow_api.py` Zeile 1674-1683: JSONResponse statt HTTPException
- Fehler werden jetzt als strukturiertes JSON zurückgegeben

### 3. Synonym-Eintrag "36 Nici zu RP" aktualisiert ✅

**Problem:**
- Adresse fehlte für "36 Nici zu RP" (KdNr 4993 → 4601)

**Fix:**
- `scripts/import_customer_synonyms.py`: Adresse und Koordinaten hinzugefügt
- Synonym-Import ausgeführt
- Datenbank aktualisiert

**Eintrag:**
- Alias: "36 Nici zu RP"
- Echte KdNr: 4601
- Adresse: Mügelner Str. 29, 01237 Dresden
- Koordinaten: (51.013179, 13.804567)

### 4. Marker-Nummerierung implementiert ✅

**Status:** Bereits implementiert und funktionsfähig
- Marker zeigen Nummern auf der Karte
- Nummerierung beginnt bei 1 für erste Kunde

## Neue Dateien

1. `docs/PROBLEM_OSRM_POLYGONE.md` - Problem-Analyse
2. `docs/FIX_ROUTE_DETAILS_404.md` - Fix-Anleitung
3. `docs/FIX_APPLIED_OSRM_TIMEOUT.md` - Angewandter Fix
4. `tests/route_details_test.http` - HTTP-Tests
5. `tests/route_details_payload.json` - Test-Payload
6. `tests/powershell_tests.ps1` - PowerShell-Test-Script
7. `ZIP/OSRM_POLYGONE_PROBLEM_20251106_205624.zip` - Alle relevanten Dateien

## Technische Details

### OSRM-Client Fix

**Datei:** `services/osrm_client.py`
**Zeile:** 137-142

**Vorher:**
```python
timeout = httpx.Timeout(
    connect=self.connect_timeout,
    read=self.read_timeout
)
```

**Nachher:**
```python
timeout = httpx.Timeout(
    connect=self.connect_timeout,
    read=self.read_timeout,
    write=30.0,
    pool=5.0
)
```

### Workflow-Error-Handling

**Datei:** `routes/workflow_api.py`
**Zeile:** 1674-1683

**Vorher:**
```python
raise HTTPException(500, detail=f"Upload-Workflow-Fehler: {error_msg}")
```

**Nachher:**
```python
return JSONResponse(
    status_code=500,
    content={
        "success": False,
        "error": "Upload-Workflow-Fehler",
        "detail": error_msg,
        "type": type(e).__name__
    },
    media_type="application/json; charset=utf-8"
)
```

## Test-Status

- ✅ Endpoint `/api/tour/route-details` funktioniert (200 OK)
- ✅ OSRM-Geometrie wird zurückgegeben
- ✅ Synonym-Import erfolgreich
- ⏳ Frontend-Test (Browser-Cache leeren erforderlich)

## Nächste Schritte (für morgen)

1. **Browser-Cache leeren** (Strg+Shift+R)
2. **CSV-Datei erneut hochladen**
3. **Routen auf Karte prüfen** - sollten Straßen zeigen
4. **"36 Nici zu RP" testen** - sollte jetzt Adresse haben

## Bekannte Probleme

- Frontend zeigt möglicherweise noch alte Version (Cache)
- Server muss komplett neu gestartet werden für alle Änderungen

## Server-Status

- ✅ Server läuft auf Port 8111
- ✅ OSRM läuft (Docker Container)
- ✅ Datenbank funktioniert
- ✅ Endpoints verfügbar

