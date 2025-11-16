# 🧠 KI-Lernpfad: Integrierter Laufplan

**Datum:** 2025-11-16  
**Status:** 📋 ENTWURF  
**Version:** 1.0

---

## 🎯 Ziel

Ein **integrierter Laufplan**, der:
- ✅ Alle drei KI-Lernkanäle systematisch nutzt
- ✅ Die normalen Programm-Abläufe **nicht stört**
- ✅ Die KI mit allen verfügbaren Informationen versorgt
- ✅ Automatisch und non-blocking läuft

---

## 📚 Die drei KI-Lernkanäle

### 1. **Code-Audit-Kanal** (Bestehend)
**Quelle:** Manuelle Audit-ZIPs + Code-Dateien  
**Zweck:** Direkte Code-Analyse durch Cursor  
**Format:** ZIP-Dateien mit Code + Kontext

**Aktueller Stand:**
- ✅ Audit-ZIPs werden manuell erstellt
- ✅ Cursor analysiert Code direkt
- ⏳ Keine automatische Integration

---

### 2. **Runtime-Error-Kanal** (Neu implementiert)
**Quelle:** `error_events` + `error_patterns` (Datenbank)  
**Zweck:** Lernen aus echten Laufzeit-Fehlern  
**Format:** Strukturierte Patterns mit Events + Feedback

**Aktueller Stand:**
- ✅ Error-Events werden automatisch erfasst
- ✅ Patterns werden automatisch gruppiert
- ✅ API-Endpoints verfügbar
- ⏳ KI-Integration noch nicht vollständig

---

### 3. **Lessons-/Standards-Kanal** (Bestehend)
**Quelle:** `ERROR_CATALOG.md`, `LESSONS_LOG.md`, `STANDARDS.md`  
**Zweck:** Gelerntes Wissen festhalten und wiederverwenden  
**Format:** Markdown-Dokumente

**Aktueller Stand:**
- ✅ Dokumente existieren
- ✅ AI Code Checker lädt sie bereits
- ✅ Werden bei Code-Analysen verwendet
- ⏳ Automatische Updates fehlen

---

## 🔄 Integrierter Laufplan

### Phase 1: Daten-Sammlung (Automatisch, Non-Blocking)

#### 1.1 Runtime-Error-Sammlung
**Wann:** Bei jedem Request (automatisch)  
**Was:** Fehler-Events + Erfolgs-Statistiken  
**Wo:** `error_events`, `success_stats` (Datenbank)

**Implementierung:**
- ✅ Error-Handler loggt automatisch
- ✅ Middleware loggt Erfolge
- ✅ Non-blocking (Fehler beim Logging killen Request nicht)

#### 1.2 Pattern-Aggregation
**Wann:** Alle 5 Minuten (Hintergrund-Job)  
**Was:** Events zu Patterns gruppieren  
**Wo:** `error_patterns` (Datenbank)

**Implementierung:**
- ✅ Aggregator-Service läuft im Hintergrund
- ✅ Non-blocking
- ✅ Automatisch

#### 1.3 Lessons-/Standards-Updates
**Wann:** Manuell oder halbautomatisch  
**Was:** Neue Erkenntnisse in Dokumente schreiben  
**Wo:** `ERROR_CATALOG.md`, `LESSONS_LOG.md`

**Aktueller Stand:**
- ✅ Manuell möglich
- ⏳ Automatische Updates fehlen

---

### Phase 2: KI-Feed-Generierung (Periodisch, Non-Blocking)

#### 2.1 Error-Pattern-Feed
**Wann:** Täglich oder bei Bedarf  
**Was:** Neue/Offene Patterns für KI aufbereiten  
**Format:** Strukturierte JSON/Text-Datei

**Inhalt:**
- Pattern-Details (Signatur, Occurrences, Status)
- Repräsentative Events (Stacktraces, Payloads)
- Feedback-Historie
- Verknüpfte Code-Stellen

#### 2.2 Lessons-/Standards-Feed
**Wann:** Bei Änderungen  
**Was:** Aktualisierte Dokumente für KI  
**Format:** Markdown-Dateien (bereits vorhanden)

**Aktueller Stand:**
- ✅ Dokumente werden bereits geladen
- ✅ AI Code Checker nutzt sie

#### 2.3 Code-Audit-Feed
**Wann:** Bei Bedarf (manuell oder automatisch)  
**Was:** Relevante Code-Stellen für Pattern-Analyse  
**Format:** ZIP-Dateien oder strukturierte Code-Snippets

**Aktueller Stand:**
- ✅ Manuell möglich
- ⏳ Automatische Generierung fehlt

---

### Phase 3: KI-Analyse (On-Demand oder Periodisch)

