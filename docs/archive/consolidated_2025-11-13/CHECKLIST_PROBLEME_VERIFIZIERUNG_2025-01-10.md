# Checkliste: Probleme Verifizierung und Test-Plan
**Datum:** 2025-01-10  
**Zweck:** Systematische Überprüfung aller identifizierten Probleme  
**Status:** 🔄 IN ARBEIT

---

## 📋 VORBEREITUNG

### Setup-Schritte
- [ ] Server neu starten (`python start_server.py`)
- [ ] Browser-Cache leeren (Strg+F5 oder Entwicklertools → Network → "Disable cache")
- [ ] Browser-Konsole öffnen (F12 → Console-Tab)
- [ ] Network-Tab öffnen (F12 → Network-Tab, Filter: "Fetch/XHR")

---

## 🔴 KRITISCHE PROBLEME

### 1. Upload-Funktionalität funktioniert nicht
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** KRITISCH  
**Dateien:** `frontend/index.html`, `routes/upload_csv.py`

#### Test-Schritte:
- [ ] **Test 1.1:** CSV-Datei auswählen
  - [ ] Datei-Input-Feld funktioniert
  - [ ] Datei wird ausgewählt
  - [ ] Upload-Status wird angezeigt ("Lade hoch: ...")

- [ ] **Test 1.2:** Upload durchführen
  - [ ] Upload startet automatisch nach Datei-Auswahl
  - [ ] Upload-Status zeigt Fortschritt
  - [ ] Keine Fehler in Browser-Konsole
  - [ ] Upload-Status zeigt "Upload erfolgreich: [Dateiname]"

- [ ] **Test 1.3:** Backend-Verarbeitung
  - [ ] Datei wird in `./data/staging` gespeichert
  - [ ] Datei hat korrekten Namen (Timestamp_Dateiname.csv)
  - [ ] Datei ist UTF-8 kodiert
  - [ ] Server-Logs zeigen keine Fehler

- [ ] **Test 1.4:** Match startet automatisch
  - [ ] Nach Upload startet automatisch Match
  - [ ] Match-Status wird angezeigt
  - [ ] Match-Response kommt vom Server (200 OK)

#### Erwartetes Ergebnis:
✅ Upload funktioniert einwandfrei, Datei wird gespeichert, Match startet automatisch

#### Bei Fehlern prüfen:
- Browser-Konsole auf Fehler
- Network-Tab: `/api/upload/csv` Request prüfen
- Server-Logs auf `[UPLOAD ERROR]` prüfen
- Prüfen ob `uploadInfo` und `workflowStatus` DOM-Elemente existieren

---

### 2. Status-Indikatoren werden nicht grün
**Status:** ⚠️ TEILWEISE BEHOBEN  
**Priorität:** HOCH  
**Dateien:** `frontend/index.html`, `routes/health_check.py`

#### 2.1 DB-Status
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)

##### Test-Schritte:
- [ ] **Test 2.1.1:** DB-Status-Endpoint prüfen
  - [ ] Browser-Konsole: `fetch('/health/db').then(r => r.json()).then(console.log)`
  - [ ] Response: `{status: "online", tables: [...], table_count: X}`
  - [ ] HTTP-Status: 200 OK
  - [ ] `tables` ist ein Array (nicht String)

- [ ] **Test 2.1.2:** DB-Status in UI prüfen
  - [ ] Status-Indikator zeigt "DB online (X Tabellen)" (grün)
  - [ ] Icon ist grün (`text-success`)
  - [ ] Status wird beim Seitenladen aktualisiert

##### Erwartetes Ergebnis:
✅ DB-Status zeigt grün: "DB online (17 Tabellen)"

#### 2.2 LLM-Status
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)

##### Test-Schritte:
- [ ] **Test 2.2.1:** LLM-Status-Endpoint prüfen
  - [ ] Browser-Konsole: `fetch('/api/workflow/status').then(r => r.json()).then(console.log)`
  - [ ] Response enthält: `{llm_status: "...", llm_model: "...", workflow_engine: "..."}`
  - [ ] HTTP-Status: 200 OK

- [ ] **Test 2.2.2:** LLM-Status in UI prüfen
  - [ ] Status-Indikator zeigt "LLM OpenAI (konfiguriert)" oder ähnlich (grün)
  - [ ] Icon ist grün (`text-success`)
  - [ ] Status wird beim Seitenladen aktualisiert

##### Erwartetes Ergebnis:
✅ LLM-Status zeigt grün: "LLM OpenAI (konfiguriert)" oder "LLM [Model]"

