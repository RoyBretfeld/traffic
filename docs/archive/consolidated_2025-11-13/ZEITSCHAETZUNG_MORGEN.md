# Zeitschätzung: To-Do-Liste für morgen

## 📊 Übersicht

**Gesamt: ~15-20 Stunden** (2-3 Arbeitstage)

**Aufgeteilt nach Priorität:**

---

## 🔴 Priorität 1: Basis funktionsfähig machen (4-6 Stunden)

### 1. 404-Fehler beheben
- **Zeit:** 15-30 Minuten
- **Aufwand:** Niedrig
- **Aktivität:** Server neu starten, Test ausführen
- **Risiko:** Niedrig

### 2. LLM-Optimierung debuggen
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:** Logs analysieren, API-Key prüfen, Response-Parsing prüfen
- **Risiko:** Mittel (könnte komplexer sein wenn LLM-API Probleme hat)

### 3. Index-Mapping robuster machen
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:** Edge-Cases testen, Logging verbessern, Fallbacks prüfen
- **Risiko:** Mittel

### 4. Splitting-Logik testen & verbessern
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:** Logik durchgehen, Tests mit W-07.00, Validierung
- **Risiko:** Niedrig-Mittel

**Summe Priorität 1:** 4-6 Stunden

---

## 🟡 Priorität 2: Betriebsordnung-Migration (8-12 Stunden)

### 5. UID-System implementieren
- **Zeit:** 2-3 Stunden
- **Aufwand:** Hoch
- **Aktivität:** 
  - `tour_uid` und `stop_uid` Generierung (SHA256)
  - Datenbank-Schema erweitern
  - Migration bestehender Daten
  - Backwards-Kompatibilität
- **Risiko:** Hoch (kann bestehende Daten beeinflussen)

### 6. API-Struktur: Neue `/engine/` Endpoints
- **Zeit:** 2-3 Stunden
- **Aufwand:** Mittel-Hoch
- **Aktivität:**
  - `/engine/tours/ingest` erstellen
  - `/engine/tours/{tour_uid}/status` erstellen
  - `/engine/tours/optimize` erstellen (neue Version)
  - `/engine/tours/split` erstellen
  - Alte Endpoints als Deprecated markieren
- **Risiko:** Mittel (API-Changes, Frontend muss angepasst werden)

### 7. OSRM Table API implementieren
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:**
  - Table API Client implementieren
  - Distanz-Matrix statt einzelne Calls
  - Integration in Optimierung
- **Risiko:** Niedrig (Code bereits vorbereitet)

### 8. Reihenfolge ändern: OSRM → Heuristik → LLM
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:**
  - Code umstrukturieren
  - LLM nur als Fallback
  - Tests anpassen
- **Risiko:** Mittel (Logik-Änderungen)

### 9. LLM-Prompt umstellen: Nur UIDs
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:**
  - Prompt-Generierung ändern
  - Response-Parsing anpassen
  - Tests anpassen
- **Risiko:** Mittel (Prompt-Änderungen können Ergebnisse beeinflussen)

### 10. Set-Validierung implementieren
- **Zeit:** 30-60 Minuten
- **Aufwand:** Niedrig-Mittel
- **Aktivität:**
  - Pydantic-Schema erweitern
  - Validierung implementieren
  - Fehler-Handling (400 + Quarantäne)
- **Risiko:** Niedrig

### 11. Quarantäne-System
- **Zeit:** 2-3 Stunden
- **Aufwand:** Hoch
- **Aktivität:**
  - Datenbank-Schema für Quarantäne
  - Admin-API für Review
  - UI für Quarantäne-Verwaltung
- **Risiko:** Hoch (neues System)

### 12. Circuit-Breaker/Retry für OSRM
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:**
  - Zentraler OSRM-Client
  - Circuit-Breaker implementieren
  - Retry-Logik
  - Tests
- **Risiko:** Mittel