#### 3.1 Pattern-Analyse
**Trigger:** Neues Pattern mit > 10 Occurrences  
**Was:** KI analysiert Pattern + Events + Code  
**Output:** Root-Cause-Analyse + Fix-Vorschlag

**Workflow:**
1. Pattern wird identifiziert (Aggregator)
2. KI-Feed wird generiert (Pattern + Events + Code)
3. Cursor-Prompt wird erstellt
4. KI analysiert
5. Feedback wird gespeichert

#### 3.2 Code-Audit
**Trigger:** Manuell oder bei größeren Änderungen  
**Was:** KI analysiert Code direkt  
**Output:** Verbesserungsvorschläge

**Aktueller Stand:**
- ✅ AI Code Checker existiert
- ✅ Nutzt ERROR_CATALOG + LESSONS_LOG
- ⏳ Nutzt noch keine Error-Patterns

#### 3.3 Lessons-Update
**Trigger:** Nach erfolgreichem Fix  
**Was:** KI erstellt LESSONS_LOG-Eintrag  
**Output:** Dokumentierter Fix + Lessons Learned

**Aktueller Stand:**
- ✅ Manuell möglich
- ⏳ Automatisch fehlt

---

### Phase 4: Feedback-Loop (Automatisch)

#### 4.1 Fix-Implementierung
**Was:** Dev/KI implementiert Fix  
**Wo:** Code-Änderungen

#### 4.2 Pattern-Status-Update
**Was:** Pattern wird als "fixed" markiert  
**Wo:** `error_patterns.status = 'fixed'`

#### 4.3 Monitoring
**Was:** Prüft ob Pattern wirklich fixed ist  
**Wo:** Aggregator prüft auf neue Events

#### 4.4 Lessons-Dokumentation
**Was:** LESSONS_LOG wird aktualisiert  
**Wo:** `Regeln/LESSONS_LOG.md`

---

## 🏗️ Technische Umsetzung

### Service: KI-Lernpfad-Koordinator

**Datei:** `backend/services/ki_learning_coordinator.py`

**Aufgaben:**
1. **Daten-Sammlung koordinieren**
   - Error-Patterns aus DB holen
   - Lessons-/Standards-Dokumente laden
   - Code-Audit-Daten sammeln

2. **KI-Feed generieren**
   - Strukturierte Feed-Datei erstellen
   - Alle drei Kanäle kombinieren
   - Für Cursor aufbereiten

3. **KI-Analyse triggern**
   - Bei neuen Patterns
   - Bei Code-Änderungen
   - Periodisch (optional)

4. **Feedback-Loop verwalten**
   - Fix-Status tracken
   - Lessons-Updates koordinieren
   - Monitoring

---

### API-Endpoints: KI-Lernpfad

**Datei:** `backend/routes/ki_learning_api.py`

**Endpoints:**
- `GET /api/ki-learning/feed` - Generiert KI-Feed (alle drei Kanäle)
- `GET /api/ki-learning/patterns` - Neue/Offene Patterns für KI
- `POST /api/ki-learning/analyze-pattern/{id}` - Triggert KI-Analyse für Pattern
- `GET /api/ki-learning/status` - Status aller drei Kanäle

---

### Integration: AI Code Checker erweitern

**Datei:** `backend/services/ai_code_checker.py`

**Erweiterungen:**
1. **Error-Patterns laden**
   - Neue Patterns aus DB holen
   - Als Kontext für Code-Analyse nutzen

2. **KI-Feed integrieren**
   - Feed-Datei laden
   - Bei Code-Analysen berücksichtigen

3. **Feedback speichern**
   - KI-Analysen als Feedback speichern
   - Pattern-Status aktualisieren

---

## 📋 Laufplan-Details

### Täglicher Zyklus

**00:00 Uhr - Pattern-Aggregation**
- Aggregator läuft (alle 5 Min, kontinuierlich)
- Neue Patterns werden erkannt

**01:00 Uhr - KI-Feed-Generierung**
- Feed wird generiert (alle drei Kanäle)
- Neue Patterns werden aufbereitet

**02:00 Uhr - KI-Analyse (Optional)**
- Automatische Analyse neuer Patterns
- Nur bei kritischen Patterns (> 10 Occurrences)

**Täglich - Lessons-Update**
- Erfolgreiche Fixes werden dokumentiert
- LESSONS_LOG wird aktualisiert

---

### On-Demand-Trigger

**Bei neuem Pattern:**
1. Pattern wird erkannt (Aggregator)
2. KI-Feed wird generiert
3. Dev/KI wird benachrichtigt (optional)
4. Analyse kann gestartet werden

