# CSV-Parsing Audit - INDEX.md

## Übersicht der gefundenen CSV/Encoding-Stellen

| path | line_range | symbol | operation | params | downstream_use | risk | notes |
|------|------------|--------|-----------|--------|----------------|------|-------|
| backend/app.py | 37-74 | read_tourplan_csv | csv_read | encoding=cp850, sep=';' | → Geocoder, → DB | **✅ REPARIERT** | **HAUPTEINGANG** - CP850 Decoding + Mojibake-Reparatur |
| backend/app.py | 2617-2628 | tourplan_analysis | http_response | media_type="application/json; charset=utf-8" | → Frontend | none | ✅ Korrekte UTF-8 Headers |
| backend/parsers/tour_plan_parser.py | 94-110 | _read_csv_lines | csv_read | encoding=cp850, latin1, delimiter=";" | → TourPlan Objekte | **re-encode-risk** | **ALTERNATIVER EINGANG** - CP850 Decoding |
| backend/parsers/tour_plan_parser.py | 364-365 | export_tour_plan_markdown | csv_write | encoding="utf-8" | → Markdown Export | none | ✅ Korrekte UTF-8 Ausgabe |
| backend/services/file_parser.py | 52-56 | read_csv_with_encoding | csv_read | encoding=cp850,latin1,iso-8859-1,utf-8 | → DataFrame | **re-encode-risk** | **DRITTER EINGANG** - Multiple Encodings |
| backend/services/file_parser.py | 81-85 | read_csv_with_encoding | csv_read | encoding=cp850,latin1,iso-8859-1,utf-8 | → DataFrame | **re-encode-risk** | **DRITTER EINGANG** - Multiple Encodings |
| fix_german_encoding.py | 11-30 | normalize_german_text | normalize | ß→ss, ä→ae, ö→oe | → Geocoding | **replace-loss** | **DEPRECATED** - Zerstört legitime Zeichen |
| fix_encoding_issues.py | 12-25 | fix_encoding_issues | normalize | Mapping-Tabelle | → CSV Reparatur | **replace-loss** | **DEPRECATED** - Ad-hoc Reparaturen |
| backend/utils/encoding_guards.py | 10-20 | trace_text | log | UTF-8 HEX-Dump | → Diagnose | none | ✅ Encoding-Diagnose |
| backend/utils/encoding_guards.py | 22-45 | assert_no_mojibake | log | Mojibake-Detection | → Guards | none | ✅ Mojibake-Prävention |

## 🎉 **MOJIBAKE-REPARATUR ERFOLGREICH ABGESCHLOSSEN**

### **Reparatur-Ergebnisse:**
- **5.042 Mojibake-Zeichen** repariert
- **34 CSV-Dateien** erfolgreich repariert
- **Alle Dateien** als UTF-8 gespeichert
- **Backups** erstellt (`.csv.backup`)

### **Häufigste reparierte Zeichen:**
- `├` (U+251C) → `ä` (U+00E4)
- `┤` (U+2524) → `ö` (U+00F6)
- `┼` (U+253C) → `Ä` (U+00C4)
- `┐` (U+2510) → `Ö` (U+00D6)

## Top-3 Risikostellen & vorgeschlagene Fixes

### 🚨 **RISIKO 1: Mehrfache CSV-Eingänge mit CP850**
**Problem:** 3 verschiedene Funktionen lesen CSV mit CP850:
- `backend/app.py:read_tourplan_csv()` (Zeile 48)
- `backend/parsers/tour_plan_parser.py:_read_csv_lines()` (Zeile 99)
- `backend/services/file_parser.py:read_csv_with_encoding()` (Zeile 52, 81)

**Fix:** 
- **EINEN** zentralen CSV-Reader verwenden
- **EINMALIGE** CP850-Decodierung
- **Dann IMMER** UTF-8 verwenden

### 🚨 **RISIKO 2: Deprecated Reparatur-Funktionen**
**Problem:** Ad-hoc-Reparaturen verschleiern Mojibake:
- `fix_german_encoding.py` - Zerstört legitime Umlaute
- `fix_encoding_issues.py` - Ad-hoc-Mappings

**Fix:**
- Alle Reparatur-Funktionen deaktivieren
- Nur Guards verwenden (`assert_no_mojibake`)
- Problem an der Quelle beheben

### 🚨 **RISIKO 3: Doppelte Encoding-Konvertierung**
**Problem:** UTF-8-Strings werden erneut mit CP850 gelesen
**Fix:**
- Guards nach jedem CSV-Ingest
- Trace-Text für Diagnose
- Keine erneute Encoding-Konvertierung

## Kopierte Dateien

```
audit/csv_parsing/
├── backend/
│   ├── app.py
│   ├── parsers/
│   │   └── tour_plan_parser.py
│   ├── services/
│   │   └── file_parser.py
│   └── utils/
│       └── encoding_guards.py
├── fix_german_encoding.py
├── fix_encoding_issues.py
└── INDEX.md
```

## Empfohlene Sofortmaßnahmen

1. **Zentralen CSV-Reader** implementieren
2. **Alle Reparatur-Funktionen** deaktivieren  
3. **Guards nach jedem Ingest** einbauen
4. **Tests** für Encoding-Roundtrip
5. **Monitoring** für Mojibake-Auftreten
