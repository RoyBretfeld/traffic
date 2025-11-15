# Kunden-Synonym-Tabelle

## Übersicht

Die Synonym-Tabelle (`address_synonyms`) dient dazu, Kunden auf Tourplänen mit ihren echten Kundennummern und Adressen zu verknüpfen. Dies ist besonders wichtig, wenn:
- Auf den Tourplänen keine vollständige Adresse vorhanden ist
- Die KdNr auf dem Tourplan nicht mit der echten Kundennummer übereinstimmt
- Kunden unter verschiedenen Namen/Aliasen auftreten

## Tabellenstruktur

Die Synonym-Tabelle speichert:
- **Alias:** Der Name oder die KdNr wie sie auf dem Tourplan erscheint
- **Customer ID:** Die echte Kundennummer aus dem ERP-System
- **Adresse:** Straße, PLZ, Stadt (falls vorhanden)
- **Priorität:** Höhere Priorität für KdNr-Lookups (2) vs. Name-Lookups (1)

## Importierte Synonyme

Basierend auf der E-Mail-Liste wurden folgende Synonyme importiert:

### Format: Tourplan-KdNr → Echte KdNr / Adresse

| Tourplan-KdNr | Alias-Name | Echte KdNr | Adresse | Notiz |
|--------------|------------|------------|---------|-------|
| 4993 | Sven PF | 5287 | Str. des 17. Juni 11, 01257 Dresden | ✅ Vollständig | Auto Werft Dresden |
| 4993 | Jochen PF | 5000 | Bärensteiner Str. 27-29, 01277 Dresden | ✅ Vollständig | MotorMafia |
| ~~6000~~ | ~~Büttner~~ | 4318 | ~~Steigerstr. 1, 01705 Freital~~ | ✅ Erkannt | Peuget Büttner |
| 44993 | AG | 40589 | Dresdner Straße 46, 01796 Pirna | ✅ Vollständig | Werk A KfZ Werkstatt |
| 4993 | Schrage/Johne PF | 4169 | Friedrich-List-Platz 2, 01069 Dresden | ✅ Vollständig | SachsenNetze GmbH |
| ~~4727~~ | ~~MSM~~ | 5236 | ~~Fröbelstraße 20, 01159 Dresden~~ | ✅ Erkannt |
| ~~6000~~ | ~~MSM~~ | 5236 | ~~Fröbelstraße 20, 01159 Dresden~~ | ✅ Erkannt |
| 40721 | Motor Mafia | 5000 | Bärensteiner Str. 27-29, 01277 Dresden | ✅ Erkannt |
| - | ~~MFH PF~~ | 5236 | ~~Fröbelstraße 20, 01159 Dresden~~ | ✅ Erkannt |
| 4993 | 36 Nici zu RP | 4601 | Mügelner Str. 29, 01237 Dresden | ✅ Vollständig | Automatikgetriebeservice |
| ~~4727~~ | ~~Hubraum~~ | 5236 | ~~Fröbelstraße 20, 01159 Dresden~~ | ✅ Erkannt |
| ~~4916~~ | ~~Astral UG~~ | 5525 | ~~Löbtauer Straße 80, 01159 Dresden~~ | ✅ Erkannt |
| 4993 | Peter Söllner | 4426 | August Bebel Strasse 82, 01728 Bannewitz | ✅ Vollständig | Kfz-Meisterbetrieb Söllner |
| 4993 | Jens Spahn PF | 4043 | Burgker Straße 145, 01705 Freital | ✅ Vollständig | autoBURGK Lohse |
| ~~44993~~ | ~~Schleich~~ | - | ~~Liebstädter Str. 45, 01796 Pirna~~ | ✅ Erkannt |
| 5461 | Blumentritt | 2118 | Straße des 17. Juni 16, 01257 Dresden | ✅ Vollständig | Blumentritt Diesel-Einspritztechnik |

## Automatische Auflösung beim CSV-Parsen

Wenn beim Einlesen einer CSV-Datei eine Adresse fehlt, wird automatisch in der Synonym-Tabelle gesucht:

1. **KdNr-Lookup:** Suche nach `KdNr:{customer_number}` (höchste Priorität)
2. **Name-Lookup:** Falls keine Adresse gefunden, suche nach Kundennamen

### Implementierung

In `backend/parsers/tour_plan_parser.py`:
- Prüft ob `street`, `postal_code` und `city` vorhanden sind
- Wenn nicht: Öffnet `SynonymStore` und sucht nach:
  - `KdNr:{customer_number}` (z.B. "KdNr:4993")
  - Oder nach `name` (z.B. "Sven PF")
- Wenn Synonym gefunden: Verwendet Adresse aus Synonym
- Speichert `real_customer_id` im Customer-Dict für weitere Verarbeitung

## Verwaltung

### Synonyme importieren

```bash
python scripts/import_customer_synonyms.py
```

### Neue Synonyme hinzufügen

1. Bearbeite `scripts/import_customer_synonyms.py`
2. Füge Eintrag zur `SYNONYM_DATA` Liste hinzu:
```python
{
    "tourplan_kdnr": "4993",  # KdNr auf Tourplan (optional)
    "alias": "Neuer Kunde",    # Name wie auf Tourplan
    "real_customer_id": "1234", # Echte KdNr
    "address": "Straße 1, 01001 Dresden",  # Adresse (optional)
    "note": "PF"  # Zusatzinfo (optional)
}
```
3. Führe Import-Script erneut aus

### Synonyme auflisten

Die Synonyme können über die Synonym-Store API abgerufen werden:
```python
from backend.services.synonyms import SynonymStore
store = SynonymStore("data/traffic.db")
synonyms = store.list_all(limit=200, active_only=True)
```

## Erweiterungen (Montag geplant)

Wenn der Zugriff auf den Kundenstamm wiederhergestellt ist:
1. Adressen für alle Synonyme vervollständigen
2. Fehlende Einträge hinzufügen
3. Koordinaten ergänzen (falls bekannt)
4. Validierung gegen echten Kundenstamm durchführen

## Verwendung im Workflow

1. **CSV-Upload:** Beim Parsen wird automatisch nach Synonymen gesucht
2. **Geocoding:** Wenn Synonym Adresse enthält, wird diese verwendet
3. **Display:** `real_customer_id` wird im Frontend angezeigt (falls vorhanden)

## Datenbank-Schema

```sql
CREATE TABLE address_synonyms (
  alias TEXT PRIMARY KEY,
  alias_norm TEXT NOT NULL,
  customer_id TEXT,
  customer_name TEXT,
  street TEXT,
  postal_code TEXT,
  city TEXT,
  country TEXT DEFAULT 'DE',
  lat REAL,
  lon REAL,
  note TEXT,
  active INTEGER DEFAULT 1,
  priority INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

## Prioritäten

- **Priority 2:** KdNr-Lookups (`KdNr:{kdnr}`) - höchste Priorität
- **Priority 1:** Name-Lookups - normale Priorität
- **Priority 0:** Sonstige Synonyme - niedrigste Priorität

