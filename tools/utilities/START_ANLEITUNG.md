# 🚀 FAMO TrafficApp - Start-Anleitung

## ⚡ Schnellstart

### **Option 1: Doppelklick auf `start.bat`** (Empfohlen)
1. Doppelklick auf **`start.bat`** im Projektordner
2. Der Server startet automatisch
3. Der Browser öffnet sich nach 3 Sekunden auf: http://127.0.0.1:8111
4. Das Konsolenfenster zeigt alle Server-Logs

### **Option 2: Manueller Start**
```cmd
cd C:\Workflow\TrafficApp
venv\Scripts\activate.bat
python start_server.py
```

### **Option 3: Stiller Start (Hintergrund)**
1. Doppelklick auf **`start_silent.bat`**
2. Server startet ohne Konsolenfenster
3. Browser öffnet sich automatisch

---

## 🛑 Server stoppen

### **Option 1: Doppelklick auf `stop.bat`**
- Stoppt alle laufenden Server-Prozesse

### **Option 2: Im Konsolenfenster**
- Drücke `Ctrl + C` im Server-Konsolenfenster

---

## 📝 Wichtige URLs

| URL | Beschreibung |
|-----|-------------|
| http://127.0.0.1:8111 | **Haupt-Frontend** (Karte + Touren) |
| http://127.0.0.1:8111/docs | API-Dokumentation (Swagger) |
| http://127.0.0.1:8111/health | Server-Health-Check |

---

## 🧪 Testen der neuen Geocoding-Funktion

1. **Server starten** mit `start.bat`
2. **CSV hochladen**: 
   - Datei auswählen (z.B. "Tourenplan 18.08.2025.csv")
   - Button **"Nur parsen (Schritt 1)"** klicken
3. **Warten**: Der Server geokodiert jetzt ALLE Adressen
4. **Ergebnis**:
   - Statistik wird angezeigt: "🌍 Geocoding: 45/50 erfolgreich (90%)"
   - Tour anklicken → Karte zeigt alle Punkte
   - **GRÜNE Zeilen** = Adresse gefunden ✅
   - **ROTE Zeilen** = Adresse nicht gefunden ❌

---

## ⚙️ Erstmaliges Setup

Falls der Server nicht startet, prüfe:

### 1. **Virtuelle Umgebung vorhanden?**
```cmd
dir venv\Scripts\python.exe
```
Falls nicht vorhanden:
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. **Dependencies installiert?**
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 3. **Port 8111 frei?**
Prüfe, ob ein anderer Prozess Port 8111 nutzt:
```cmd
netstat -ano | findstr :8111
```
Falls ja, Prozess beenden oder Port in `start_server.py` ändern.

---

## 🐛 Troubleshooting

### Problem: "Server läuft bereits"
```cmd
stop.bat
start.bat
```

### Problem: "Module not found"
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Problem: Browser öffnet sich nicht automatisch
- Öffne manuell: http://127.0.0.1:8111

### Problem: "Verbindung fehlgeschlagen"
- Prüfe Server-Logs im Konsolenfenster
- Firewall/Antivirus prüfen
- Port 8111 prüfen (siehe oben)

---

## 📊 Was wurde heute implementiert?

### ✅ **STUFE 1: Automatisches Geocoding** (FERTIG!)

1. **Backend** (`backend/app.py`):
   - `/api/parse-csv-tourplan` geokodiert jetzt ALLE Adressen beim Upload
   - Detaillierte Statistik: Erfolg/Fehler-Rate
   - Koordinaten werden direkt gespeichert

2. **Frontend** (`frontend/index.html`):
   - Ladeanimation während des Geocodings
   - Anzeige der Geocoding-Statistik
   - Rote Zeilen nur für fehlgeschlagene Adressen
   - Grüner Haken ✅ / Rotes Kreuz ❌ pro Adresse

3. **Start-Dateien**:
   - `start.bat` - Normaler Start mit Logs
   - `start_silent.bat` - Stiller Hintergrund-Start
   - `stop.bat` - Server stoppen

### 🔜 **Nächste Schritte (STUFE 2 + 3)**:
1. Export der fehlgeschlagenen Adressen
2. AddressCorrector verbessern
3. Manuelle Korrektur-UI für rote Zeilen

---

## 💡 Tipps

- **Geocoding-Cache**: Bereits geokodierte Adressen werden gecacht (schneller bei erneutem Upload)
- **Server-Logs**: Im Konsolenfenster siehst du alle Geocoding-Vorgänge
- **Entwicklungsmodus**: Auto-Reload bei Code-Änderungen aktiv

---

**Viel Erfolg! 🚀**

