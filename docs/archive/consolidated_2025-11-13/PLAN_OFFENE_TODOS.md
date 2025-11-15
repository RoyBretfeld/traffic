# Offene TODOs - FAMO TrafficApp 3.0

**Erstellt:** 2025-11-09  
**Stand:** Nach Sub-Routen-Generator Audit & kritischen Fixes

---

## 📊 Gesamtübersicht

**Phase 1:** ✅ **100% abgeschlossen**  
**Phase 2:** ✅ **100% abgeschlossen** (alle 3 Features) (Aktualisiert 2025-01-10)  
**Phase 3:** ⏸️ **0%** (optional, noch nicht begonnen)  
**Phase 4:** ⏸️ **0%** (geplant für später)

---

## 🔴 HOCH PRIORITÄT (Sofort)

### 1. Phase 2.1: Datenbank-Schema-Erweiterung aktivieren ✅
**Status:** ✅ **ABGESCHLOSSEN** (2025-01-10)

**Abgeschlossene Tasks:**
- [x] Feature-Flag aktiviert (`new_schema_enabled: true` in `config/app.yaml`)
- [x] Migration-Script erstellt (mit Backup + Rollback)
- [x] Migration durchgeführt (`stats_monthly` Tabelle erstellt)
- [x] Tests für neue Tabellen vorhanden

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

---

### 2. Phase 2.3: Statistik-Detailseite im Admin ✅
**Status:** ✅ **ABGESCHLOSSEN** (2025-01-10)

**Abgeschlossene Tasks:**
- [x] Stats-Detail-Endpoints (Tage, Monate, Export) - bereits vorhanden
- [x] Charts (Chart.js) - implementiert
- [x] Export-Funktion (CSV, JSON) - implementiert und verbessert
- [x] Statistik-Detail Tab im Admin - vollständig implementiert

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

---

### 3. Admin-Auth implementieren ✅
**Status:** ✅ **ABGESCHLOSSEN** (2025-01-10)

**Abgeschlossene Tasks:**
- [x] Auth-Check für Admin-Bereich - implementiert
- [x] Login-System (Session-basiert mit Passwort-Hash) - implementiert
- [x] Session-Management - implementiert
- [x] Login-Seite (`/admin/login.html`) - erstellt
- [x] Geschützte Routen - implementiert

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

---

## 🟡 MITTEL PRIORITÄT (Kurzfristig)

### 4. Phase 2.2: Layout-Persistenz für abdockbare Panels ✅
**Status:** ✅ **BEREITS IMPLEMENTIERT**

**Implementierte Features:**
- [x] Persistentes Layout (localStorage) - `savePanelLayout`/`loadPanelLayout`
- [x] Panel-Positionen speichern - implementiert
- [x] Panel-Größen speichern - implementiert
- [x] 7-Tage-Gültigkeit - implementiert

**Status:** ✅ **VOLLSTÄNDIG IMPLEMENTIERT**

---

### 5. Routing-Optimizer erweitern
**Status:** ✅ Implementiert, aber noch nicht vollständig getestet

**Offene Tasks:**
- [ ] Clustering für n > 80 Stopps (aktuell: NN+2-Opt)
- [ ] Valhalla/GraphHopper Integration (optional)
- [ ] Tests mit echten Touren durchführen

**Risiko:** 🟡 **MITTEL** (optional, aktuell funktioniert es)

---

### 6. Dresden-Quadranten Frontend-Integration
**Status:** ✅ Backend implementiert, Frontend fehlt

**Offene Tasks:**
- [ ] UI für Dresden-Quadranten & Zeitbox-Planung
- [ ] Visualisierung der Sektoren auf Karte
- [ ] Sub-Routen-Anzeige

**Risiko:** 🟢 **NIEDRIG** (neue UI-Komponente)

---

## 🟢 NIEDRIG PRIORITÄT (Mittelfristig - Optional)

### 7. Phase 3.1: Lizenzierungssystem
**Status:** ⏸️ Geplant, aber optional

**Offene Tasks:**
- [ ] Ed25519-basierte JWT-Lizenzen
- [ ] Device-Fingerprinting
- [ ] Grace-Period (Offline)
- [ ] Admin-UI für Lizenzverwaltung

**Risiko:** 🟡 **MITTEL** (neue Komponente)

---

### 8. Phase 3.2: Export & Live-Daten
**Status:** ⏸️ Geplant, aber optional

**Offene Tasks:**
- [ ] Maps-Export (Google/Apple URLs + QR-Codes)
- [ ] Baustellen-Overlay (Autobahn API)
- [ ] Speedcams-Overlay (mit Legal-Guard, opt-in)

**Risiko:** 🟡 **MITTEL** (externe APIs)

---

### 9. Phase 3.3: Deployment & AI-Ops
**Status:** ⏸️ Geplant, aber optional

**Offene Tasks:**
- [ ] NSIS-Installer
- [ ] Update-Strategie (LTS, manuell)
- [ ] AI-Healthcheck (E-Mail-Alerts)
- [ ] Smoke-Tests

**Risiko:** 🟡 **MITTEL** (neue Infrastruktur)

---

## ⏸️ LANGFRISTIG (Später)

### 10. Phase 4.1: React-Migration
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
1. ⚠️ **Phase 2.1 Schema aktivieren** (wenn gewünscht)
2. ⚠️ **Phase 2.3 Statistik-Detailseite** (wenn gewünscht)
3. ✅ **Routing-Optimizer testen** (mit echten Touren)

### Nächste 2 Wochen:
1. Phase 2.1 Migration durchführen (mit Backup)
2. Phase 2.3 Statistik-Detailseite implementieren
3. Admin-Auth implementieren
4. Layout-Persistenz für Panels

### Nächster Monat:
1. Phase 3 Features (wenn gewünscht)
2. Dresden-Quadranten Frontend-Integration
3. Routing-Optimizer erweitern (Clustering, Valhalla/GraphHopper)

---

## 🎯 ZUSAMMENFASSUNG

### ✅ Was fertig ist:
- **MVP Patchplan:** 100%
- **Phase 1:** 100%
- **Phase 2.2:** Abdockbare Panels funktionieren
- **Routing-Optimizer:** Implementiert (über Plan hinaus)
- **Sub-Routen-Generator:** Vollständig implementiert & dokumentiert

### 🟡 Was teilweise fertig ist:
- **Phase 2.1:** Schema definiert, aber noch nicht aktiviert
- **Phase 2.2:** Panels funktionieren, Layout-Persistenz noch offen

### ❌ Was noch aussteht:
- **Phase 2.1:** Schema-Aktivierung und Migration
- **Phase 2.3:** Statistik-Detailseite
- **Admin-Auth:** Für Produktion wichtig
- **Phase 3:** Alle optionalen Features
- **Phase 4:** React-Migration (später)

---

## 📝 HINWEISE

1. **Priorisierung:** Fokus auf Phase 2.1 und 2.3 (hohe Priorität)
2. **Risiko:** Alle geplanten Änderungen sind rollback-sicher
3. **Tests:** Nach jeder Änderung Smoke-Tests durchführen
4. **Backup:** Vor größeren Änderungen (Schema-Migration) Backup erstellen

---

**Stand:** 2025-11-09  
**Nächste Aktualisierung:** Nach Implementierung der nächsten Features

