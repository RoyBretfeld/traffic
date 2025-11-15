# TODO-Liste für morgen: Sub-Routen Generator & AI-Integration

## 🎯 Hauptziel

**Sub-Routen-Generierung für W-Touren zum Laufen bringen**

Insbesondere: W-07.00 mit 30 Adressen → 3-4 optimierte Sub-Routen

---

## ✅ Schritt 1: 404-Fehler beheben

**Problem:** `/api/tour/optimize` gibt 404 zurück

**Aktionen:**
- [ ] Server neu starten (`python start_server.py`)
- [ ] Endpoint testen: `http://127.0.0.1:8111/docs` → `/api/tour/optimize` sollte sichtbar sein
- [ ] Test-Skript ausführen: `python scripts/test_optimize_endpoint.py`
- [ ] Prüfen ob Router korrekt registriert ist in `backend/app.py`

**Erfolg-Kriterium:** Endpoint antwortet mit 200 statt 404

---

## ✅ Schritt 2: LLM-Optimierung debuggen

**Problem:** Warum schlägt LLM-Optimierung fehl?

**Aktionen:**
- [ ] Server-Logs prüfen: `[TOUR-OPTIMIZE] LLM-Fehler` Meldungen
- [ ] OpenAI API-Key prüfen: Ist er gesetzt? (`OPENAI_API_KEY`)
- [ ] LLM-Response prüfen: Wird JSON korrekt geparst?
- [ ] Fallback-Logik testen: Funktioniert Nearest-Neighbor wenn LLM fehlschlägt?

**Erfolg-Kriterium:** LLM gibt optimierte Route zurück ODER Fallback funktioniert

---

## ✅ Schritt 3: Index-Mapping robuster machen

**Problem:** Index-Mapping schlägt manchmal fehl

**Aktionen:**
- [ ] Koordinaten-Match-Toleranz prüfen (aktuell: 0.0001)
- [ ] Fallback für fehlende Matches testen
- [ ] Logging verbessern: Welche Stopps können nicht gemappt werden?
- [ ] Edge-Cases testen: Was wenn Koordinaten identisch sind?

**Erfolg-Kriterium:** Alle Stopps werden korrekt gemappt, auch bei Edge-Cases

---

## ✅ Schritt 4: Splitting-Logik testen & verbessern

**Problem:** Wie funktioniert das Splitting genau?

**Aktionen:**
- [ ] `splitTourIntoSubRoutes()` Logik durchgehen
- [ ] Test mit W-07.00 (30 Stopps, 105 Min)
- [ ] Prüfen: Werden Sub-Routen korrekt erstellt?
- [ ] Prüfen: Sind alle Stopps enthalten? (keine fehlenden)
- [ ] Prüfen: Sind alle Sub-Routen < 60 Minuten?

**Erfolg-Kriterium:** W-07.00 wird in 3-4 Sub-Routen aufgeteilt, alle < 60 Min

---

## ✅ Schritt 5: Geografisches Clustering (Optional)

**Ideen für intelligenteres Splitting:**

**Aktionen:**
- [ ] Clustering-Logik analysieren: Sollte VOR Optimierung passieren?
- [ ] K-Means oder DBSCAN für geografische Gruppierung
- [ ] Clustering dann optimieren innerhalb jedes Clusters
- [ ] Clustering-basierte Aufteilung statt sequenzielles Splitting

**Erfolg-Kriterium:** Sub-Routen sind geografisch kohärent (keine "Sprung"-Routen)

---

## ✅ Schritt 6: Dokumentation & Testing

**Aktionen:**
- [ ] Vollständige Test-Suite für Sub-Routen-Generator
- [ ] Edge-Cases dokumentieren (1 Stopp, 100 Stopps, keine Koordinaten, etc.)
- [ ] Performance-Tests (wie lange dauert Optimierung für 30 Stopps?)
- [ ] User-Guide für Sub-Routen-Generator erstellen

**Erfolg-Kriterium:** Dokumentation vollständig, Tests laufen

---

