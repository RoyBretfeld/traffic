# Analyse: Aktuelle Implementierung vs. Betriebsordnung

## ⚠️ KRITISCHE ABWEICHUNGEN

### 1. ❌ Index-Mapping statt UIDs

**Betriebsordnung sagt:**
- `stop_uid = sha256(source_id | norm(address) | plz | ort)`
- **KEIN** Index-Mapping/Koordinatenvergleich als Identität

**Aktuelle Implementierung:**
- `routes/workflow_api.py` Zeile 973-1028: **Koordinaten-Match** mit Toleranz
- `valid_stops.index(opt_stop)` - versucht Objekt-Identität
- Fallback: Koordinaten-Match (0.0001 Toleranz)

**Problem:** Verstößt gegen Betriebsordnung §13 (Verbot: "Kein Index‑Mapping/Koordinatenvergleich")

**Lösung:** Umstellen auf `stop_uid`-basierte Identifikation

---

### 2. ❌ LLM ohne UID-basierten Prompt

**Betriebsordnung sagt:**
- Prompt: **ausschließlich `stop_uid`** (+ optionale Labels/Constraints)
- **KEINE** Indizes/Koordinaten im Prompt

**Aktuelle Implementierung:**
- `services/llm_optimizer.py` Zeile 204-253: Prompt enthält **Koordinaten** und **Indizes**
- Beispiel: `"0: Kunde 1 - Fröbelstraße 1 (51.0492, 13.6984)"`

**Problem:** Verstößt gegen Betriebsordnung §5 (LLM-Prompt: nur UIDs)

**Lösung:** Prompt umstellen auf `stop_uid` + Labels

---

### 3. ❌ Keine Set-Validierung

**Betriebsordnung sagt:**
- Harte Validierung: `set(route) == set(valid_stop_uids) and len(route) == len(valid_stop_uids)`
- Bei Fehler: **400 + Quarantäne** (kein Auto-Fix)

**Aktuelle Implementierung:**
- `routes/workflow_api.py` Zeile 1024-1028: Fehlende Indizes werden **automatisch hinzugefügt**
- Keine Quarantäne bei Validierungsfehler

**Problem:** Verstößt gegen Betriebsordnung §3 (Valider Zwang) und §0 (Sicherheitsgurt)

**Lösung:** Harte Set-Validierung + Quarantäne bei Fehler

---

### 4. ❌ LLM als Primär-Strategie (nicht Fallback)

**Betriebsordnung sagt:**
- LLM **nur Fallback** wenn Heuristik/OSRM nicht eindeutig
- OSRM **vor** LLM

**Aktuelle Implementierung:**
- `routes/workflow_api.py` Zeile 959-967: **LLM wird zuerst versucht**
- Fallback zu Nearest-Neighbor nur wenn LLM fehlschlägt
- OSRM wird optional verwendet (Zeile 210-214), nicht als Primär-Strategie

**Problem:** Verstößt gegen Betriebsordnung §4 (OSRM vor LLM) und §5 (LLM nur Fallback)

**Lösung:** Reihenfolge ändern: OSRM → Heuristik → LLM (nur wenn nötig)

---

### 5. ❌ Keine OSRM Table API (nur Route API)

**Betriebsordnung sagt:**
- **OSRM Table API** für Distanz-Matrix: `GET /table/v1/driving/{coords}?annotations=duration`
- Table für Optimierung, Route für Visualisierung

**Aktuelle Implementierung:**
- `services/llm_optimizer.py` Zeile 256-306: Nur **Route API** (`/route/v1/driving/`)
- Table API wird nicht verwendet

**Problem:** Ineffizient (n² Requests statt 1 Request für Matrix)

**Lösung:** OSRM Table API für Distanz-Matrix verwenden

---

### 6. ❌ Keine Timeouts/Retry/Circuit-Breaker

**Betriebsordnung sagt:**
- `connect_timeout=1.5s`, `read_timeout=8s`
- Retry 2× (idempotente GETs)
- Circuit-Breaker (Trip 5/60s, Half-Open 30s)

**Aktuelle Implementierung:**
- `services/llm_optimizer.py` Zeile 269: Nur `timeout=self.osrm_timeout` (10s)
- Kein Retry, kein Circuit-Breaker

**Problem:** Keine Resilienz bei OSRM-Ausfällen

**Lösung:** Zentraler OSRM-Client mit Timeouts/Retry/CB

---

### 7. ❌ API-Endpoint-Struktur anders

**Betriebsordnung sagt:**
- `/engine/tours/ingest`
- `/engine/tours/{tour_uid}/status`
- `/engine/tours/optimize`
- `/engine/tours/split`

**Aktuelle Implementierung:**
- `/api/tour/optimize` (nicht `/engine/tours/optimize`)
- Keine `/ingest` oder `/status` Endpoints
- Keine `/split` Endpoint (Splitting im Frontend)

**Problem:** Andere API-Struktur, keine klare Trennung Engine vs. andere APIs

**Lösung:** Neue `/engine/` Endpoints erstellen (alte behalten für Kompatibilität?)

---

### 8. ❌ Keine UID-Generierung

**Betriebsordnung sagt:**
- `tour_uid = sha256(tour_id)`
- `stop_uid = sha256(source_id | norm(address) | plz | ort)`

**Aktuelle Implementierung:**
- Keine UID-Generierung
- Verwendet `tour_id` direkt (z.B. "W-07.00 Uhr Tour")

**Problem:** Keine deterministische Identifikation

**Lösung:** UID-Generierung implementieren

---

## ✅ Was bereits korrekt ist

1. ✅ Pydantic v2 (vermutlich, muss geprüft werden)
2. ✅ FastAPI
3. ✅ SQLite
4. ✅ LLM mit JSON-Format (`response_format={"type": "json_object"}`)
5. ✅ Fallback-Mechanismus (Nearest-Neighbor)
6. ✅ OSRM-Code vorhanden (muss nur aktiviert/verbessert werden)

---

## 🔄 Migrations-Plan

### Phase 1: UID-System einführen
1. `tour_uid` und `stop_uid` Generierung implementieren
2. Datenbank-Schema erweitern (UID-Spalten)
3. Bestehende Touren migrieren (Backwards-Kompatibilität)

### Phase 2: API umstellen
1. Neue `/engine/` Endpoints erstellen
2. Alte `/api/tour/optimize` behalten (Deprecated)
3. Migrations-Guide dokumentieren

### Phase 3: OSRM-First
1. OSRM Table API implementieren
2. OSRM vor LLM verwenden
3. Circuit-Breaker/Retry hinzufügen

### Phase 4: LLM als Fallback
1. LLM-Prompt auf UIDs umstellen
2. LLM nur wenn OSRM/Heuristik nicht ausreicht
3. `llm_usage_ratio` Metriken

### Phase 5: Validierung & Quarantäne
1. Set-Validierung implementieren
2. Quarantäne-System für fehlerhafte Touren
3. Admin-API für Review

---

## 📋 Konkrete To-Do-Liste (Morgen)

1. **UID-System:** `tour_uid` und `stop_uid` Generierung
2. **OSRM Table API:** Distanz-Matrix statt einzelne Route-Calls
3. **API-Struktur:** Neue `/engine/` Endpoints
4. **Reihenfolge ändern:** OSRM → Heuristik → LLM
5. **Validierung:** Set-Validierung + Quarantäne
6. **LLM-Prompt:** Auf UIDs umstellen
7. **Circuit-Breaker:** OSRM-Client mit Resilienz

---

**Status:** ⚠️ Aktuelle Implementierung weicht erheblich von Betriebsordnung ab. Migration erforderlich.

