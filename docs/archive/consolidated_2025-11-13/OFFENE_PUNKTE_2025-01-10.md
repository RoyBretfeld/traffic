# Offene Punkte - FAMO TrafficApp 3.0

**Stand:** 2025-01-10 (Nach Live-Daten & Blitzer-Integration)

---

## ✅ GERADE IMPLEMENTIERT (Heute)

### Live-Daten & Blitzer-Integration
- ✅ **Live-Traffic-Daten Service** (`backend/services/live_traffic_data.py`)
  - Baustellen, Unfälle, Sperrungen
  - Blitzer/Radar (optional)
  - Integration in Routen-Optimierung
- ✅ **API-Endpunkte** (`routes/live_traffic_api.py`)
  - GET/POST/DELETE für Hindernisse
  - GET/POST/DELETE für Blitzer
- ✅ **Routen-Optimierung erweitert** (`backend/services/routing_optimizer.py`)
  - Verzögerungen durch Hindernisse berücksichtigt
  - Alternative Routen bei kritischen Hindernissen
- ✅ **Frontend-Visualisierung** (`frontend/index.html`)
  - Blitzer-Marker auf Karte
  - Toggle-Button zum Ein-/Ausblenden
  - Info-Banner bei gefundenen Blitzern

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

---

## 🔴 HOCH PRIORITÄT (Sofort)

### 1. Live-Daten: Echte API-Integrationen
**Status:** 🟡 Basis vorhanden, aber Mock-Daten

**Offene Tasks:**
- [ ] **Autobahn API** (mautinfo.de) - Echte Baustellen-Daten
  - Aktuell: Mock-Daten für Tests
  - TODO in Code: `backend/services/live_traffic_data.py:163`
- [ ] **Blitzer-Daten-Quelle** - Rechtliche Klärung
  - Blitzer.de bietet keine öffentliche API
  - Alternative Datenquellen finden oder manuelle Datenerfassung
- [ ] **OSM Overpass API** - Verbesserung
  - Aktuell: Basis-Implementierung vorhanden
  - Erweiterte Queries für mehr Daten

**Risiko:** 🟡 **MITTEL** (externe APIs, rechtliche Aspekte)

---

### 2. Phase 2.1: Datenbank-Schema-Erweiterung aktivieren
**Status:** 🟡 Schema definiert, Migration-Script vorhanden, aber noch nicht aktiviert

**Offene Tasks:**
- [ ] Feature-Flag aktivieren (`new_schema_enabled: true` in `config/app.yaml`)
- [ ] Migration durchführen (mit Backup)
- [ ] Tests mit neuen Tabellen

**Risiko:** 🟡 **MITTEL** (mit Backup + Rollback sicher)

**Dateien:**
- `db/schema_phase2.py` (bereits definiert)
- `scripts/migrate_schema_phase2.py` (bereits vorhanden)
- `config/app.yaml` (Feature-Flag setzen)

---

### 3. Admin-Auth implementieren
**Status:** ⚠️ Admin-Bereich ohne Authentifizierung

**Offene Tasks:**
- [ ] Auth-Check für Admin-Bereich
- [ ] Login-System (optional: einfache Passwort-Abfrage)
- [ ] Session-Management

**Risiko:** 🟡 **MITTEL** (für Produktion wichtig)

---

## 🟡 MITTEL PRIORITÄT (Kurzfristig)

### 4. Live-Daten: Verbesserungen
**Status:** ✅ Basis implementiert, aber Verbesserungen möglich

**Offene Tasks:**
- [ ] **Präzisere Distanz-Berechnung** zu Routen-Segmenten
  - Aktuell: Vereinfachte Berechnung (Minimum der Endpunkte)
  - TODO in Code: `backend/services/live_traffic_data.py:395`
  - TODO in Code: `backend/services/routing_optimizer.py:444`
- [ ] **GPX-Import** für Blitzer-Daten
  - Import-Funktion für GPX-Dateien
  - Validierung und Duplikatsprüfung
- [ ] **Caching-Optimierung**
  - Separate Cache-Dauer für verschiedene Datentypen
  - Aktuell: 15 Min für Hindernisse, 60 Min für Blitzer

**Risiko:** 🟢 **NIEDRIG** (Verbesserungen, keine kritischen Features)

---

### 5. Routing-Optimizer erweitern
**Status:** ✅ Implementiert, aber noch nicht vollständig

**Offene Tasks:**
- [ ] **Clustering für n > 80 Stopps**
  - Aktuell: NN+2-Opt (TODO in Code: `routing_optimizer.py:645`)
  - Sollte: Clustering-Algorithmus
- [ ] **Valhalla/GraphHopper Integration** (optional)
  - Aktuell: Nur OSRM + lokale Haversine
  - TODO in Code: `routing_optimizer.py:164, 171`
- [ ] **Tests mit echten Touren** durchführen

**Risiko:** 🟡 **MITTEL** (optional, aktuell funktioniert es)

---

### 6. Phase 2.2: Layout-Persistenz für abdockbare Panels
**Status:** ✅ Panels funktionieren, Layout-Persistenz bereits implementiert (2025-11-09)

**Offene Tasks:**
- [x] Persistentes Layout (localStorage) - ✅ **BEREITS IMPLEMENTIERT**
- [x] Panel-Positionen speichern - ✅ **BEREITS IMPLEMENTIERT**
- [x] Panel-Größen speichern - ✅ **BEREITS IMPLEMENTIERT**

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT** (siehe `docs/PHASE2_VERIFICATION.md`)

---

### 7. Phase 2.3: Statistik-Detailseite im Admin
**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT** (2025-11-09)

