#!/usr/bin/env python3
"""
Erstellt ein fokussiertes Audit-ZIP für den Polyline-Fehler (OSRM-Routen nicht sichtbar).

Dieses Script erstellt eine ZIP-Datei mit allen relevanten Dateien für die Analyse
des Problems: OSRM liefert Routen mit distance_m: 0, alle Koordinaten identisch.
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent

# Fokussierte Dateien für Polyline-Problem
POLYLINE_RELEVANT_FILES = [
    # Backend: OSRM-Client
    'services/osrm_client.py',
    'backend/services/real_routing.py',
    'backend/cache/osrm_cache.py',
    
    # Backend: Route-Details API
    'backend/routes/tour_routes.py',
    'backend/routes/workflow_api.py',
    
    # Frontend: Route-Visualisierung
    'frontend/index.html',  # drawRouteLines, decodePolyline, etc.
    
    # Dokumentation
    'Regeln/LESSONS_LOG.md',  # Eintrag zum Polyline-Fehler
    'Regeln/AUDIT_FLOW_ROUTING.md',
    'PROJECT_PROFILE.md',
    'docs/Architecture.md',
    
    # Konfiguration
    'backend/config.py',
    '.env.example',
]

# Zusätzliche Verzeichnisse für Kontext
POLYLINE_RELEVANT_DIRS = [
    'services',
    'backend/services',
    'backend/routes',
    'backend/cache',
    'frontend',
]

def create_polyline_audit_zip(output_path: Path):
    """Erstellt das fokussierte Polyline-Audit-ZIP-Paket."""
    print(f"[ZIP] Erstelle Polyline-Audit-Paket: {output_path.name}")
    print(f"[ZIP] Projekt-Root: {PROJECT_ROOT}")
    print()
    
    file_count = 0
    total_size = 0
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Füge spezifische Dateien hinzu
        for rel_file in POLYLINE_RELEVANT_FILES:
            file_path = PROJECT_ROOT / rel_file
            if file_path.exists():
                try:
                    zipf.write(file_path, rel_file)
                    file_count += 1
                    total_size += file_path.stat().st_size
                    print(f"   [+] {rel_file}")
                except Exception as e:
                    print(f"   [WARN] Fehler bei {rel_file}: {e}")
            else:
                print(f"   [SKIP] Nicht gefunden: {rel_file}")
        
        # Füge relevante Verzeichnisse hinzu (nur Python/JS/HTML/CSS/MD)
        for rel_dir in POLYLINE_RELEVANT_DIRS:
            dir_path = PROJECT_ROOT / rel_dir
            if dir_path.exists() and dir_path.is_dir():
                for root, dirs, files in os.walk(dir_path):
                    root_path = Path(root)
                    
                    # Filtere ausgeschlossene Verzeichnisse
                    dirs[:] = [d for d in dirs if d not in {'__pycache__', '.git', 'venv', 'node_modules'}]
                    
                    for file in files:
                        file_path = root_path / file
                        
                        # Nur relevante Dateitypen
                        if file_path.suffix not in {'.py', '.js', '.html', '.css', '.md', '.json', '.txt'}:
                            continue
                        
                        # Überspringe bereits hinzugefügte Dateien
                        rel_path = file_path.relative_to(PROJECT_ROOT)
                        rel_str = str(rel_path).replace('\\', '/')
                        if rel_str in POLYLINE_RELEVANT_FILES:
                            continue
                        
                        try:
                            zipf.write(file_path, rel_path)
                            file_count += 1
                            total_size += file_path.stat().st_size
                        except Exception as e:
                            print(f"   [WARN] Fehler bei {rel_path}: {e}")
    
    print()
    print(f"[OK] ZIP erstellt: {output_path.name}")
    print(f"[OK] Dateien: {file_count}")
    print(f"[OK] Groesse: {total_size / 1024 / 1024:.2f} MB")
    print(f"[OK] ZIP-Groesse: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

def create_polyline_readme(output_path: Path):
    """Erstellt spezifische README für das Polyline-Audit."""
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    zip_name = output_path.name
    
    readme_content = f"""# Polyline-Fehler Audit – FAMO TrafficApp 3.0

**Erstellt:** {timestamp_str}  
**Zweck:** Fokussierte Analyse des Problems: OSRM-Routen werden nicht als echte Straßenrouten angezeigt

---

## 🔴 Problem-Beschreibung

### Symptom