## 🔍 Debugging-Strategie

### Wenn 404-Fehler weiterhin auftritt:

1. **Server-Logs prüfen:**
   ```bash
   # Im Server-Terminal
   # Suche nach: "include_router" oder "workflow_api"
   ```

2. **Router-Registrierung prüfen:**
   ```python
   # backend/app.py Zeile 75
   app.include_router(workflow_api_router)
   ```

3. **Endpoint manuell testen:**
   ```bash
   python scripts/test_optimize_endpoint.py
   ```

### Wenn LLM-Optimierung fehlschlägt:

1. **API-Key prüfen:**
   ```bash
   echo $OPENAI_API_KEY  # Linux/Mac
   echo %OPENAI_API_KEY% # Windows
   ```

2. **Server-Logs prüfen:**
   - Suche nach: `[TOUR-OPTIMIZE] LLM-Fehler`
   - Prüfe Traceback

3. **Fallback testen:**
   - LLM temporär deaktivieren
   - Prüfe ob Nearest-Neighbor funktioniert

### Wenn Index-Mapping fehlschlägt:

1. **Koordinaten prüfen:**
   - Sind alle Koordinaten gültig? (-90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180)
   - Gibt es Duplikate?

2. **Mapping-Logik debuggen:**
   - Logge `valid_stops` und `optimized_stops_list`
   - Prüfe welche Stopps nicht gemappt werden können

---

## 📋 Test-Checkliste

### Vor Tests:
- [ ] Server läuft auf `http://127.0.0.1:8111`
- [ ] CSV-Datei mit W-Touren hochgeladen
- [ ] Mindestens eine W-Tour mit > 10 Stopps vorhanden

### Während Tests:
- [ ] Browser-Konsole offen (F12)
- [ ] Server-Terminal sichtbar für Backend-Logs
- [ ] Netzwerk-Tab prüfen (F12 → Network)

### Nach Tests:
- [ ] Prüfe ob Sub-Routen erstellt wurden
- [ ] Prüfe ob alle Stopps enthalten sind
- [ ] Prüfe ob Zeit-Berechnungen korrekt sind
- [ ] Prüfe ob UI aktualisiert wurde

---

## 🎯 Erfolg-Metriken

**Morgen ist erfolgreich wenn:**
- ✅ `/api/tour/optimize` Endpoint funktioniert (kein 404)
- ✅ W-07.00 (30 Stopps) wird in 3-4 Sub-Routen aufgeteilt
- ✅ Alle Sub-Routen sind < 60 Minuten
- ✅ Alle 30 Stopps sind in Sub-Routen enthalten (keine fehlenden)
- ✅ UI zeigt Sub-Routen korrekt an

---

## 💡 Offene Fragen

1. **Soll geografisches Clustering VOR Optimierung passieren?**
   - Aktuell: Optimierung → Splitting
   - Alternative: Clustering → Optimierung innerhalb Cluster → Splitting

2. **Wie intelligent soll das Splitting sein?**
   - Aktuell: Sequenziell (Stopp 0-9, 10-19, 20-29)
   - Alternative: Intelligent (geografische Gruppen)

3. **Was wenn eine Sub-Route > 60 Min ist (auch nach Splitting)?**
   - Aktuell: Wird trotzdem erstellt
   - Alternative: Weiter splitten oder Warnung?

4. **Soll FAMO-Depot Start/Ende sein?**
   - Aktuell: Ja, wird in Zeitberechnung berücksichtigt
   - Alternative: Optional?

---

## 📚 Referenzen

- **Dokumentation:** `docs/SUB_ROUTES_GENERATOR_LOGIC.md`
- **Code:** 
  - Frontend: `frontend/index.html` → `generateSubRoutes()`
  - Backend: `routes/workflow_api.py` → `optimize_tour_with_ai()`
  - AI: `services/llm_optimizer.py` → `optimize_route()`
- **Logging-Guide:** `docs/LOGGING_GUIDE.md`

---

**Viel Erfolg morgen! 🚀**