### 13. Index-Mapping entfernen
- **Zeit:** 1-2 Stunden
- **Aufwand:** Mittel
- **Aktivität:**
  - Code auf UIDs umstellen
  - Tests anpassen
  - Alten Code entfernen
- **Risiko:** Mittel (viele Stellen betroffen)

**Summe Priorität 2:** 8-12 Stunden

---

## 🟢 Priorität 3: Nice-to-Have (4-6 Stunden)

### 14. Geografisches Clustering (Optional)
- **Zeit:** 3-4 Stunden
- **Aufwand:** Hoch
- **Aktivität:**
  - DBSCAN/K-Means implementieren
  - Clustering vor Optimierung
  - Tests
- **Risiko:** Mittel (komplexe Logik)

### 15. Route-Visualisierung
- **Zeit:** 2-3 Stunden
- **Aufwand:** Mittel-Hoch
- **Aktivität:**
  - Backend-Endpoint für Route-Details
  - Frontend: Karten-Library integrieren
  - Modal für Route-Anzeige
- **Risiko:** Mittel

### 16. Verkehrszeiten-Service
- **Zeit:** 2-3 Stunden
- **Aufwand:** Mittel
- **Aktivität:**
  - TrafficTimeService implementieren
  - Multiplikator-Tabelle
  - UI-Anzeige
- **Risiko:** Niedrig

### 17. Dokumentation & Testing
- **Zeit:** 2-3 Stunden
- **Aufwand:** Niedrig-Mittel
- **Aktivität:**
  - Test-Suite erweitern
  - Edge-Cases dokumentieren
  - User-Guide
- **Risiko:** Niedrig

**Summe Priorität 3:** 4-6 Stunden

---

## 📈 Realistische Zeitschätzung

### Szenario 1: Nur Basis funktionsfähig (Morgen)
**Zeit:** 4-6 Stunden
- Priorität 1 Punkte
- Ergebnis: Sub-Routen-Generator funktioniert

### Szenario 2: Basis + Teilweise Migration
**Zeit:** 8-10 Stunden
- Priorität 1 + Priorität 2 (Punkte 5-9)
- Ergebnis: Funktionierend + UIDs/OSRM-First

### Szenario 3: Vollständige Migration (Realistisch)
**Zeit:** 15-20 Stunden (2-3 Tage)
- Alle Prioritäten
- Ergebnis: Vollständig nach Betriebsordnung

---

## ⚠️ Risiken & Puffer

**Kritische Risiken:**
1. **UID-Migration:** Kann bestehende Daten beeinflussen → +2 Stunden Puffer
2. **API-Changes:** Frontend muss angepasst werden → +1-2 Stunden Puffer
3. **LLM-Prompt-Änderungen:** Können Ergebnisse beeinflussen → +1 Stunde Puffer
4. **Quarantäne-System:** Neues System, unvorhersehbare Probleme → +2 Stunden Puffer

**Empfohlener Puffer:** +30% → **20-26 Stunden** insgesamt

---

## 🎯 Empfehlung für morgen

**Fokus: Priorität 1 (4-6 Stunden)**

1. 404-Fehler beheben (30 Min) ✅
2. System testen (1-2 Stunden) ✅
3. Wenn funktioniert → Migration starten (restliche Zeit)
4. Wenn nicht funktioniert → Debugging (restliche Zeit)

**Realistisch:** 6-8 Stunden Arbeit für morgen

---

## 📋 Checkliste für Zeitschätzung

- [ ] Server läuft, Endpoint erreichbar? (30 Min)
- [ ] W-07.00 kann optimiert werden? (1-2 Stunden)
- [ ] Sub-Routen werden erstellt? (1-2 Stunden)
- [ ] UI zeigt Sub-Routen korrekt? (30 Min)
- [ ] Logs zeigen keine kritischen Fehler? (30 Min)

**Minimum für "funktionsfähig":** 4-6 Stunden

