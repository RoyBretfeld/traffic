# Offene Punkte – TrafficApp 3.0

**Stand:** 2025-11-22  
**Status:** 6/12 AR-Punkte abgeschlossen

---

## ✅ Abgeschlossen (6/12)

- ✅ **AR-02:** Admin-APIs unter `/api/admin/*` gebündelt (Backward Compatibility)
- ✅ **AR-09:** Tourplan-Übersicht als Tab in `admin.html` integriert
- ✅ **AR-04:** Stats-Daily Migration erstellt (`db/migrations/2025-11-22_add_stats_daily.sql`)
- ✅ **AR-05:** Geocoding-Failure-Liste als Admin-Tab integriert
- ✅ **AR-06:** OSRM-Cache Cleanup-Script erstellt (`scripts/cleanup_osrm_cache.py`)
- ✅ **AR-11:** Requirements gepinnt (exakte Versionen)

---

## 🔴 Offen – Phase B (Betriebsfest machen)

### AR-01: Job-Runner & Queues ⚠️ **TOP-PRIORITÄT**

**Status:** ❌ Nicht umgesetzt  
**Aufwand:** 2-3 Tage  
**Priorität:** 🔴 **KRITISCH**

**Aktuell:**
- `CodeImprovementJob` läuft als asyncio-Task
- `ErrorPatternAggregator` läuft als asyncio-Task
- Keine Retry/Backoff/Dead-Letter-Queue

**Ziel:**
- Queue-System einführen (RQ/Redis oder **Arq** empfohlen)
- Queues: `import`, `geocode`, `stats`, `embeddings`
- Retry mit exponential Backoff
- Dead-Letter-Queue für fehlgeschlagene Jobs
- Monitoring (Queue-Längen, Job-Status)

**Empfehlung:** **Arq** (asyncio-basiert, Redis-Backend)

---

### AR-04: Stats-Aggregator Job (Teil 2)

**Status:** ⚠️ Migration erstellt, aber Job fehlt  
**Aufwand:** 1-2 Tage  
**Priorität:** 🟡 **WICHTIG**

**Bereits erledigt:**
- ✅ `stats_daily` Tabelle erstellt
- ✅ Migration vorhanden

**Noch zu tun:**
- ❌ Aggregator-Job implementieren (füllt `stats_daily` täglich)
- ❌ Frontend nutzt `stats_daily` statt direkter DB-Abfragen
- ❌ Optional: `stats_weekly` Tabelle + Job

---

### AR-05: Geocoding-Failure Retry (Teil 2)

**Status:** ⚠️ Tab erstellt, aber Retry-Funktion fehlt  
**Aufwand:** 1 Tag  
**Priorität:** 🟡 **WICHTIG**

**Bereits erledigt:**
- ✅ Geocoding-Fehler Tab in `admin.html`
- ✅ Filter, Suche, Löschen implementiert

**Noch zu tun:**
- ❌ Retry-Funktion implementieren (API-Endpoint `/api/geocode/retry`)
- ❌ Backoff/Retry-Logic für fehlgeschlagene Geocodes

---

### AR-06: OSRM-Cache Cleanup Job (Teil 2)

**Status:** ⚠️ Script erstellt, aber Cron-Job fehlt  
**Aufwand:** 0.5 Tage  
**Priorität:** 🟢 **NICHT KRITISCH**

**Bereits erledigt:**
- ✅ `scripts/cleanup_osrm_cache.py` erstellt
- ✅ Cleanup-Logik vorhanden

**Noch zu tun:**
- ❌ Cron-Job / Scheduled Task einrichten
- ❌ Monitoring für Cache-Größe

---

### AR-09: Admin-Navigation vollständig konsolidieren (Teil 2)

**Status:** ⚠️ Teilweise umgesetzt  
**Aufwand:** 2-3 Tage  
**Priorität:** 🟡 **WICHTIG**

**Bereits erledigt:**
- ✅ Tourplan-Übersicht als Tab integriert
- ✅ Geocoding-Fehler als Tab integriert

**Noch zu tun:**
- ❌ Weitere separate Seiten als Tabs integrieren:
  - `frontend/admin/statistik.html` → Tab in `admin.html`
  - `frontend/admin/systemregeln.html` → Tab in `admin.html`
  - `frontend/admin/ki-integration.html` → Tab in `admin.html`
  - `frontend/admin/db-verwaltung.html` → Tab in `admin.html`
  - Weitere separate Seiten...
