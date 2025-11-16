# 🧠 KI-Lernpfad: Error-Learning-System

**Datum:** 2025-11-16  
**Status:** ✅ IMPLEMENTIERT  
**Version:** 1.0

---

## 📋 Übersicht

Das Error-Learning-System erfasst automatisch alle Fehler-Ereignisse (negatives Logging) und erfolgreiche Requests (positives Logging), gruppiert sie zu Patterns und stellt sie der KI (Cursor) als Lernbasis zur Verfügung.

**Zweck:**
- **Automatisches Lernen** aus Laufzeitverhalten
- **Fehlerkatalog** der sich selbst füllt
- **KI-Lernpfad** für bessere Fixes und Regeln
- **Brücke** zwischen Code → Laufzeit → Fehler → KI → Fix → Standards

---

## 🏗️ Architektur

### Datenfluss

```
1. Request/Event passiert (Frontend oder Backend)
   ↓
2. Backend verarbeitet:
   - Erfolg → positives Event loggen (success_stats)
   - Fehler → negatives Event loggen (error_events)
   ↓
3. Error-Logger schreibt in:
   - klassische Logs (rotate)
   - Datenbank-Tabellen (error_events, success_stats)
   ↓
4. Aggregator-Job (alle 5 Min) fasst Events zu Patterns zusammen
   ↓
5. KI-Feed nimmt Patterns + Kontext und erzeugt Vorschläge
   ↓
6. Lessons-Log / Standards werden aktualisiert
```

---

## 📊 Datenbank-Schema

### Tabelle: `error_events`

Rohdaten aller Fehler-Ereignisse.

**Wichtige Spalten:**
- `id` (PK)
- `timestamp`
- `trace_id` (verknüpft zu Trace-Logging)
- `endpoint` (z.B. `/api/tour/route-details`)
- `http_method`
- `status_code` (z.B. 500, 422, 404)
- `error_type` (z.B. `ValidationError`, `IntegrityError`)
- `module` (z.B. `subroute_generator`, `osrm_client`)
- `message_short` (gecappte Fehlermeldung)
- `stack_hash` (Hash über Stacktrace zur Pattern-Erkennung)
- `stacktrace` (optional gekürzt)
- `payload_snapshot` (gecappte/anon. Nutzdaten)
- `environment` (`dev`, `prod`, `test`)
- `severity` (`info`, `warn`, `error`, `critical`)
- `is_handled` (bool: wurde der Fehler bewusst behandelt?)
- `pattern_id` (FK auf error_patterns)

### Tabelle: `error_patterns`

Fehlerklassen / Muster, auf die die KI trainiert.

**Spalten:**
- `id` (PK)
- `stack_hash` (Key für Gruppierung)
- `signature` (z.B. `ValueError in subroute_generator: cannot read property 'legs' of undefined`)
- `first_seen`, `last_seen`
- `occurrences` (Anzahl Vorkommen)
- `last_status_code`
- `primary_endpoint`
- `component` (Backend/Frontend/Infra/OSRM)
- `status` (`open`, `investigating`, `fixed`, `ignored`)
- `root_cause_hint` (Kurztext für Menschen + KI)
- `linked_rule_id` (Referenz auf Standards/Regeln)
- `linked_lesson_id` (Referenz auf LESSONS_LOG-Eintrag)

### Tabelle: `error_feedback`

Bindeglied zwischen Menschen/KI und Patterns.

**Spalten:**
- `id` (PK)
- `pattern_id` (FK)
- `source` (`dev`, `cursor`, `user`, `monitoring`)
- `note` (Kommentar)
- `resolution_status` (`todo`, `in_progress`, `fixed`, `won't_fix`)
- `created_at`, `updated_at`

### Tabelle: `success_stats`

Aggregierte Erfolgs-Statistiken.

**Spalten:**
- `id` (PK)
- `endpoint`
- `time_bucket` (z.B. Tag: `2025-11-16`)
- `total_calls`
- `success_calls`
- `error_calls`
- `avg_latency_ms`

---

## 🔧 Backend-Integration

### 1. Zentraler Error-Handler

**Datei:** `backend/core/error_handlers.py`

**Funktion:** `http_exception_handler()`

**Aufgaben:**
- Erfasst jeden 4xx/5xx standardisiert
- Extrahiert Trace-ID, Request-Infos, Exception-Typ, Stacktrace
- Berechnet `stack_hash` für Pattern-Erkennung
- Schreibt in `error_events`

**Integration:**
- Automatisch bei allen HTTPExceptions
- Keine zusätzlichen Code-Änderungen nötig

### 2. Trace-ID-Verknüpfung

