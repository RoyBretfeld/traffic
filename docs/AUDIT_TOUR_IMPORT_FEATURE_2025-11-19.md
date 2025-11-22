# 🟡 FEATURE IN ENTWICKLUNG: Tour-Import & Vorladen

**Datum:** 2025-11-19  
**Status:** 🚧 IN ENTWICKLUNG (Grundstruktur erstellt)  
**Schweregrad:** 🟡 FEATURE (kein Fehler)  
**Dateien:** `backend/routes/tour_import_api.py`, `db/migrations/020_import_batches.sql`

---

## 🎯 Feature-Beschreibung

**Ziel:** Admin-Funktion "Tour-Import & Vorladen" für Batch-Import von Tourplänen mit automatischem Geocoding.

**Funktionen:**
1. Batch-Import vieler Tourpläne (CSV/ZIP)
2. Automatisches Geocoding im Hintergrund
3. Kunden/Adressen und Touren in DB "vorladen"
4. Import-Status und Füllstände im Adminbereich anzeigen

---

## ✅ Was wurde bereits implementiert

### 1. DB-Migration (020_import_batches.sql)
- ✅ Tabelle `import_batches` (Metadaten zu Importläufen)
- ✅ Tabelle `import_batch_items` (pro Datei im Batch)
- ✅ Tabelle `customers` (Kunden-Adress-Pool mit Geocode)
- ✅ Indizes für Performance
- ✅ Migration wird automatisch in `db/schema.py` angewendet

### 2. Backend-API-Endpunkte
- ✅ `POST /api/import/batch` - Erstellt neuen Import-Batch
- ✅ `GET /api/import/batches` - Listet alle Batches
- ✅ `GET /api/import/batch/{id}` - Ruft spezifischen Batch ab
- ✅ `GET /api/import/stats` - Globale Import-Statistiken
- ⚠️ `POST /api/import/upload` - Upload-Endpoint (Platzhalter, noch nicht implementiert)
- ⚠️ `POST /api/import/batch/{id}/start` - Startet Import (Platzhalter, noch nicht implementiert)

### 3. Router-Registrierung
- ✅ Router in `backend/app_setup.py` registriert

---

## ❌ Was noch fehlt

### 1. CSV-Parsing & Import-Worker
- ❌ CSV-Dateien parsen und in DB speichern
- ❌ ZIP-Dateien entpacken und verarbeiten
- ❌ Kunden in `customers` Tabelle anlegen
- ❌ Touren in `tours` Tabelle anlegen (Status `preloaded`)
- ❌ Tour-Stops in `tour_stops` Tabelle anlegen

### 2. Geocoding-Worker
- ❌ Hintergrund-Worker für Geocoding
- ❌ Verarbeitung von `customers` mit `geocode_status = pending`
- ❌ Koordinaten setzen und Status aktualisieren (`ok` oder `failed`)

### 3. Frontend-Admin-Seite
- ❌ `frontend/admin/tour-import.html` erstellen
- ❌ Upload-Interface (ein oder mehrere CSV/ZIP)
- ❌ Import-Batches-Tabelle mit Status
- ❌ Füllstände & Adressqualität-Anzeige
- ❌ Navigation im Admin-Bereich erweitern

### 4. Import-Profile
- ❌ Spaltenmapping je Kunde/Format
- ❌ Tabelle `import_profiles` (optional)

---

## 📋 Implementierungs-Plan

### Phase 1: CSV-Parsing (Priorität: HOCH)
1. Bestehenden CSV-Parser nutzen (`backend/parsers/tour_plan_parser.py`)
2. Upload-Handler implementieren
3. Daten in `customers` und `tours` Tabellen speichern

### Phase 2: Geocoding-Worker (Priorität: HOCH)
1. Background-Task für Geocoding erstellen
2. Bestehenden Geocoding-Service nutzen
3. Status-Updates in DB

### Phase 3: Frontend (Priorität: MITTEL)
1. Admin-Seite erstellen
2. Upload-Interface
3. Status-Anzeige
4. Navigation erweitern

### Phase 4: Nice-to-Have (Priorität: NIEDRIG)
1. Import-Profile
2. Simulation-Imports
3. Monitoring-Card im Dashboard

---

## 🔗 Verwandte Dateien

**Backend:**
- `backend/routes/tour_import_api.py` - API-Endpunkte
- `backend/parsers/tour_plan_parser.py` - CSV-Parser (bestehend)
- `backend/services/geocoding_service.py` - Geocoding-Service (bestehend)

**Datenbank:**
- `db/migrations/020_import_batches.sql` - Migration
- `db/schema.py` - Schema-Initialisierung

**Frontend:**
- `frontend/admin.html` - Admin-Hauptseite (Navigation erweitern)
- `frontend/admin/tour-import.html` - **FEHLT NOCH**

**Dokumentation:**
- `docs/TOUR_IMPORT_VORLADEN.md` - Feature-Spezifikation (vom Benutzer bereitgestellt)

---

## 🧪 Test-Plan

1. **DB-Migration testen:**
   - Tabellen werden erstellt
   - Indizes funktionieren

2. **API-Endpunkte testen:**
   - Batch erstellen
   - Batches auflisten
   - Statistiken abrufen

3. **CSV-Import testen:**
   - CSV hochladen
   - Daten werden in DB gespeichert
   - Geocoding startet automatisch

4. **Frontend testen:**
   - Upload funktioniert
   - Status wird angezeigt
   - Navigation funktioniert

---

## 📝 Notizen

- Bestehende CSV-Parser können wiederverwendet werden
- Geocoding-Service ist bereits vorhanden
- DB-Schema ist erweitert und bereit
- API-Struktur ist vorbereitet

**Nächster Schritt:** CSV-Parsing und Import-Worker implementieren

---

**Erstellt:** 2025-11-19  
**Für:** Externes Audit / KI-Entwicklung