#### 2.3 OSRM-Status
**Status:** ❌ OFFEN - Endpoint gibt 404

##### Test-Schritte:
- [ ] **Test 2.3.1:** Server neu starten
  - [ ] Server stoppen (Ctrl+C)
  - [ ] Server neu starten (`python start_server.py`)
  - [ ] Server startet ohne Fehler

- [ ] **Test 2.3.2:** OSRM-Status-Endpoint prüfen
  - [ ] Browser-Konsole: `fetch('/health/osrm').then(r => r.json()).then(console.log)`
  - [ ] HTTP-Status: 200 OK (nicht 404!)
  - [ ] Response: `{status: "ok" oder "down", url: "...", message: "..."}`

- [ ] **Test 2.3.3:** OSRM-Status in UI prüfen
  - [ ] Status-Indikator zeigt "OSRM online" (grün) oder "OSRM offline" (rot)
  - [ ] Icon ist grün (`text-success`) oder rot (`text-danger`)
  - [ ] Status wird beim Seitenladen aktualisiert

##### Erwartetes Ergebnis:
✅ OSRM-Status zeigt grün: "OSRM online" (wenn OSRM erreichbar) oder rot: "OSRM offline" (wenn nicht erreichbar)

##### Bei 404-Fehler prüfen:
- Router-Registrierung in `backend/app.py` prüfen
- `routes/health_check.py` prüfen ob Endpoint existiert
- Server-Logs auf Import-Fehler prüfen

---

### 3. Tour-Übersicht bleibt leer nach Workflow
**Status:** ⚠️ TEILWEISE BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** HOCH  
**Dateien:** `frontend/index.html`, `routes/workflow_api.py`

#### Test-Schritte:
- [ ] **Test 3.1:** Workflow ausführen
  - [ ] CSV-Datei hochladen
  - [ ] "Kompletter Workflow" Button klicken
  - [ ] Workflow-Status zeigt Fortschritt
  - [ ] Workflow wird erfolgreich abgeschlossen

- [ ] **Test 3.2:** Tour-Übersicht prüfen
  - [ ] Tour-Übersicht zeigt Touren (nicht "Noch keine Tourdaten")
  - [ ] Anzahl der Touren ist korrekt
  - [ ] Tour-Namen werden angezeigt
  - [ ] Anzahl der Stopps pro Tour wird angezeigt

- [ ] **Test 3.3:** Tour-Details prüfen
  - [ ] Klick auf Tour funktioniert
  - [ ] Tour-Details werden rechts angezeigt
  - [ ] Karte zeigt Route
  - [ ] Stopps werden auf Karte angezeigt

- [ ] **Test 3.4:** Browser-Konsole prüfen
  - [ ] Keine Fehler in Console
  - [ ] `renderToursFromMatch` wird aufgerufen
  - [ ] Workflow-Response enthält `tours` Array

#### Erwartetes Ergebnis:
✅ Tour-Übersicht zeigt alle Touren nach erfolgreichem Workflow

#### Bei Fehlern prüfen:
- Browser-Konsole auf `renderToursFromMatch` Aufruf
- Workflow-Response-Struktur prüfen (`tours` vs `customers`)
- Network-Tab: `/api/workflow/upload` Response prüfen

---

### 4. Routing-Fehler: 0.0 Min Fahrt, fehlende Distanzen
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** HOCH  
**Dateien:** `routes/workflow_api.py`, `common/normalize.py`

#### Test-Schritte:
- [ ] **Test 4.1:** Tour-Details öffnen
  - [ ] Tour aus Liste auswählen
  - [ ] Tour-Details werden angezeigt
  - [ ] Route-Details werden geladen

- [ ] **Test 4.2:** Fahrtdauer prüfen
  - [ ] Fahrtdauer wird angezeigt (nicht "0.0 Min")
  - [ ] Fahrtdauer ist > 0 für alle Segmente
  - [ ] Fahrtdauer ist realistisch (nicht zu hoch)

- [ ] **Test 4.3:** Distanzen prüfen
  - [ ] Distanzen werden angezeigt (nicht "-")
  - [ ] Distanzen sind > 0 für alle Segmente
  - [ ] Distanzen sind realistisch

- [ ] **Test 4.4:** Duplikat-Erkennung prüfen
  - [ ] Duplikat-Warnungen werden angezeigt (falls vorhanden)
  - [ ] Identische Koordinaten werden erkannt
  - [ ] Minimale Distanz (10 Meter) wird für Duplikate verwendet

#### Erwartetes Ergebnis:
✅ Fahrtdauer und Distanzen werden korrekt angezeigt, Duplikate werden erkannt