- OSRM liefert Routen mit `distance_m: 0` und `duration_s: 0`
- Polyline6-Dekodierung ergibt identische Koordinaten (z.B. alle `[50.815399, 14.766153]`)
- Frontend erkennt das korrekt und verwendet Fallback (Luftlinien)
- **Aber: Keine echten Straßenrouten werden angezeigt, nur gestrichelte Luftlinien**
- OSRM-Response hat `200 OK`, aber Route ist ungültig
- Direkter OSRM-Test funktioniert (liefert gültige Route mit distance > 0)

### Vermutete Ursache

**Koordinaten-Formatierungsfehler in `osrm_client.py`:**
- `coords` ist im Format `[(lon, lat), (lon, lat), ...]` (siehe `build_route_details`)
- Aber die Schleife iteriert als `(lat, lon)`, was die Reihenfolge vertauscht
- OSRM erhält falsche Koordinaten → liefert ungültige Route

---

## 📁 Relevante Dateien (in diesem ZIP)

### Backend (OSRM-Integration)

1. **`services/osrm_client.py`** ⚠️ **HAUPTPROBLEM**
   - Zeile 331: `coord_string = ";".join(f"{{lon}},{{lat}}" for lat, lon in coords)`
   - **FEHLER:** Iteriert als `(lat, lon)`, aber `coords` ist `[(lon, lat), ...]`
   - **FIX:** `coord_string = ";".join(f"{{lon}},{{lat}}" for lon, lat in coords)`
   - Zeile 380-400: Validierung für ungültige Routen (distance_m: 0)

2. **`backend/services/real_routing.py`**
   - Zeile 293-299: `build_route_details()` konvertiert Koordinaten zu `[(lon, lat), ...]`
   - Zeile 313-316: Ruft `osrm_client.get_route(coords_osrm, ...)` auf

3. **`backend/cache/osrm_cache.py`**
   - Cache für OSRM-Routen (könnte ungültige Routen cachen)

### Frontend (Route-Visualisierung)

4. **`frontend/index.html`** ⚠️ **WICHTIG**
   - Zeile 4186-4296: `decodePolyline()` und `decodePolyline6Inline()`
   - Zeile 4299-4450: `drawRouteLines()` – zeichnet OSRM-Routen
   - Zeile 4410-4418: Prüfung auf identische Koordinaten
   - Zeile 4451-4520: `drawStraightLines()` – Fallback für Luftlinien

### Dokumentation

5. **`Regeln/LESSONS_LOG.md`**
   - Eintrag: "2025-11-18 – OSRM liefert Routen mit distance_m: 0 (alle Koordinaten identisch)"
   - Vollständige Fehlerbeschreibung, Ursache, Fix, Lessons Learned

---

## 🔍 Audit-Aufgabe

**Ziel:** Finde und fixe den Fehler, warum OSRM keine echten Straßenrouten liefert.

### Schritt 1: Koordinaten-Format prüfen

1. Öffne `services/osrm_client.py` Zeile 331
2. Prüfe: In welchem Format ist `coords`?
   - Siehe `backend/services/real_routing.py` Zeile 299: `coords_osrm = [(lon, lat) for lat, lon in coords_raw]`
   - **Ergebnis:** `coords` ist `[(lon, lat), (lon, lat), ...]`
3. Prüfe: Wie wird `coord_string` formatiert?
   - Aktuell: `f"{{lon}},{{lat}}" for lat, lon in coords`
   - **Problem:** Iteriert als `(lat, lon)`, aber `coords` ist `[(lon, lat), ...]`
   - **Fix:** `f"{{lon}},{{lat}}" for lon, lat in coords`

### Schritt 2: OSRM-Request validieren

1. Prüfe `services/osrm_client.py` Zeile 380-400
2. Wird `distance_m: 0` erkannt und abgelehnt?
3. Wird die Request-URL geloggt für Debugging?

### Schritt 3: Frontend-Validierung prüfen

1. Öffne `frontend/index.html` Zeile 4410-4418
2. Wird geprüft, ob alle Koordinaten identisch sind?
3. Wird der Fallback korrekt verwendet?

### Schritt 4: Test durchführen

```bash
# Server starten
python start_server.py

# Im Browser: Tour mit Sub-Routen laden
# Erwartung: Echte Straßenrouten (nicht nur Luftlinien)
```

---

## 🛠️ Fix-Strategie

### Fix 1: Koordinaten-Formatierung korrigieren

**Datei:** `services/osrm_client.py`  
**Zeile:** 331