**Bei Code-Änderungen:**
1. Code wird geändert
2. AI Code Checker analysiert
3. Nutzt alle drei Kanäle als Kontext
4. Verbesserungsvorschläge

**Bei erfolgreichem Fix:**
1. Pattern-Status wird auf "fixed" gesetzt
2. Monitoring prüft (keine neuen Events)
3. LESSONS_LOG wird aktualisiert
4. Standards werden angepasst (optional)

---

## 🔧 Implementierungs-Plan

### Schritt 1: KI-Lernpfad-Koordinator (Service)

**Datei:** `backend/services/ki_learning_coordinator.py`

**Funktionen:**
- `generate_ki_feed()` - Generiert Feed aus allen drei Kanälen
- `get_new_patterns()` - Holt neue/offene Patterns
- `trigger_pattern_analysis()` - Triggert KI-Analyse
- `update_lessons_from_fix()` - Aktualisiert LESSONS_LOG

### Schritt 2: API-Endpoints

**Datei:** `backend/routes/ki_learning_api.py`

**Endpoints:**
- `GET /api/ki-learning/feed` - KI-Feed
- `GET /api/ki-learning/patterns` - Patterns für KI
- `POST /api/ki-learning/analyze-pattern/{id}` - Analyse triggern
- `GET /api/ki-learning/status` - Status

### Schritt 3: AI Code Checker erweitern

**Datei:** `backend/services/ai_code_checker.py`

**Erweiterungen:**
- Error-Patterns als Kontext laden
- KI-Feed integrieren
- Feedback speichern

### Schritt 4: Cursor-Prompt-Templates erweitern

**Datei:** `Regeln/CURSOR_PROMPT_TEMPLATE.md`

**Neue Templates:**
- Template #15: "Analysiere Pattern mit allen drei Kanälen"
- Template #16: "KI-Feed generieren und analysieren"

### Schritt 5: Automatische Lessons-Updates (Optional)

**Datei:** `backend/services/lessons_updater.py`

**Funktionen:**
- Automatisch LESSONS_LOG-Einträge erstellen
- Bei erfolgreichen Fixes
- Mit Pattern-Verknüpfung

---

## ✅ Garantien (Non-Blocking)

### 1. Daten-Sammlung
- ✅ **Non-Blocking:** Fehler beim Logging killen Request nicht
- ✅ **Asynchron:** Aggregator läuft im Hintergrund
- ✅ **Resilient:** Fehler werden geloggt, aber nicht propagiert

### 2. KI-Feed-Generierung
- ✅ **Non-Blocking:** Läuft im Hintergrund
- ✅ **Optional:** Kann manuell getriggert werden
- ✅ **Cached:** Feed wird gecacht, nicht bei jedem Request neu generiert

### 3. KI-Analyse
- ✅ **On-Demand:** Wird nicht automatisch bei jedem Request ausgelöst
- ✅ **Optional:** Kann deaktiviert werden
- ✅ **Non-Blocking:** Läuft asynchron

### 4. Lessons-Updates
- ✅ **Manuell:** Primär manuell
- ✅ **Optional:** Automatische Updates können deaktiviert werden
- ✅ **Non-Blocking:** Läuft im Hintergrund

---

## 📊 Monitoring

### Status-Dashboard

**Endpoint:** `GET /api/ki-learning/status`

**Output:**
```json
{
  "code_audit_kanal": {
    "status": "active",
    "last_audit": "2025-11-16T10:00:00",
    "audits_count": 42
  },
  "runtime_error_kanal": {
    "status": "active",
    "patterns_total": 15,
    "patterns_open": 8,
    "events_total": 234,
    "last_aggregation": "2025-11-16T10:05:00"
  },
  "lessons_standards_kanal": {
    "status": "active",
    "lessons_count": 25,
    "standards_count": 50,
    "last_update": "2025-11-16T09:00:00"
  }
}
```

---

## 🎯 Nächste Schritte

### Sofort (kritisch)

1. ✅ **KI-Lernpfad-Koordinator implementieren**
2. ✅ **API-Endpoints erstellen**
3. ✅ **AI Code Checker erweitern**

### Kurzfristig (wichtig)

1. ⏳ **Cursor-Prompt-Templates erweitern**
2. ⏳ **KI-Feed-Generierung implementieren**
3. ⏳ **Status-Dashboard erstellen**

### Langfristig (optional)

1. ⏳ **Automatische Lessons-Updates**
2. ⏳ **Automatische Pattern-Analyse**
3. ⏳ **Monitoring-Alerts**

---

**Erstellt:** 2025-11-16  
**Status:** 📋 **ENTWURF**  
**Nächste Schritte:** Implementierung starten