#### Bei Fehlern prüfen:
- Browser-Konsole auf Route-Details-Response
- Network-Tab: `/api/tour/route-details` Response prüfen
- Server-Logs auf Duplikat-Erkennung

---

### 5. Sub-Touren werden nicht angezeigt
**Status:** ⚠️ TEILWEISE BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** MITTEL  
**Dateien:** `frontend/index.html`, `routes/workflow_api.py`

#### Test-Schritte:
- [ ] **Test 5.1:** Sub-Touren generieren
  - [ ] Tour mit > 30 Stopps auswählen
  - [ ] Sub-Routen Generator starten
  - [ ] Sub-Touren werden generiert

- [ ] **Test 5.2:** Sub-Touren in UI prüfen
  - [ ] Alle Sub-Touren werden in Liste angezeigt
  - [ ] Nicht nur die erste Route, sondern alle 5-6 Routen
  - [ ] Sub-Tour-Namen werden angezeigt
  - [ ] Anzahl der Stopps pro Sub-Tour wird angezeigt

- [ ] **Test 5.3:** Sub-Tour-Details prüfen
  - [ ] Klick auf Sub-Tour funktioniert
  - [ ] Sub-Tour-Details werden angezeigt
  - [ ] Karte zeigt Sub-Tour-Route
  - [ ] Stopps der Sub-Tour werden auf Karte angezeigt

- [ ] **Test 5.4:** Browser-Konsole prüfen
  - [ ] Keine Fehler in Console
  - [ ] `sub_tours` Array wird verarbeitet
  - [ ] Alle Sub-Touren werden gerendert

#### Erwartetes Ergebnis:
✅ Alle Sub-Touren werden in der UI angezeigt und sind klickbar

#### Bei Fehlern prüfen:
- Browser-Konsole auf `sub_tours` Verarbeitung
- Network-Tab: `/api/tour/optimize` Response prüfen
- Prüfen ob `allTourCustomers` korrekt befüllt wird

---

## 🟡 MITTLERE PROBLEME

### 6. Button-Layout: Buttons nicht nebeneinander
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** NIEDRIG

#### Test-Schritte:
- [ ] **Test 6.1:** Button-Layout prüfen
  - [ ] "Karte abdocken" und "Touren abdocken" sind nebeneinander
  - [ ] "Blitzer ausblenden" und "Hindernisse einblenden" sind nebeneinander
  - [ ] Buttons haben jeweils 50% Breite
  - [ ] Buttons sind in zwei Zeilen

#### Erwartetes Ergebnis:
✅ Buttons sind nebeneinander in zwei Zeilen angeordnet

---

### 7. Live-Daten: Blitzer und Hindernisse nicht angezeigt
**Status:** ✅ IMPLEMENTIERT (Code vorhanden)  
**Priorität:** MITTEL

#### Test-Schritte:
- [ ] **Test 7.1:** Route auf Karte anzeigen
  - [ ] Tour auswählen
  - [ ] Route wird auf Karte angezeigt
  - [ ] Route-Details werden geladen

- [ ] **Test 7.2:** Blitzer prüfen
  - [ ] Blitzer-Marker werden auf Karte angezeigt (falls vorhanden)
  - [ ] Blitzer-Info-Banner wird angezeigt
  - [ ] "Blitzer ausblenden" Button funktioniert
  - [ ] Blitzer werden ausgeblendet/eingeblendet

- [ ] **Test 7.3:** Hindernisse prüfen
  - [ ] Hindernis-Marker werden auf Karte angezeigt (falls vorhanden)
  - [ ] Hindernis-Info-Banner wird angezeigt
  - [ ] "Hindernisse einblenden" Button funktioniert
  - [ ] Hindernisse werden ausgeblendet/eingeblendet

- [ ] **Test 7.4:** Browser-Konsole prüfen
  - [ ] Keine Fehler in Console
  - [ ] `speed_cameras` und `traffic_incidents` werden verarbeitet
  - [ ] Marker werden erstellt

#### Erwartetes Ergebnis:
✅ Blitzer und Hindernisse werden auf Karte angezeigt, Toggle-Buttons funktionieren

---

### 8. Staging-Verzeichnis: Daten türmen sich auf
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** MITTEL

#### Test-Schritte:
- [ ] **Test 8.1:** Staging-Verzeichnis prüfen
  - [ ] `./data/staging` Verzeichnis existiert
  - [ ] Anzahl der Dateien ist < 100
  - [ ] Alte Dateien (> 24 Stunden) wurden gelöscht

