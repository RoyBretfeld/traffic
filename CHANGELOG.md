# FAMO TrafficApp - Changelog

## Version 1.2.0 - Manuelle Koordinaten-Eingabe (2025-10-09)

### ✅ Neue Features
- **Manuelle Koordinaten-Eingabe:** Benutzer können Koordinaten für Adressen eingeben, die vom automatischen Geocoding nicht gefunden werden
- **UI-Integration:** "Koordinaten eingeben" Button im Tourplan Management für Adressen ohne Geo-Daten
- **Modal-Interface:** Benutzerfreundliches Eingabeformular für Breitengrad/Längengrad
- **API-Endpoint:** `POST /api/tourplan/manual-geo` für programmatische Koordinaten-Eingabe

### 🔧 Technische Verbesserungen
- **Datenbank-Schema erweitert:** `geo_cache` Tabelle um `source` und `by_user` Spalten
- **Migration-System:** Automatische Schema-Updates für bestehende Installationen
- **Repository-Pattern:** Erweiterte `upsert` Funktion mit Metadaten-Support
- **Validierung:** Koordinaten-Bereiche und Eingabe-Validierung

### 📊 Datenbank-Änderungen
```sql
-- Neue Spalten in geo_cache
ALTER TABLE geo_cache ADD COLUMN source TEXT DEFAULT 'geocoded';
ALTER TABLE geo_cache ADD COLUMN by_user TEXT;
```

### 🧪 Tests
- Unit-Tests für Repository-Funktionalität
- API-Endpoint-Tests mit Validierung
- Update-Verhalten-Tests für bestehende Einträge

### 📚 Dokumentation
- Vollständige API-Dokumentation
- Implementierungs-Guide
- Benutzer-Anleitung

### 🎯 Anwendungsfall
**Problem:** Adressen die vom automatischen Geocoding nicht gefunden werden, können nicht angefahren werden
**Lösung:** Manuelle Koordinaten-Eingabe über UI oder API
**Ergebnis:** 100% Abdeckung aller bestellten Kunden

### 🔄 Rückwärtskompatibilität
- Bestehende Datenbanken werden automatisch migriert
- Alte API-Endpoints bleiben unverändert
- Keine Breaking Changes

---

## Version 1.1.x - Vorherige Versionen
- Fail-Cache-System
- Alias-System für Adress-Vorschläge
- Audit-Logging
- Geocoding-Robustheit mit Retry/Backoff
- Tourplan Management UI
- Zentrale CSV-Ingest-Pipeline
- Encoding-Fixes und Mojibake-Schutz
