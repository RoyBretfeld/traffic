# Changelog – 18. November 2025

## 🔴 KRITISCH: OSRM Polyline-Fehler behoben

### Problem
- OSRM lieferte Routen mit `distance_m: 0` und `duration_s: 0`
- Polyline6 dekodierte zu identischen Koordinaten
- Frontend zeigte nur gestrichelte Luftlinien statt echte Straßenrouten

### Root Cause
Koordinaten-Formatierungsfehler in `services/osrm_client.py`:
- `coords` ist im Format `[(lon, lat), ...]`
- Schleife entpackte aber als `(lat, lon)` → Reihenfolge vertauscht
- OSRM erhielt falsche Koordinaten → ungültige Route

### Fix
1. **Koordinaten-Formatierung korrigiert** (`services/osrm_client.py` Zeile 340):
   ```python
   # VORHER (FALSCH):
   coord_string = ";".join(f"{lon},{lat}" for lat, lon in coords)
   
   # NACHHER (RICHTIG):
   coord_string = ";".join(f"{lon},{lat}" for lon, lat in coords)
   ```

2. **Validierung für ungültige Routen** (Zeile 407-418):
   - Erkennt `distance_m == 0` oder `duration_s == 0`
   - Gibt `None` zurück (nicht cachen, Fallback verwenden)
   - Loggt Request-URL und Koordinaten für Debugging

3. **Debug-Logging hinzugefügt** (Zeile 342-346):
   - Loggt erste 3 Koordinaten vor OSRM-Request
   - Loggt generierte URL-String (erste 50 Zeichen)

### Geänderte Dateien
- `services/osrm_client.py` (Koordinaten-Fix, Validierung, Logging)
- `frontend/index.html` (Prüfung auf identische Koordinaten bereits vorhanden)
- `Regeln/LESSONS_LOG.md` (Fehler dokumentiert)

### Dokumentation
- `ZIP/POLYLINE_FEHLER_AUDIT_20251118_200434.zip` (Vollständiges Audit-Paket)
- `ZIP/README_POLYLINE_AUDIT_20251118.md` (Detailliertes Audit-README)
- `ZIP/POLYLINE_FEHLER_KURZDIAGNOSE.md` (Kurzdiagnose)
- `ZIP/POLYLINE_FIX_ZUSAMMENFASSUNG.md` (Zusammenfassung)

---

## ✅ Sub-Routen-Generator repariert

### Änderungen
- Sub-Routen werden korrekt in Tour-Liste angezeigt
- Gruppierungs-Problem behoben (Base-Tour-ID-Extraktion)
- Nur Touren mit > 4 Kunden werden optimiert
- Frontend-Fetch-Timeout hinzugefügt (60 Sekunden)
- OSRM-Calls mit Timeout versehen (5 Sekunden)

### Geänderte Dateien
- `frontend/index.html`
- `backend/routes/workflow_api.py`
- `services/osrm_client.py`

---

## ✅ Route-Visualisierung verbessert

### Änderungen
- OSRM-Routen-Linien sichtbarer gemacht (weight: 6, opacity: 0.9)
- Fallback-Linien (Luftlinien) dezent gestylt (weight: 3, gestrichelt)
- Prüfung auf identische Koordinaten im Frontend
- Umfangreiches Debug-Logging für Route-Zeichnung

### Geänderte Dateien
- `frontend/index.html`

---

## 📚 Dokumentation aktualisiert

- `docs/STATUS_AKTUELL.md` – Neueste Errungenschaften hinzugefügt
- `PROJECT_PROFILE.md` – Version auf 1.2 aktualisiert
- `DOKUMENTATION.md` – Version auf 2.2 aktualisiert
- `Regeln/LESSONS_LOG.md` – Neuer Eintrag für Polyline-Fehler

---

**Stand:** 2025-11-18 21:15

