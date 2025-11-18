# Cursor-Dokumentations-Update-Template

**Version:** 1.0  
**Stand:** 2025-11-16  
**Zweck:** Standard-Prompt für Cursor, um Dokumentation nach Code-Änderungen zu aktualisieren

---

## Standard-Prompt für Doku-Update

**Kopiere diesen Prompt in Cursor, wenn Code-Änderungen die Architektur betreffen:**

```markdown
# Dokumentations-Update erforderlich

Ich habe Code-Änderungen vorgenommen, die die Architektur betreffen. Bitte aktualisiere die Dokumentation gezielt.

## Änderungen (Diff)

[HIER: Beschreibe die Änderungen oder füge `git diff HEAD~1..HEAD` ein]

## Betroffene Bereiche

- [ ] Routing / OSRM-Anbindung
- [ ] Touren-Workflow (neuer Schritt, neue Queue)
- [ ] Infrastruktur (Container-IP, Ports, Docker vs. LXC)
- [ ] Hauptmodule (neue Services, neue Routen)
- [ ] Frontend-Komponenten
- [ ] API-Endpoints

## Zu aktualisierende Dateien

1. **`docs/ARCHITEKTUR_KOMPLETT.md`**
   - [ ] Systemübersicht (Abschnitt 1️⃣)
   - [ ] Touren-Workflow (Abschnitt 2️⃣)
   - [ ] Routing-Stack (Abschnitt 3️⃣)
   - [ ] Module & Verantwortung (Abschnitt 4️⃣)
   - [ ] Infra & Ports (Abschnitt 5️⃣)

2. **`MODULE_MAP.md`**
   - [ ] Neue Module hinzufügen
   - [ ] Abhängigkeiten aktualisieren
   - [ ] Kommunikations-Flows erweitern
   - [ ] Status aktualisieren (stabil/experimentell/deprecated)

3. **`PROJECT_PROFILE.md`** (falls nötig)
   - [ ] Infrastruktur-Abschnitt
   - [ ] Module-Übersicht

4. **`docs/STATUS_AKTUELL.md`** (falls nötig)
   - [ ] Neue Erreichungen dokumentieren

## Regeln

- ✅ **Nur betroffene Abschnitte** ändern (keine komplette Doku umschreiben)
- ✅ **Datum im Header** aktualisieren
- ✅ **Version** erhöhen (falls größere Änderungen)
- ✅ **Stil beibehalten** (keine Stilbrüche)
- ❌ **Keine neuen Strukturen** erfinden (ohne explizite Freigabe)

## Checkliste nach Update

- [ ] Datum im Header aktualisiert
- [ ] Version erhöht (falls nötig)
- [ ] Betroffene Abschnitte aktualisiert
- [ ] MODULE_MAP.md aktualisiert (falls Module betroffen)
- [ ] Keine Stilbrüche eingeführt
- [ ] Links funktionieren noch
```

---

## Beispiel: Routing-Änderung

```markdown
# Dokumentations-Update: OSRM-Client erweitert

## Änderungen

- `services/osrm_client.py`: Neue Methode `get_distance_matrix()` hinzugefügt
- `backend/routes/workflow_api.py`: Nutzt jetzt `get_distance_matrix()` statt einzelner Route-Calls

## Betroffene Bereiche

- [x] Routing / OSRM-Anbindung
- [ ] Touren-Workflow
- [ ] Infrastruktur
- [x] Hauptmodule (osrm_client Service)

## Zu aktualisierende Dateien

1. **`MODULE_MAP.md`**
   - [x] `osrm_client` Service: Neue Methode dokumentieren
   - [x] Kommunikations-Flow "Touren-Workflow" aktualisieren

2. **`docs/ARCHITEKTUR_KOMPLETT.md`**
   - [x] Abschnitt 3️⃣ (Routing-Stack): `get_distance_matrix()` erwähnen
   - [x] Abschnitt 2️⃣ (Touren-Workflow): Flow aktualisieren
```

---

## Beispiel: Neues Modul

```markdown
# Dokumentations-Update: Neuer Service `tour_validator.py`

## Änderungen

- Neuer Service: `backend/services/tour_validator.py`
- Wird genutzt von: `workflow_api.py`
- Nutzt: `geo_repo`, `osrm_client`

## Betroffene Bereiche

- [x] Hauptmodule (neuer Service)

## Zu aktualisierende Dateien

1. **`MODULE_MAP.md`**
   - [x] Neue Zeile für `tour_validator` hinzufügen
   - [x] Kommunikations-Flow "Touren-Workflow" erweitern

2. **`docs/ARCHITEKTUR_KOMPLETT.md`**
   - [x] Abschnitt 4️⃣ (Module & Verantwortung): `tour_validator` hinzufügen
   - [x] Abschnitt 2️⃣ (Touren-Workflow): Validierungsschritt dokumentieren
```

---

## Automatische Prüfung (Optional)

**Cursor kann prüfen:**

1. **Module-Consistency-Check:**
   - Jedes Modul im Code soll in `MODULE_MAP.md` vorkommen (oder als intern markiert sein)

2. **Infra-Check:**
   - OSRM-Host/Port in Doku == real verwendete Config (`.env`, `osrm_client`)

3. **Endpoint-Check:**
   - Alle Endpoints in `backend/app.py` sollten in `ARCHITEKTUR_KOMPLETT.md` erwähnt sein (oder als intern markiert)

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-16  
**Projekt:** FAMO TrafficApp 3.0

📝 **Template für nachvollziehbare Dokumentations-Updates**

