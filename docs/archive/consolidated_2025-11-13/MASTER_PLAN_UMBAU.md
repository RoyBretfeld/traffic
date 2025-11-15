# Master-Plan: FAMO TrafficApp 3.0 - Umbau & Erweiterungen

**Erstellt:** 2025-01-10  
**Status:** 🟢 Bereit zur Umsetzung  
**Priorität:** Schrittweise, minimalinvasiv

---

## 📋 Übersicht

Dieser Plan konsolidiert alle geplanten Umbauten und Erweiterungen in einer einzigen, umsetzbaren Liste. Alle Änderungen sind **rollback-sicher** und **minimalinvasiv** - bestehende Features bleiben funktionsfähig.

---

## ✅ MVP Patchplan - BEREITS IMPLEMENTIERT

### Status: ✅ Fertig
- Config-System (`config/app.yaml` + `backend/config.py`)
- OSRM-Client erweitert (Fallback, Polyline6)
- Health-Endpoints (`/health/osrm`, `/health/app`)
- Stats-Box im Frontend (read-only, Mock-Daten)
- Route-Details Endpoint (Polyline6)

**Nächster Schritt:** PyYAML installieren (`pip install pyyaml`), Server neu starten

---

## 🎯 Phase 1: Sofort (Niedriges Risiko)

### 1.1 OSRM-Polyline6-Decode im Frontend
**Ziel:** Straßen-Linien statt gerade Linien auf Karte  
**Risiko:** 🟢 Sehr niedrig (nur Frontend-JavaScript)  
**Dateien:** `frontend/index.html` (JavaScript erweitern)  
**Aufwand:** ~2 Stunden

**Tasks:**
- [ ] Polyline6-Decoder im Frontend implementieren
- [ ] Route-Geometrie korrekt auf Karte rendern
- [ ] Fallback auf gerade Linien wenn Decode fehlschlägt

---

### 1.2 Stats-Box: Echte Daten aus DB
**Ziel:** Mock-Daten durch echte DB-Aggregation ersetzen  
**Risiko:** 🟢 Niedrig (neue Funktion, bestehende unverändert)  
**Dateien:** `routes/stats_api.py`, `backend/services/stats_aggregator.py` (neu)  
**Aufwand:** ~4 Stunden

**Tasks:**
- [ ] Stats-Aggregator Service erstellen
- [ ] DB-Queries für monatliche Touren, Stops, KM
- [ ] Stats-API erweitern (Mock → DB)
- [ ] Tests

---

### 1.3 Admin-Bereich (neue Seite)
**Ziel:** Separate Admin-Seite mit Testboard, AI-Test, Statistik  
**Risiko:** 🟢 Niedrig (neue Seite, Hauptseite unverändert)  
**Dateien:** `frontend/admin.html` (neu), `routes/admin_api.py` (neu)  
**Aufwand:** ~1 Tag

**Tasks:**
- [ ] Admin-HTML-Seite erstellen
- [ ] Navigation erweitern (Admin-Link, nur für Admins)
- [ ] Admin-API-Endpoints (Testboard, AI-Test, Stats-Detail)
- [ ] Auth-Check (JWT oder Basic-Auth)

---

## 🟡 Phase 2: Kurzfristig (Mittleres Risiko)

### 2.1 Datenbank-Schema-Erweiterung
**Ziel:** Neue Tabellen für Stats, Routes, OSRM-Cache  
**Risiko:** 🟡 Mittel (Migration nötig, aber mit Backup)  
**Dateien:** `docs/database_schema.sql`, `scripts/migrate_YYYYMMDD.py` (neu)  
**Aufwand:** ~1 Woche

**Tasks:**
- [ ] Schema erweitern (stats_*, routes, route_legs, osrm_cache)
- [ ] Migration-Script erstellen (mit Backup + Rollback)
- [ ] Schrittweise Einführung (erst schreiben, dann lesen)
- [ ] Tests

**WICHTIG:** Backup vor Migration, Rollback-Plan bereit

---

### 2.2 Abdockbare Panels (Phase 1 - Vanilla JS)
**Ziel:** Karte/Tour-Übersicht in separaten Fenstern  
**Risiko:** 🟡 Mittel (neue Funktion, bestehende Ansicht bleibt)  
**Dateien:** `frontend/index.html` (JavaScript erweitern)  
**Aufwand:** ~2 Tage

**Tasks:**
- [ ] `window.open` für Panel-Fenster
- [ ] BroadcastChannel/postMessage für Kommunikation
- [ ] Persistentes Layout (localStorage)
- [ ] Button zum Abdocken in Hauptseite

---

### 2.3 Statistik-Detailseite im Admin
**Ziel:** Vollständige Statistik-Ansicht mit Charts  
**Risiko:** 🟡 Mittel (neue Seite, bestehende unverändert)  
**Dateien:** `frontend/admin.html` (erweitern), `routes/stats_api.py` (erweitern)  
**Aufwand:** ~2 Tage