**Datei:** `backend/middlewares/trace_id.py`

**Funktion:** `TraceIDMiddleware`

**Aufgaben:**
- Generiert Trace-ID für jeden Request
- Misst Request-Dauer
- Loggt erfolgreiche Requests (2xx) in `success_stats`
- Setzt `request.state.request_start_time` für Error-Handler

### 3. Error-Learning-Service

**Datei:** `backend/services/error_learning_service.py`

**Funktionen:**
- `log_error_event()` - Loggt Fehler-Event
- `log_success_event()` - Loggt Erfolgs-Event
- `calculate_stack_hash()` - Berechnet Hash für Pattern-Erkennung
- `extract_error_signature()` - Erstellt lesbare Signatur
- `get_error_patterns()` - Holt Patterns aus DB
- `get_error_events()` - Holt Events aus DB

### 4. Aggregator-Service

**Datei:** `backend/services/error_pattern_aggregator.py`

**Funktion:** `aggregate_error_patterns()`

**Aufgaben:**
- Läuft periodisch (alle 5 Minuten) als Hintergrund-Job
- Gruppiert Events nach `stack_hash`
- Erstellt/aktualisiert `error_patterns`
- Verknüpft Events mit Patterns
- Prüft Patterns auf "fixed" Status

**Integration:**
- Startet automatisch beim Server-Start
- Läuft im Hintergrund (non-blocking)

---

## 🌐 API-Endpoints

### GET `/api/audit/error-patterns`

Liste aller Error-Patterns.

**Query-Parameter:**
- `status` (optional): Filter nach Status (`open`, `investigating`, `fixed`, `ignored`)
- `component` (optional): Filter nach Component
- `limit` (optional, default: 50): Maximale Anzahl Ergebnisse

**Response:**
```json
{
  "success": true,
  "patterns": [
    {
      "id": 1,
      "stack_hash": "abc123...",
      "signature": "ValueError in subroute_generator: ...",
      "first_seen": "2025-11-16T10:00:00",
      "last_seen": "2025-11-16T15:30:00",
      "occurrences": 42,
      "last_status_code": 500,
      "primary_endpoint": "/api/tour/optimize",
      "component": "subroute_generator",
      "status": "open"
    }
  ],
  "count": 1
}
```

### GET `/api/audit/error-patterns/{pattern_id}`

Detailansicht eines Error-Patterns.

**Response:**
```json
{
  "success": true,
  "pattern": { ... },
  "events": [ ... ],  // Repräsentative Events (max. 5)
  "feedback": [ ... ]  // Feedback von Dev/KI
}
```

### GET `/api/audit/error-events`

Liste von Error-Events.

**Query-Parameter:**
- `pattern_id` (optional): Filter nach Pattern-ID
- `endpoint` (optional): Filter nach Endpoint
- `limit` (optional, default: 100): Maximale Anzahl Ergebnisse

### POST `/api/audit/error-feedback`

Speichert Feedback zu einem Error-Pattern.

**Request Body:**
```json
{
  "pattern_id": 1,
  "source": "cursor",
  "note": "Subrouten-Generator: Payload-Feld `legs` ist `null`, weil Frontend falsches Mapping nutzt.",
  "resolution_status": "fixed"
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": 123,
  "message": "Feedback gespeichert"
}
```

### GET `/api/audit/error-stats`

Aggregierte Statistiken über Error-Patterns.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_patterns": 15,
    "open_patterns": 8,
    "fixed_patterns": 5,
    "total_events": 234
  },
  "top_patterns": [ ... ]
}
```

---

## 🤖 KI-Anbindung

### 1. Cursor-Prompts erweitern

**Datei:** `Regeln/CURSOR_PROMPT_TEMPLATE.md`

**Neue Templates:**
- Template #13: "Analysiere Error-Pattern #X"
- Template #14: "Erstelle Fix-Vorschlag für Pattern #X"

**Beispiel:**
```
Analysiere Error-Pattern #23:
- Pattern: ValueError in subroute_generator: cannot read property 'legs' of undefined
- Occurrences: 42
- Primary Endpoint: /api/tour/optimize
- Status: open

