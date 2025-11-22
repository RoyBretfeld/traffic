# Architektur-Review Roadmap 2025-11-22

**Quelle:** TrafficApp 3.0 – Architektur & Funktions‑Review (2025‑11‑22)  
**Status:** Phase A (Security) abgeschlossen, Phase B startet

---

## ✅ Bereits umgesetzt (Phase A)

### Security (AR-08) ✅
- [x] CORS Allowlist (Production)
- [x] Security-Header (CSP, HSTS, X-Frame-Options, etc.)
- [x] Upload-Whitelist + `resolve()` Check
- [x] Admin-APIs geschützt (`require_admin`)
- [x] Debug-Routen nur mit Flag

**Dokumentation:** `docs/SECURITY_ABSCHLUSS_2025-11-22.md`

### Teilweise vorhanden
- ✅ **Geocoding-Cache:** `geo_cache` Tabelle existiert
- ✅ **OSRM-Cache:** `backend/cache/osrm_cache.py` existiert
- ✅ **Stats-Aggregator:** `backend/services/stats_aggregator.py` existiert
- ✅ **Background-Jobs:** `CodeImprovementJob`, `ErrorPatternAggregator` (aber keine Queue)
- ✅ **Admin-Navigation:** `admin.html` mit Tabs (aber auch separate Seiten)

---

## 🎯 Phase B – Betriebsfest machen (1–2 Wochen)

### AR-01: Job-Runner & Queues ⚠️ **TOP-PRIORITÄT**

**Status:** BackgroundTasks vorhanden, aber keine belastbare Queue

**Aktuell:**
- `CodeImprovementJob` läuft als asyncio-Task
- `ErrorPatternAggregator` läuft als asyncio-Task
- Keine Retry/Backoff/Dead-Letter-Queue

**Ziel:**
- Queue-System einführen (RQ/Redis oder Arq)
- Queues: `import`, `geocode`, `stats`, `embeddings`
- Retry mit exponential Backoff
- Dead-Letter-Queue für fehlgeschlagene Jobs
- Monitoring (Queue-Längen, Job-Status)

**Empfehlung:** **Arq** (asyncio-basiert, Redis-Backend)

**Aufwand:** 2-3 Tage

---

### AR-02: Admin-APIs bündeln & konsolidieren

**Status:** Teilweise umgesetzt (alle Router haben `require_admin`)

**Aktuell:**
- Router sind geschützt, aber nicht unter `/api/admin/*` gebündelt
- Kein globaler Prefix

**Ziel:**
- Alle Admin-APIs unter `/api/admin/*` bündeln
- Globaler `Depends(require_admin_auth)` auf Router-Level
- Login-Rate-Limit (bereits vorhanden ✅)

**Aufwand:** 1 Tag

---

### AR-09: Admin-Navigation konsolidieren ⚠️ **WICHTIG**

**Status:** Gemischte Seiten vorhanden

**Aktuell:**
- `admin.html` mit Tabs (gut ✅)
- Aber auch: `frontend/admin/tourplan-uebersicht.html` (separate Seite ❌)
- Aber auch: `frontend/admin/statistik.html` (separate Seite ❌)

**Ziel:**
- **Nur eine Admin-Seite:** `admin.html`
- Alle Module als Tabs integrieren
- Konsistente Benennung: `#tab-db`, `#tab-stats`, `#tab-tourplan`, etc.

**Aufwand:** 2-3 Tage

---

### AR-04: Stats-Aggregator erweitern

**Status:** Aggregator existiert, aber prüfen ob `stats_daily` gefüllt wird

**Aktuell:**
- `backend/services/stats_aggregator.py` existiert
- Endpoints: `/api/stats/daily`, `/api/stats/monthly`
- Frontend nutzt bereits Aggregat

**Ziel:**
- Prüfen ob `stats_daily` Tabelle existiert und gefüllt wird
- Job für tägliche Aggregation (über Queue)
- Optional: `stats_weekly` Tabelle

**Aufwand:** 1-2 Tage

---

## 🎯 Phase C – Funktional erweitern (2–4 Wochen)

### AR-03: Tourplan-Tab "Tagesübersicht"

**Status:** Separate Seite `tourplan-uebersicht.html` existiert

**Ziel:**
- Als Tab in `admin.html` integrieren
- Summen: km, Zeiten, Kosten
- Live-Daten aus DB

**Aufwand:** 1-2 Tage

---

### AR-05: Geocoding-Cache + Failure-Liste

**Status:** Cache existiert (`geo_cache` Tabelle)

**Ziel:**
- Failure-Liste im Admin-Tab
- Backoff/Retry für fehlgeschlagene Geocodes
- Manuelle Korrektur-UI

**Aufwand:** 2-3 Tage

---

### AR-06: OSRM-Cache optimieren

**Status:** Cache existiert (`backend/cache/osrm_cache.py`)

**Ziel:**
- TTL-Management
- Cache-Hit-Rate-Metriken
- Cleanup-Job

**Aufwand:** 1 Tag

---

### AR-07: RBAC Minimal

**Status:** Benutzerverwaltung existiert, aber keine Rollen

**Aktuell:**
- `users` Tabelle mit `role` Spalte (aber nur "admin")
- Keine Rollen-Definitionen

**Ziel:**
- Rollen: `Admin`, `Dispo`, `ReadOnly`
- Tabs & Endpoints rollenbasiert schützen
- `Depends(require_role("admin"))` etc.

**Aufwand:** 3-4 Tage

---

## 🎯 Phase D – Skalierung & Qualität (4+ Wochen)

### AR-10: Observability

**Ziel:**
- Prometheus-Metriken
- OpenTelemetry-Tracing
- Health/Ready-Probes
- Queue-Längen-Metriken

**Aufwand:** 3-5 Tage

---

### AR-11: Requirements pinnen

**Status:** Aktuell nur `>=` Versionen

**Ziel:**
- Exakte Versionen pinnen
- CI mit `pip-audit`/`safety`
- Regelmäßige Updates

**Aufwand:** 1 Tag

---

### AR-12: Postgres-Migrationspfad

**Ziel:**
- Abstraktionslayer prüfen (bereits vorhanden ✅)
- Migrations über Alembic dokumentieren
- Feature-Flags für Dual-Write

**Aufwand:** 2-3 Tage

---

## 📊 Prioritäten-Matrix

### Sofort (diese Woche)
1. **AR-09:** Admin-Navigation konsolidieren (wichtig für UX)
2. **AR-02:** Admin-APIs bündeln (konsistente Struktur)
3. **AR-04:** Stats-Aggregator prüfen/erweitern

### Nächste Woche
4. **AR-01:** Job-Runner & Queues (kritisch für Skalierung)
5. **AR-03:** Tourplan-Tab integrieren
6. **AR-05:** Geocoding-Failure-Liste

### Später
7. **AR-07:** RBAC Minimal
8. **AR-10:** Observability
9. **AR-11:** Requirements pinnen
10. **AR-12:** Postgres-Migrationspfad

---

## 🎯 Nächste Schritte (heute)

**Empfehlung:** Mit **AR-09** (Admin-Navigation konsolidieren) beginnen, da:
- Schnell umsetzbar (2-3 Tage)
- Große UX-Verbesserung
- Konsistente Struktur für weitere Features

**Danach:** AR-02 (Admin-APIs bündeln) für konsistente API-Struktur.

---

**Letzte Aktualisierung:** 2025-11-22  
**Nächste Review:** Nach Phase B (1-2 Wochen)

