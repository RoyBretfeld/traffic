# Fix: OSRM-Polygone werden jetzt korrekt geladen

## Problem behoben

**Datum:** 2025-11-06

**Problem:**
- Endpoint `/api/tour/route-details` gab 404 zurück
- OSRM-Client gab keine Geometrie zurück (httpx.Timeout-Fehler)

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

## Test-Ergebnisse

**Vorher:**
- Endpoint: 404 Not Found
- Geometrie: Nein
- Quelle: haversine_fallback

**Nachher:**
- Endpoint: 200 OK ✅
- Geometrie: Ja (1154 Zeichen Polyline) ✅
- Quelle: osrm ✅

## Nächste Schritte

1. ✅ Server neu gestartet
2. ✅ Endpoint getestet (200 + Geometrie)
3. ⏳ Frontend testen (Browser-Cache leeren)
4. ⏳ Routen auf Karte prüfen (sollten Straßen zeigen, nicht Geraden)

## Status

- **Endpoint funktioniert:** ✅
- **OSRM-Geometrie wird zurückgegeben:** ✅
- **Frontend-Dekodierung:** ⏳ (muss getestet werden)