```python
# VORHER (FALSCH):
coord_string = ";".join(f"{{lon}},{{lat}}" for lat, lon in coords)

# NACHHER (RICHTIG):
coord_string = ";".join(f"{{lon}},{{lat}}" for lon, lat in coords)
# WICHTIG: coords ist bereits [(lon, lat), ...], daher korrekte Iteration
```

### Fix 2: Ungültige Routen erkennen

**Datei:** `services/osrm_client.py`  
**Zeile:** 380-400

```python
# Prüfe ob Route gültig ist (distance > 0)
if distance_m == 0 or duration_s == 0:
    self.logger.warning(f"OSRM: Route hat distance_m={{distance_m}}, duration_s={{duration_s}} - möglicherweise ungültig")
    self.logger.warning(f"OSRM: Request-URL war: {{url}}")
    self.logger.warning(f"OSRM: Koordinaten waren: {{coords[:3]}}... (erste 3)")
    return None  # ❌ Nicht cachen, Fallback verwenden
```

### Fix 3: Frontend-Validierung

**Datei:** `frontend/index.html`  
**Zeile:** 4410-4418

```javascript
// Prüfe ob alle Koordinaten identisch sind
const uniqueCoords = new Set(decodedCoordinates.map(c => `${{c[0].toFixed(6)}},${{c[1].toFixed(6)}}`));
if (uniqueCoords.size === 1) {{
    console.error(`❌ KRITISCH: Alle ${{decodedCoordinates.length}} Koordinaten sind identisch!`);
    drawStraightLines(customersWithCoords, routeColor, includeDepot);  // Fallback
    return;
}}
```

---

## 📊 Erwartetes Ergebnis nach Fix

1. **OSRM liefert gültige Routen:**
   - `distance_m > 0`
   - `duration_s > 0`
   - Polyline6 enthält unterschiedliche Koordinaten

2. **Frontend zeigt echte Straßenrouten:**
   - Keine Fallback-Luftlinien mehr
   - Routen folgen Straßenverlauf
   - Routen sind sichtbar auf der Karte

3. **Debug-Logs zeigen korrekte Koordinaten:**
   - Request-URL enthält `lon,lat;lon,lat;...` (nicht `lat,lon`)
   - OSRM-Response hat `distance_m > 0`

---

## 🔗 Verwandte Dokumentation

- **`Regeln/LESSONS_LOG.md`** – Vollständige Fehlerbeschreibung
- **`Regeln/AUDIT_FLOW_ROUTING.md`** – Routing-Audit-Workflow
- **`PROJECT_PROFILE.md`** – Projekt-Kontext
- **`docs/Architecture.md`** – Architektur-Übersicht

---

## ✅ Checkliste für Audit

- [ ] Koordinaten-Format in `osrm_client.py` geprüft
- [ ] Fix für `coord_string`-Formatierung implementiert
- [ ] Validierung für ungültige Routen (distance_m: 0) hinzugefügt
- [ ] Frontend-Validierung für identische Koordinaten geprüft
- [ ] Debug-Logging für Koordinaten hinzugefügt
- [ ] Test durchgeführt: Echte Straßenrouten werden angezeigt
- [ ] LESSONS_LOG.md aktualisiert (falls neuer Fehlertyp)

---

**Projekt:** FAMO TrafficApp 3.0  
**Stack:** Python 3.10, FastAPI, Vanilla JS, SQLite  
**Stand:** {datetime.now().strftime('%Y-%m-%d')}  
**Audit-Paket:** `{zip_name}`
"""
    
    readme_path = output_path.parent / f'README_POLYLINE_AUDIT_{datetime.now().strftime("%Y%m%d")}.md'
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"[OK] README erstellt: {readme_path}")

if __name__ == '__main__':
    # Erstelle Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_name = f'POLYLINE_FEHLER_AUDIT_{timestamp}.zip'
    zip_path = PROJECT_ROOT / 'ZIP' / zip_name
    
    # Erstelle ZIP-Verzeichnis falls nicht vorhanden
    zip_path.parent.mkdir(exist_ok=True)
    
    # Erstelle ZIP
    create_polyline_audit_zip(zip_path)
    
    # Erstelle README
    create_polyline_readme(zip_path)
    
    print()
    print("=" * 60)
    print("[OK] POLYLINE-AUDIT-PAKET ERSTELLT")
    print("=" * 60)
    print(f"[ZIP] Datei: {zip_path}")
    print(f"[DOC] README: ZIP/README_POLYLINE_AUDIT_*.md")
    print()
    print("Naechste Schritte:")
    print("1. ZIP entpacken und analysieren")
    print("2. README lesen für Kontext")
    print("3. Fehler fixen und testen")