**Tasks:**
- [ ] Stats-Detail-Endpoints (Tage, Monate, Export)
- [ ] Charts (Sparklines, Mini-Graphs)
- [ ] Export-Funktion (CSV, JSON)
- [ ] Pfad-Konfiguration (Storage-Pfad)

---

## 🔴 Phase 3: Mittelfristig (Optional)

### 3.1 Lizenzierungssystem
**Ziel:** Online-Lizenzprüfung, Offline-Fallback  
**Risiko:** 🟡 Mittel (neue Komponente, optional)  
**Dateien:** `services/licensing.py` (neu), `routes/licensing_api.py` (neu)  
**Aufwand:** ~1 Woche

**Tasks:**
- [ ] Ed25519-basierte JWT-Lizenzen
- [ ] Device-Fingerprinting
- [ ] Grace-Period (Offline)
- [ ] Admin-UI für Lizenzverwaltung

---

### 3.2 Export & Live-Daten
**Ziel:** Maps-Export, Baustellen-Overlay, Speedcams  
**Risiko:** 🟡 Mittel (neue Features, bestehende unverändert)  
**Dateien:** `routes/export_api.py` (neu), `frontend/index.html` (erweitern)  
**Aufwand:** ~1 Woche

**Tasks:**
- [ ] Maps-Export (Google/Apple URLs + QR-Codes)
- [ ] Baustellen-Overlay (Autobahn API)
- [ ] Speedcams-Overlay (mit Legal-Guard, opt-in)

---

### 3.3 Deployment & AI-Ops
**Ziel:** Installer, Updates, AI-Monitoring  
**Risiko:** 🟡 Mittel (neue Komponenten)  
**Dateien:** `installer/` (neu), `scripts/ai_healthcheck.py` (neu)  
**Aufwand:** ~2 Wochen

**Tasks:**
- [ ] NSIS-Installer
- [ ] Update-Strategie (LTS, manuell)
- [ ] AI-Healthcheck (E-Mail-Alerts)
- [ ] Smoke-Tests

---

## ⏸️ Phase 4: Langfristig (Später)

### 4.1 React-Migration
**Ziel:** Frontend von Vanilla JS zu React  
**Risiko:** 🔴 Hoch (große Änderung)  
**Status:** ⏸️ Geplant, aber nicht sofort  
**Aufwand:** ~1 Monat

**Empfehlung:** Erst alle anderen Features fertig, dann React

---

## 🛡️ Sicherheits-Strategie

### Für jede Änderung:
1. ✅ **Backup erstellen** (automatisch vor Migrationen)
2. ✅ **Feature-Flags** (kann deaktiviert werden ohne Code-Änderung)
3. ✅ **Schrittweise** (eine Änderung zur Zeit)
4. ✅ **Tests** (nach jeder Änderung)
5. ✅ **Rollback-Plan** (Backup + alte Version)

---

## 📊 Priorisierung

### Sofort (diese Woche):
1. ✅ MVP Patchplan (bereits implementiert)
2. OSRM-Polyline6-Decode im Frontend
3. Stats-Box: Echte Daten aus DB

### Kurzfristig (nächste 2 Wochen):
1. Admin-Bereich
2. Datenbank-Schema-Erweiterung
3. Abdockbare Panels (Phase 1)

### Mittelfristig (nächster Monat):
1. Statistik-Detailseite
2. Export & Live-Daten
3. Lizenzierungssystem (wenn nötig)

### Langfristig (später):
1. React-Migration (wenn nötig)
2. Deployment & AI-Ops (wenn nötig)

---

## 📝 Checkliste für jede Änderung

### Vor der Änderung:
- [ ] Backup erstellen
- [ ] Feature-Flag in `config/app.yaml` setzen
- [ ] Tests schreiben
- [ ] Rollback-Plan dokumentieren

### Nach der Änderung:
- [ ] Tests ausführen
- [ ] Health-Checks prüfen
- [ ] Manuelle Tests (CSV-Upload, Optimierung)
- [ ] Dokumentation aktualisieren

---

## 🔄 Rollback-Strategie

### Stats-Box deaktivieren:
```yaml
# config/app.yaml
app:
  feature_flags:
    stats_box_enabled: false
```

### OSRM-Fallback deaktivieren:
```yaml
# config/app.yaml
osrm:
  fallback_enabled: false
```

### Migration rückgängig machen:
1. Server stoppen
2. Backup-DB wiederherstellen
3. Alte Version wiederherstellen

---

## 📚 Referenzen

- **Aktueller Stand:** `docs/AKTUELLER_STAND_2025-01-10.md`
- **MVP Patchplan:** `docs/MVP_PATCHPLAN_IMPLEMENTIERT.md`
- **Architektur:** `docs/ARCHITEKTUR_KOMPLETT.md`

---

**Status:** 🟢 Bereit zur Umsetzung  
**Nächster Schritt:** Phase 1.1 - OSRM-Polyline6-Decode im Frontend

