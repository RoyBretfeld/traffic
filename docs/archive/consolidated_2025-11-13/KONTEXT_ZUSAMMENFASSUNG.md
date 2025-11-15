# Kontext-Zusammenfassung für morgen

## 📌 Situation heute (01.11.2025)

### Was wurde gemacht:
1. ✅ Test-Dashboard Tests korrigiert (Geocoding, Address Corrections, Database Migrations, Database Backup)
2. ✅ Sub-Routen Generator Code verbessert (Index-Mapping robuster, Koordinaten-Validierung)
3. ✅ Fehlerbehandlung verbessert
4. ✅ Detaillierte Dokumentation erstellt (9 Dateien)

### Aktuelles Problem:
- **404-Fehler** auf `/api/tour/optimize` Endpoint
- Sub-Routen-Generator funktioniert nicht (alle 11 Touren schlagen fehl)
- Server muss wahrscheinlich neu gestartet werden

### Wichtigste Erkenntnisse:
1. **Betriebsordnung erstellt:** Klare Regeln wie implementiert werden soll
2. **Aktuelle Implementierung weicht ab:** Index-Mapping statt UIDs, LLM zuerst statt OSRM
3. **Migration erforderlich:** Schrittweise Umstellung auf Betriebsordnung

---

## 📋 To-Do-Liste für morgen

### 15 Haupt-Punkte:
1. 404-Fehler beheben (Server neu starten)
2. KI-Clustering-Engine testen
3. OSRM-Integration aktivieren
4. Route-Visualisierung implementieren
5. Verkehrszeiten-Service
6. UI-Verbesserungen
7. UID-System implementieren
8. API-Struktur (`/engine/` Endpoints)
9. OSRM Table API
10. Reihenfolge ändern (OSRM → LLM)
11. LLM-Prompt umstellen (nur UIDs)
12. Set-Validierung
13. Quarantäne-System
14. Circuit-Breaker/Retry
15. Index-Mapping entfernen

**Geschätzte Zeit:** 4-6 Stunden (Basis) bis 15-20 Stunden (komplett)

---

## 🔑 Wichtige Dateien

### Code:
- `routes/workflow_api.py` - API-Endpoint `/api/tour/optimize` (Zeile 897)
- `services/llm_optimizer.py` - LLM-Optimierung (Zeile 87)
- `frontend/index.html` - Sub-Routen Generator UI (Zeile 1956)

### Dokumentation:
- `docs/CURSOR_KI_BETRIEBSORDNUNG.md` - **WICHTIGSTE REGELN**
- `docs/CURRENT_IMPLEMENTATION_ANALYSIS.md` - Was muss geändert werden?
- `docs/START_HIER_MORGEN.md` - **START HIER morgen!**

---

## 🎯 Erfolg-Kriterien

**Minimum (4-6 Stunden):**
- ✅ 404-Fehler behoben
- ✅ W-07.00 kann optimiert werden
- ✅ Sub-Routen werden erstellt

**Optimal (8-12 Stunden):**
- ✅ Alles oben + UID-System + OSRM-First

**Vollständig (15-20 Stunden):**
- ✅ Vollständige Migration nach Betriebsordnung

---

**Status:** ✅ Alles dokumentiert, bereit für morgen!