**Offene Tasks:**
- [x] Stats-Detail-Endpoints (Tage, Monate, Export) - ✅ **FERTIG**
- [x] Charts (Chart.js) - ✅ **FERTIG**
- [x] Export-Funktion (CSV, JSON) - ✅ **FERTIG**

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT** (siehe `docs/PHASE2_VERIFICATION.md`)

---

## 🟢 NIEDRIG PRIORITÄT (Mittelfristig - Optional)

### 8. Dresden-Quadranten Frontend-Integration
**Status:** ✅ Backend implementiert, Frontend fehlt

**Offene Tasks:**
- [ ] UI für Dresden-Quadranten & Zeitbox-Planung
- [ ] Visualisierung der Sektoren auf Karte
- [ ] Sub-Routen-Anzeige

**Risiko:** 🟢 **NIEDRIG** (neue UI-Komponente)

---

### 9. Phase 3.1: Lizenzierungssystem
**Status:** ⏸️ Geplant, aber optional

**Offene Tasks:**
- [ ] Ed25519-basierte JWT-Lizenzen
- [ ] Device-Fingerprinting
- [ ] Grace-Period (Offline)
- [ ] Admin-UI für Lizenzverwaltung

**Risiko:** 🟡 **MITTEL** (neue Komponente)

---

### 10. Phase 3.2: Export & Live-Daten (weitere Features)
**Status:** 🟡 Teilweise implementiert (Live-Daten Basis vorhanden)

**Offene Tasks:**
- [ ] Maps-Export (Google/Apple URLs + QR-Codes)
- [ ] Baustellen-Overlay auf Karte (Frontend)
- [ ] Unfälle-Overlay auf Karte (Frontend)
- [ ] Sperrungen-Overlay auf Karte (Frontend)

**Risiko:** 🟡 **MITTEL** (Frontend-Erweiterungen)

---

### 11. Phase 3.3: Deployment & AI-Ops
**Status:** ⏸️ Geplant, aber optional

**Offene Tasks:**
- [ ] NSIS-Installer
- [ ] Update-Strategie (LTS, manuell)
- [ ] AI-Healthcheck (E-Mail-Alerts)
- [ ] Smoke-Tests

**Risiko:** 🟡 **MITTEL** (neue Infrastruktur)

---

## ⏸️ LANGFRISTIG (Später)

### 12. Phase 4.1: React-Migration
**Status:** ⏸️ Geplant, aber nicht sofort

**Offene Tasks:**
- [ ] Frontend von Vanilla JS zu React
- [ ] Komponenten-Migration
- [ ] State-Management

**Risiko:** 🔴 **HOCH** (große Änderung)

**Empfehlung:** Erst alle anderen Features fertig, dann React

---

## 📋 NÄCHSTE SCHRITTE (Priorisiert)

### Diese Woche:
1. ⚠️ **Live-Daten: Echte API-Integrationen** (Autobahn API, Blitzer-Daten-Quelle)
2. ⚠️ **Phase 2.1 Schema aktivieren** (wenn gewünscht)
3. ✅ **Live-Daten & Blitzer testen** (mit echten Daten)

### Nächste 2 Wochen:
1. Live-Daten: Verbesserungen (präzisere Berechnung, GPX-Import)
2. Phase 2.1 Migration durchführen (mit Backup)
3. Admin-Auth implementieren
4. Routing-Optimizer erweitern (Clustering, Valhalla/GraphHopper)

### Nächster Monat:
1. Phase 3 Features (wenn gewünscht)
2. Dresden-Quadranten Frontend-Integration
3. Frontend-Overlays für Hindernisse (Baustellen, Unfälle, Sperrungen)

---

## 🎯 ZUSAMMENFASSUNG

### ✅ Was fertig ist:
- **MVP Patchplan:** 100%
- **Phase 1:** 100%
- **Phase 2.2:** Abdockbare Panels (100%)
- **Phase 2.3:** Statistik-Detailseite (100%)
- **Live-Daten & Blitzer:** Basis-Implementierung (100%)
- **Routing-Optimizer:** Implementiert (über Plan hinaus)
- **Sub-Routen-Generator:** Vollständig implementiert & dokumentiert

### 🟡 Was teilweise fertig ist:
- **Phase 2.1:** Schema definiert, Migration-Script vorhanden, aber noch nicht aktiviert
- **Live-Daten:** Basis vorhanden, aber echte API-Integrationen fehlen
- **Routing-Optimizer:** Funktioniert, aber Clustering & Valhalla/GraphHopper fehlen

### ❌ Was noch aussteht:
- **Live-Daten:** Echte API-Integrationen (Autobahn API, Blitzer-Daten-Quelle)
- **Phase 2.1:** Schema-Aktivierung und Migration
- **Admin-Auth:** Für Produktion wichtig
- **Dresden-Quadranten:** Frontend-Integration
- **Phase 3:** Alle optionalen Features
- **Phase 4:** React-Migration (später)

---

## 📝 HINWEISE

1. **Live-Daten:** Basis ist implementiert, aber echte Datenquellen müssen noch integriert werden
2. **Blitzer:** Rechtliche Aspekte beachten (Blitzer.de bietet keine öffentliche API)
3. **Priorisierung:** Fokus auf Live-Daten-API-Integrationen und Phase 2.1 Schema-Aktivierung
4. **Risiko:** Alle geplanten Änderungen sind rollback-sicher
5. **Tests:** Nach jeder Änderung Smoke-Tests durchführen

---

**Stand:** 2025-01-10  
**Nächste Aktualisierung:** Nach Implementierung der nächsten Features