- [ ] **Test 8.2:** Cleanup-Funktion prüfen
  - [ ] Upload einer neuen Datei
  - [ ] Cleanup wird nach Upload ausgeführt (wenn > 100 Dateien)
  - [ ] Server-Logs zeigen Cleanup-Meldungen

#### Erwartetes Ergebnis:
✅ Staging-Verzeichnis wird automatisch bereinigt

---

## 🤖 KI-CODECHECKER (Noch nicht implementiert)

### 10. KI-CodeChecker System
**Status:** 📋 PLANUNG - Noch nicht implementiert  
**Priorität:** HOCH  
**Dateien:** `backend/services/code_checker.py` (muss erstellt werden)

#### Test-Schritte:
- [ ] **Test 10.1:** Code-Checker ausführen
  - [ ] `python scripts/run_code_check.py` ausführen
  - [ ] Code-Checker prüft alle relevanten Dateien
  - [ ] Report wird generiert (`docs/CODE_CHECK_REPORT.md`)
  - [ ] Keine kritischen Fehler gefunden

- [ ] **Test 10.2:** KI-Prüfung durchführen (Phase 2)
  - [ ] KI-Checker ist konfiguriert
  - [ ] KI prüft Code auf Fehler und Best Practices
  - [ ] KI findet bekannte Probleme
  - [ ] Fix-Vorschläge sind hilfreich

- [ ] **Test 10.3:** Integration in Workflow (Phase 3)
  - [ ] Pre-Commit-Hook funktioniert
  - [ ] Automatische Prüfung bei Code-Änderungen
  - [ ] CI/CD-Integration funktioniert

#### Erwartetes Ergebnis:
✅ KI-CodeChecker prüft automatisch Code und findet Probleme

#### Implementierungsstatus:
- [ ] Phase 1: Code-Analyzer (Grundlagen)
- [ ] Phase 2: KI-Integration
- [ ] Phase 3: Workflow-Integration

**Details:** Siehe `docs/KI_CODECHECKER_KONZEPT_2025-01-10.md`

---

## 🟢 NIEDRIGE PROBLEME

### 9. Browser-Cache: Änderungen werden nicht übernommen
**Status:** ✅ BEHOBEN (Code-Änderungen implementiert)  
**Priorität:** NIEDRIG

#### Test-Schritte:
- [ ] **Test 9.1:** Cache-Header prüfen
  - [ ] Browser-Konsole: Network-Tab öffnen
  - [ ] Request zu `/` oder `/ui/` prüfen
  - [ ] Response-Header enthalten `Cache-Control: no-cache, no-store, must-revalidate`

#### Erwartetes Ergebnis:
✅ Cache-Header sind korrekt gesetzt

---

## 📊 ZUSAMMENFASSUNG

### Test-Status
- **Gesamt-Tests:** 25 Tests
- **Kritische Tests:** 15 Tests
- **Mittlere Tests:** 7 Tests
- **Niedrige Tests:** 3 Tests

### Erwartete Ergebnisse
- ✅ **Behoben:** 6 Probleme (Upload, DB-Status, LLM-Status, Routing-Fehler, Button-Layout, Staging)
- ⚠️ **Teilweise behoben:** 3 Probleme (OSRM-Status, Tour-Übersicht, Sub-Touren)
- ✅ **Implementiert:** 1 Problem (Live-Daten)

### Nächste Schritte nach Tests
1. Alle Tests durchführen
2. Fehler dokumentieren
3. Offene Probleme beheben
4. Erneut testen

---

## 🔧 DEBUGGING-TIPPS

### Browser-Konsole
- F12 → Console-Tab öffnen
- Nach Fehlern suchen (rot markiert)
- `[UPLOAD]`, `[STATUS]`, `[WORKFLOW]` Logs prüfen

### Network-Tab
- F12 → Network-Tab öffnen
- Filter: "Fetch/XHR"
- Requests prüfen:
  - `/api/upload/csv` → Upload
  - `/health/db` → DB-Status
  - `/health/osrm` → OSRM-Status
  - `/api/workflow/status` → LLM-Status
  - `/api/workflow/upload` → Workflow
  - `/api/tour/route-details` → Route-Details

### Server-Logs
- Server-Terminal prüfen
- Nach `[ERROR]`, `[WARNING]` suchen
- `[UPLOAD ERROR]`, `[STATUS]` Logs prüfen

---

**Erstellt:** 2025-01-10  
**Letzte Aktualisierung:** 2025-01-10  
**Nächste Überprüfung:** Nach Test-Durchführung

