# 🗄️ Datenbank-Dokumentation - FAMO TrafficApp

## 📚 Übersicht

Diese Dokumentation beschreibt die komplette Datenbankstruktur der FAMO TrafficApp. Sie ist in mehrere Dateien aufgeteilt:

## 📁 Dateien

| Datei | Beschreibung | Verwendung |
|-------|--------------|------------|
| `DATABASE_SCHEMA.md` | **Hauptdokumentation** | Vollständige Beschreibung aller Tabellen, Spalten und Beziehungen |
| `database_schema.sql` | **SQL-Schema** | Ausführbares SQL-Script zum Erstellen der Datenbank |
| `DATABASE_README.md` | **Diese Datei** | Übersicht und Anleitung |

## 🚀 Schnellstart

### 1. **Datenbank erstellen**
```bash
# SQLite-Datenbank mit Schema erstellen
sqlite3 traffic.db < docs/database_schema.sql
```

### 2. **Schema validieren**
```bash
# Tabellen prüfen
sqlite3 traffic.db "SELECT name FROM sqlite_master WHERE type='table';"

# Indizes prüfen
sqlite3 traffic.db "SELECT name FROM sqlite_master WHERE type='index';"
```

### 3. **Beispieldaten laden**
```bash
# Die SQL-Datei enthält bereits Beispieldaten
# Zusätzliche Testdaten können über die API eingefügt werden
```

## 🔧 Wartung

### **Backup erstellen**
```bash
# Vollständiges Backup
sqlite3 traffic.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Nur Schema
sqlite3 traffic.db ".schema" > schema_backup.sql
```

### **Performance optimieren**
```bash
# VACUUM für Speicher-Optimierung
sqlite3 traffic.db "VACUUM;"

# ANALYZE für Query-Optimierung
sqlite3 traffic.db "ANALYZE;"
```

## 📊 Monitoring

### **Wichtige Abfragen**
```sql
-- Anzahl Kunden mit/ohne Koordinaten
SELECT 
    COUNT(*) as total_kunden,
    COUNT(lat) as mit_koordinaten,
    COUNT(*) - COUNT(lat) as ohne_koordinaten
FROM kunden;

-- Touren pro Tag
SELECT 
    datum,
    COUNT(*) as anzahl_touren,
    SUM(JSON_ARRAY_LENGTH(kunden_ids)) as total_kunden
FROM touren 
GROUP BY datum 
ORDER BY datum DESC;
```

## 🐛 Troubleshooting

### **Häufige Probleme**

1. **"no such table: tours"**
   - **Problem:** API versucht auf `tours` zuzugreifen, aber Tabelle heißt `touren`
   - **Lösung:** `backend/app.py` prüfen und `tours` → `touren` ändern

2. **"database is locked"**
   - **Problem:** Mehrere Prozesse greifen gleichzeitig auf DB zu
   - **Lösung:** Server neu starten, andere Prozesse beenden

3. **"UNIQUE constraint failed"**
   - **Problem:** Doppelte Einträge werden eingefügt
   - **Lösung:** `INSERT OR IGNORE` verwenden

### **Debug-Befehle**
```bash
# Datenbank-Status prüfen
sqlite3 traffic.db "PRAGMA integrity_check;"

# Tabellen-Größen anzeigen
sqlite3 traffic.db "SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=main.name) as count FROM sqlite_master WHERE type='table';"

# Letzte Änderungen anzeigen
sqlite3 traffic.db "SELECT * FROM kunden ORDER BY created_at DESC LIMIT 10;"
```

## 📈 Performance-Tipps

1. **Indizes nutzen** - Alle wichtigen Spalten sind indiziert
2. **Geocache verwenden** - Adressen werden gecacht
3. **JSON-Funktionen** - `JSON_ARRAY_LENGTH()` für Kunden-Zählung
4. **Views nutzen** - Vordefinierte Views für häufige Abfragen

## 🔄 Updates

### **Schema-Updates**
```bash
# 1. Backup erstellen
sqlite3 traffic.db ".backup backup_before_update.db"

# 2. Schema aktualisieren
sqlite3 traffic.db < docs/database_schema.sql

# 3. Daten migrieren (falls nötig)
# Migration-Scripts in docs/migrations/
```

### **Daten-Migration**
```bash
# Alte Daten in neue Struktur migrieren
sqlite3 traffic.db < docs/migrations/migrate_v1_to_v2.sql
```

## 📚 Weitere Dokumentation

- [API-Dokumentation](API_DOKUMENTATION.md)
- [Multi-Tour Generator](MULTI_TOUR_GENERATOR_README.md)
- [Technische Dokumentation](TECHNISCHE_DOKUMENTATION.md)
- [Installationsanleitung](INSTALLATION_GUIDE.md)

## 🤝 Support

Bei Problemen mit der Datenbank:

1. **Logs prüfen** - Server-Logs in `logs/`
2. **Backup wiederherstellen** - Falls Daten korrupt
3. **Schema neu erstellen** - Mit `database_schema.sql`
4. **Issue erstellen** - Mit detaillierter Fehlermeldung

---

*Letzte Aktualisierung: 19. August 2025*