Bitte:
1. Analysiere die repräsentativen Events
2. Identifiziere die Root Cause
3. Erstelle Fix-Vorschlag
4. Dokumentiere in LESSONS_LOG
```

### 2. Automatische LESSONS_LOG-Einträge

**Workflow:**
1. Pattern wird als `fixed` markiert (via Feedback)
2. Aggregator prüft: Keine neuen Events in letzter Zeit
3. Automatisch LESSONS_LOG-Eintrag erzeugen (optional, zukünftig)

### 3. ZIP-Integration

**Beim Erstellen von Audit-ZIPs:**
- Relevante `error_patterns` mit einpacken
- Beispiel-Events mit einpacken
- Feedback-Historie mit einpacken

---

## 📝 Typischer Workflow

### 1. Fehler tritt auf

```
Request → Exception → Error-Handler → error_events
```

### 2. Aggregator gruppiert

```
Aggregator (alle 5 Min) → error_patterns
```

### 3. Dev/KI analysiert

```
GET /api/audit/error-patterns/{id}
→ Pattern + Events + Feedback
```

### 4. Fix wird umgesetzt

```
POST /api/audit/error-feedback
{
  "pattern_id": 23,
  "source": "cursor",
  "note": "Fix: Frontend-Mapping korrigiert",
  "resolution_status": "fixed"
}
```

### 5. Monitoring bestätigt

```
Aggregator sieht: Keine neuen Events
→ Pattern-Status bleibt "fixed"
```

### 6. LESSONS_LOG aktualisiert

```
Manuell oder automatisch:
- Eintrag in LESSONS_LOG.md
- Link auf Commit/Change
- Verknüpfung mit Pattern
```

---

## 🧪 Tests

### Backend-Tests

1. **Error-Event-Logging testen:**
   ```python
   # Künstliche Exception auslösen
   # Prüfen ob Event in error_events erscheint
   ```

2. **Pattern-Aggregation testen:**
   ```python
   # Mehrere Events mit gleichem stack_hash
   # Prüfen ob Pattern erstellt/aktualisiert wird
   ```

3. **API-Endpoints testen:**
   ```bash
   curl "http://localhost:8111/api/audit/error-patterns"
   curl "http://localhost:8111/api/audit/error-stats"
   ```

### Integration-Tests

1. **End-to-End:**
   - Request mit Fehler → Event → Pattern → Feedback → Status-Update

2. **Performance:**
   - DB-Größe, Lösch-/Archiv-Strategie

---

## 📊 Monitoring

### Dashboard-Views

**Im Test-Dashboard:**
- Anzahl offener Patterns
- Top-Fehler (nach Occurrences)
- Trends (Fehler über Zeit)
- Erfolgsrate (success_stats)

### Alerts

**Optional (zukünftig):**
- Neues Pattern mit > 10 Occurrences → Alert
- Pattern-Status ändert sich → Notification

---

## 🔄 Wartung

### Archiv-Strategie

**Alte Events:**
- Events älter als 30 Tage → Archivieren
- Events älter als 90 Tage → Löschen (optional)

**Patterns:**
- Patterns mit Status "fixed" + keine Events in 7 Tagen → Archivieren

### Performance

**Indizes:**
- Alle wichtigen Spalten sind indiziert
- Queries sollten schnell sein (< 100ms)

**DB-Größe:**
- Monitoring: `SELECT COUNT(*) FROM error_events`
- Bei > 100.000 Events: Archivierung starten

---

## ✅ Implementierungs-Status

### Phase 1: Datenmodell & Schema ✅

- [x] `error_events` Tabelle
- [x] `error_patterns` Tabelle
- [x] `error_feedback` Tabelle
- [x] `success_stats` Tabelle
- [x] Indizes für Performance
- [x] Schema in `ensure_schema()` integriert

### Phase 2: Error-Logging integriert ✅

- [x] Error-Handler erweitert
- [x] Trace-ID-Integration
- [x] Success-Logging in Middleware
- [x] Error-Learning-Service implementiert

### Phase 3: Aggregation & APIs ✅

- [x] Aggregator-Service implementiert
- [x] API-Endpoints erstellt
- [x] Router registriert
- [x] Aggregator im Startup integriert

### Phase 4: KI-Anbindung ⏳

- [ ] Cursor-Prompt-Templates erweitern
- [ ] Automatische LESSONS_LOG-Einträge (optional)
- [ ] ZIP-Integration (optional)

### Phase 5: Härtung & Monitoring ⏳

- [ ] Unit-Tests
- [ ] Integration-Tests
- [ ] Dashboard-Views
- [ ] Archiv-Strategie

---

## 🎯 Nächste Schritte

1. **Server neu starten** (Schema-Änderungen erfordern Neustart)
2. **Testen:** Fehler auslösen und prüfen ob Events erfasst werden
3. **API testen:** `/api/audit/error-patterns` aufrufen
4. **KI-Prompts erweitern:** Templates für Pattern-Analyse

---

**Erstellt:** 2025-11-16  
**Status:** ✅ **PHASE 1-3 IMPLEMENTIERT**  
**Nächste Schritte:** Phase 4-5 (KI-Anbindung, Tests)

