# FAMO TrafficApp - Server-Start Anleitung

## 🚀 Schnellstart für Vorführungen

**Einfach doppelklicken:**
- `START_SERVER_ROBUST.bat` (Windows)
- `START_SERVER_ROBUST.ps1` (PowerShell)

Das Skript behebt automatisch:
- ✅ Beschädigte Datenbanken (automatische Reparatur)
- ✅ Fehlende virtuelle Umgebung (wird erstellt)
- ✅ Fehlende Packages (werden installiert)
- ✅ Blockierte Ports (alte Prozesse werden beendet)

## 📋 Was das robuste Start-Skript macht:

1. **Prüft Server-Status** - Falls bereits läuft, öffnet Browser
2. **Beendet alte Prozesse** - Räumt blockierte Ports auf
3. **Repariert Datenbank** - Automatisch bei Beschädigung
4. **Prüft Venv** - Erstellt bei Bedarf neu
5. **Aktiviert Venv** - Stellt sicher, dass Python korrekt ist
6. **Prüft Packages** - Installiert fehlende automatisch
7. **Startet Server** - Öffnet Browser nach 3 Sekunden

## ⚠️ Wichtig für Vorführungen:

- **Keine Fehler** - Alle Probleme werden automatisch behoben
- **Keine Fragen** - Läuft vollautomatisch
- **Saubere Ausgabe** - Nur wichtige Meldungen
- **Zuverlässig** - Startet immer, auch bei Problemen

## 🔧 Manuelle Reparatur (falls nötig):

```bash
# Datenbank reparieren
python scripts\repair_db.py --auto

# Server starten
python start_server.py
```

## 📝 Logs:

- Server-Logs: `logs/`
- Port-Check-Log: `logs/port_check_*.log`
- DB-Reparatur-Backups: `backups/db_repairs/`