- ❌ Alte separate Seiten entfernen (nach vollständiger Migration)

---

## 🟡 Offen – Phase C (Funktional erweitern)

### AR-03: Tourplan-Tab Tagesübersicht (KPIs)

**Status:** ❌ Nicht umgesetzt  
**Aufwand:** 1-2 Tage  
**Priorität:** 🟡 **WICHTIG**

**Hinweis:** Tourplan-Tab existiert bereits, aber AR-03 meint spezifische KPIs:
- Summen: km, Zeiten, Kosten
- Live-Daten aus DB
- Tagesübersicht mit detaillierten KPIs

**Ziel:**
- Erweitere Tourplan-Tab um detaillierte KPIs
- Tagesübersicht mit Summen (km, Zeiten, Kosten)

---

### AR-07: RBAC Minimal

**Status:** ❌ Nicht umgesetzt  
**Aufwand:** 3-4 Tage  
**Priorität:** 🟡 **WICHTIG**

**Aktuell:**
- `users` Tabelle mit `role` Spalte (aber nur "admin")
- Keine Rollen-Definitionen

**Ziel:**
- Rollen: `Admin`, `Dispo`, `ReadOnly`
- Tabs & Endpoints rollenbasiert schützen
- `Depends(require_role("admin"))` etc.

---

## 🔵 Offen – Phase D (Skalierung & Qualität)

### AR-10: Observability

**Status:** ❌ Nicht umgesetzt  
**Aufwand:** 3-5 Tage  
**Priorität:** 🟢 **NICHT KRITISCH**

**Ziel:**
- Prometheus-Metriken
- OpenTelemetry-Tracing
- Health/Ready-Probes (bereits vorhanden ✅)
- Queue-Längen-Metriken (nach AR-01)

**Bereits vorhanden:**
- ✅ `/healthz` und `/readyz` Endpoints
- ✅ `/metrics/simple` Endpoint (einfache Metriken)

---

### AR-11: CI-Erweiterung (Teil 2)

**Status:** ⚠️ Requirements gepinnt, aber CI fehlt  
**Aufwand:** 1 Tag  
**Priorität:** 🟡 **WICHTIG**

**Bereits erledigt:**
- ✅ Exakte Versionen in `requirements.txt`
- ✅ `pip-audit` und `safety` hinzugefügt

**Noch zu tun:**
- ❌ CI-Pipeline mit `pip-audit`/`safety` erweitern
- ❌ Regelmäßige Security-Scans

---

### AR-12: Postgres-Migrationspfad

**Status:** ❌ Nicht umgesetzt  
**Aufwand:** 2-3 Tage  
**Priorität:** 🟢 **NICHT KRITISCH**

**Ziel:**
- Abstraktionslayer prüfen (bereits vorhanden ✅)
- Migrations über Alembic dokumentieren
- Feature-Flags für Dual-Write

---

## 📊 Prioritäten-Matrix

### Sofort (diese Woche)
1. 🔴 **AR-01:** Job-Runner & Queues (kritisch für Skalierung)
2. 🟡 **AR-04:** Stats-Aggregator Job (füllt `stats_daily`)
3. 🟡 **AR-05:** Retry-Funktion (Geocoding-Fehler)

### Nächste Woche
4. 🟡 **AR-09:** Admin-Navigation vollständig konsolidieren
5. 🟡 **AR-03:** Tourplan-Tab KPIs erweitern
6. 🟡 **AR-11:** CI-Erweiterung (Security-Scans)

### Später
7. 🟡 **AR-07:** RBAC Minimal
8. 🟢 **AR-10:** Observability (Prometheus/OTel)
9. 🟢 **AR-12:** Postgres-Migrationspfad
10. 🟢 **AR-06:** Cron-Job einrichten (OSRM-Cache)

---

## 🎯 Nächste Schritte (Empfehlung)

**Diese Woche:**
1. **AR-01** (Job-Runner) – kritisch für Skalierung
2. **AR-04** (Stats-Aggregator Job) – schnell umsetzbar
3. **AR-05** (Retry-Funktion) – schnell umsetzbar

**Nächste Woche:**
4. **AR-09** (Admin-Navigation) – große UX-Verbesserung
5. **AR-03** (Tourplan-KPIs) – Funktionalität erweitern

---

**Letzte Aktualisierung:** 2025-11-22  
**Nächste Review:** Nach Phase B (1-2 Wochen)

