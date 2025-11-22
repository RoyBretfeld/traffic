# Tour-Import Feature - Status 2025-11-19

## Aktueller Stand

**Datum:** 2025-11-19 20:30  
**Status:** 🟡 IN ARBEIT (Implementiert, aber nicht getestet)

---

## Was wurde implementiert

### Backend (`backend/routes/tour_import_api.py`)

1. **Upload-Endpoint** (`POST /api/import/upload`)
   - ✅ CSV-Dateien hochladen
   - ✅ ZIP-Archive entpacken und verarbeiten
   - ✅ CSV-Parsing mit `parse_tour_plan_to_dict()`
   - ✅ Kunden-Extraktion (KdNr, Name, Straße, PLZ, Stadt)
   - ✅ Speicherung in `customers` Tabelle
   - ✅ Batch-Erstellung und Statistik-Update

2. **Start-Endpoint** (`POST /api/import/batch/{batch_id}/start`)
   - ✅ Startet Geocoding-Worker im Hintergrund
   - ✅ Aktualisiert Batch-Status

3. **Geocoding-Worker** (`backend/services/geocoding_worker.py`)
   - ✅ Verarbeitet Kunden mit `geocode_status = 'pending'`
   - ✅ Geocodiert Adressen
   - ✅ Aktualisiert Koordinaten in DB

### Datenbank

- ✅ Migration `020_import_batches.sql` erstellt
- ✅ Tabellen: `import_batches`, `import_batch_items`, `customers`
- ⚠️ `touren` Tabelle existiert, aber Schema-Validierung fehlt

---

## Was fehlt noch / Probleme

### 1. Frontend-Integration

- ❓ Ruft Frontend `/api/import/upload` korrekt auf?
- ❓ Werden Dateien korrekt als `multipart/form-data` gesendet?
- ❓ Fehlerbehandlung im Frontend vorhanden?

### 2. Testing

- ❌ Noch kein Test-Upload durchgeführt
- ❌ Keine Validierung ob Kunden korrekt gespeichert werden
- ❌ Geocoding-Worker nicht getestet

### 3. Fehlerbehandlung

- ⚠️ CSV-Parsing-Fehler werden geloggt, aber nicht an Frontend zurückgegeben
- ⚠️ Validierung der CSV-Struktur fehlt
- ⚠️ Duplikat-Erkennung bei Kunden könnte verbessert werden

### 4. Datenbank-Schema

- ⚠️ `touren` Tabelle existiert, aber `status` Feld fehlt (wurde angepasst)
- ⚠️ Verknüpfung zwischen `customers` und `import_batches` fehlt

---

## Nächste Schritte (für morgen)

### 1. Server neu starten

```bash
# Alte Prozesse beenden
Get-Process python | Stop-Process -Force

# Server neu starten
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8111 --reload
```

### 2. Frontend prüfen

- Prüfe `frontend/admin/tour-import.html`
- Stelle sicher, dass Upload-Button `/api/import/upload` aufruft
- Prüfe Fehlerbehandlung

### 3. Test-Upload durchführen

1. CSV-Datei hochladen
2. Prüfe Server-Logs auf Fehler
3. Prüfe `customers` Tabelle: Werden Kunden gespeichert?
4. Prüfe `import_batches` Tabelle: Wird Batch erstellt?

### 4. Geocoding testen

1. Rufe `/api/import/batch/{batch_id}/start` auf
2. Prüfe ob Geocoding-Worker läuft
3. Prüfe ob Koordinaten in `customers` Tabelle gesetzt werden

---

## Bekannte Probleme

1. **"Hier geht garnichts"** (Benutzer-Feedback)
   - Ursache unklar - könnte Frontend-Integration oder Server-Problem sein
   - Muss getestet werden

2. **Batch-Erstellung gibt 500 Fehler**
   - Siehe LESSONS_LOG.md Eintrag "Tour-Import API: Router gibt 404"
   - Server-Neustart erforderlich

---

## Dateien

- `backend/routes/tour_import_api.py` - Haupt-Implementierung
- `backend/services/geocoding_worker.py` - Geocoding-Worker
- `db/migrations/020_import_batches.sql` - Datenbank-Migration
- `frontend/admin/tour-import.html` - Frontend (zu prüfen)

---

**Erstellt:** 2025-11-19 20:30  
**Für:** Fortsetzung morgen

