# ☁️ Cloud-Integration & Synchronisierung

## 📋 Übersicht

Dieses Projekt unterstützt automatische Synchronisierung zwischen dem lokalen Entwicklungsumfeld und einer Cloud-Kopie:

- **Quelle (Lokal):** `C:\Workflow\TrafficApp`
- **Ziel (Cloud):** `C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0`

## 🔄 Synchronisierung durchführen

### Option 1: PowerShell-Skript (Empfohlen)

```powershell
# Nur Dokumentationsdateien
powershell -ExecutionPolicy Bypass -File "C:\Workflow\TrafficApp\sync_documentation.ps1"

# Mit vollständiger Sync (auch docs/ Verzeichnis)
powershell -ExecutionPolicy Bypass -File "C:\Workflow\TrafficApp\sync_documentation.ps1" -FullSync
```

### Option 2: Batch-Skript (Einfach)

```cmd
# Einfach doppelklick auf:
C:\Workflow\TrafficApp\sync_documentation.bat
```

### Option 3: Manuell mit xcopy

```cmd
# Komplette Projektstruktur
xcopy "C:\Workflow\TrafficApp" "C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0" /E /I /Y

# Nur Dokumentation
xcopy "C:\Workflow\TrafficApp\*.md" "C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0\" /Y
xcopy "C:\Workflow\TrafficApp\docs" "C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0\docs" /E /I /Y
```

## 📁 Synchronisierte Dateien

Die folgenden Dateien werden automatisch synchronisiert:

- `README.md` - Hauptdokumentation
- `CHANGELOG.md` - Änderungsprotokoll
- `CURSOR_RULES.md` - Cursor-Richtlinien
- `ADRESS_ERKENNUNG_DOKUMENTATION.md` - Adresserkennung
- `SYSTEMABSCHLUSS_DOKUMENTATION.md` - Systemabschluss
- `MIGRATION_TO_OPENAI.md` - OpenAI-Migration
- `README_CSV_PARSING.md` - CSV-Parsing
- `FILE_INPUT_FIX_REPORT.md` - Datei-Input-Bericht
- `STATUS_REPORT.md` - Statusbericht
- `docs/` - Gesamtes Dokumentationsverzeichnis (mit `-FullSync`)

## ⚙️ Automatische Synchronisierung (Optional)

Für automatische Synchronisierung in regelmäßigen Intervallen können Sie einen **Windows Task Scheduler** verwenden:

### Schritt 1: Task Scheduler öffnen
```
Win + R → taskschd.msc
```

### Schritt 2: Neue Aufgabe erstellen
- **Name:** TrafficApp Cloud Sync
- **Trigger:** Täglich / Wöchentlich (nach Bedarf)
- **Aktion:** 
  ```
  powershell -ExecutionPolicy Bypass -File "C:\Workflow\TrafficApp\sync_documentation.ps1"
  ```

## 🎯 Workflow-Empfehlung

1. **Entwicklung** → lokal in `C:\Workflow\TrafficApp`
2. **Nach Dokumentations-Update** → Sync-Skript ausführen
3. **Zu Hause studieren** → Datei von `______Famo TrafficApp 3.0` öffnen

## 🔍 Überprüfung

```powershell
# Prüfen, ob Synchronisierung erfolgreich war
Compare-Object -ReferenceObject (Get-ChildItem "C:\Workflow\TrafficApp\*.md") `
               -DifferenceObject (Get-ChildItem "C:\Users\Bretfeld\Meine Ablage\______Famo TrafficApp 3.0\*.md")
```

## 💡 Tipps

- Beide Skripte **überschreiben** die Zieldateien
- Keine Konflikte - immer die neueste Version gewinnt
- Für **Code-Synchronisierung** komplett xcopy verwenden (siehe Option 3)
- Die **venv/** und **node_modules/** sind sehr groß - diese separat handhaben

## 🆘 Troubleshooting

### Fehler: "Zugriff verweigert"
- Sicherstellen, dass Windows-Benutzer Schreibrechte hat
- Evtl. als Administrator ausführen

### Fehler: "Pfad nicht gefunden"
- Pfade prüfen (mit Leerzeichen kann es Probleme geben)
- In PowerShell mit Anführungszeichen umgeben

---

**Erstellt:** October 2025  
**Letzte Aktualisierung:** October 22, 2025
