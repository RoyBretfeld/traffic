# FAMO Traffic - Installations-Anleitung

## 🚀 **Komplette Setup-Anleitung**

### ✅ **Voraussetzungen:**
- Windows 10/11 (getestet)
- Python 3.10+
- PowerShell oder Bash
- Internetverbindung

---

## 📦 **1. Projekt-Setup**

### **Schritt 1: Verzeichnis vorbereiten**
```powershell
cd "C:\Users\Bretfeld\Meine Ablage\_________FAMO"
# Projekt ist bereits in: Traffic/
cd Traffic
```

### **Schritt 2: Virtual Environment**
```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

---

## 🤖 **2. AI-System (optional)**

### **Schritt 1: Ollama installieren**
1. Download: https://ollama.ai/download/windows
2. Standardinstallation durchführen
3. Ollama starten (automatisch im Hintergrund)

### **Schritt 2: Qwen-Modell installieren**
```powershell
# In neuer PowerShell:
ollama pull qwen2.5:0.5b

# Testen:
ollama list
# Sollte qwen2.5:0.5b anzeigen
```

### **Schritt 3: Modelle-Verzeichnis (optional)**
```powershell
# Lokaler Modelle-Ordner:
$env:OLLAMA_MODELS = "C:\Users\Bretfeld\Meine Ablage\_________FAMO\Traffic\ai_models"
```

---

## 🗃️ **3. Datenbank-Setup**

### **Automatische Initialisierung:**
```powershell
# Beim ersten Start wird automatisch erstellt:
python start_server.py
```

### **Manuelle Initialisierung (falls nötig):**
```powershell
python -c "
from backend.db.schema import init_db
init_db()
print('✅ Datenbank initialisiert!')
"
```

---

## 🎯 **4. System starten**

### **Hauptserver starten:**
```powershell
cd "C:\Users\Bretfeld\Meine Ablage\_________FAMO\Traffic"
& ".\.venv\Scripts\Activate.ps1"
python start_server.py
```

### **Erfolgsmeldung:**
```
🚀 FAMO TrafficApp wird gestartet...
📍 Server läuft auf: http://127.0.0.1:8111
🌐 Frontend UI: http://127.0.0.1:8111/ui/
📚 API Docs: http://127.0.0.1:8111/docs
❌ Beenden mit: Ctrl+C
```

---

## 🌐 **5. Frontend aufrufen**

### **URLs:**
- **Haupt-UI:** http://127.0.0.1:8111/ui/
- **API-Docs:** http://127.0.0.1:8111/docs
- **Startseite:** http://127.0.0.1:8111/

Frontend zeigt Karte + Tour-Akkordeon (Parser- bzw. Workflow-Ergebnisse) mit Filtern.

---

## 📊 **6. CSV / Workflow**

- UI: Datei wählen → "Nur parsen" (Schritt 1) oder "Workflow starten" (Schritte 1–6).
- API: `POST /api/parse-csv-tourplan` bzw. `POST /api/process-csv-modular` (siehe `docs/Api_Docs.md`).

---

## 🔧 **7. Features testen**

### **Tour-Visualisierung:**
1. **Tour-Tab anklicken** → Karte zeigt Route
2. **Marker ansehen:** 🟢 FAMO, 🔵 Kunden  
3. **Rote gestrichelte Linie** = Route

### **KI-Optimierung:**
1. **Tour auswählen**
2. **"🤖 KI-Optimierung" Button** in der Sidebar
3. **Warten auf Qwen-Antwort** (2-5 Sekunden)
4. **Optimiertes Ergebnis** lesen

### **Kunden-Validierung:**
1. **"🔍 Kunden validieren" Button** klicken
2. **Ergebnis lesen:** ✅ X gültig, ❌ Y problematisch
3. **Problematische Kunden** werden aufgelistet

---

## ⚙️ **8. Konfiguration anpassen**

### **AI-Konfiguration:**
```json
# ai_models/config.json
{
  "preferred_model": "qwen2.5:0.5b",
  "fallback_models": ["qwen2.5:1.5b", "llama3.2:1b"],
  "ollama_url": "http://localhost:11434",
  "optimization_settings": {
    "temperature": 0.1,
    "top_p": 0.9,
    "num_predict": 300
  }
}
```

### **Optimierungsregeln:**
```python
# backend/services/optimization_rules.py
max_stops_per_tour: int = 8
max_driving_time_to_last_customer: int = 60  # Minuten
service_time_per_customer_minutes: int = 2   # Verweilzeit
return_trip_buffer_minutes: int = 5          # Rückfahrt-Puffer
```

---

## 🚨 **9. Troubleshooting**

### **Problem: Ollama nicht gefunden**
```powershell
# Prüfen ob Ollama läuft:
curl http://localhost:11434/api/tags

# Falls Fehler, Ollama neu starten:
ollama serve
```

### **Problem: Datenbank-Fehler**
```powershell
# Datenbank neu erstellen:
Remove-Item "data\traffic.db" -ErrorAction SilentlyContinue
python -c "from backend.db.schema import init_db; init_db()"
```

### **Problem: Port 8111 belegt**
```powershell
# Port ändern in start_server.py:
# uvicorn.run(app, host="127.0.0.1", port=8112)
```

### **Problem: Geocoding funktioniert nicht**
```powershell
# Internet-Verbindung prüfen
# Geopy-Cache löschen:
Remove-Item "data\geocache.db" -ErrorAction SilentlyContinue
```

---

## 📋 **10. System-Check**

### **Alles funktioniert wenn:**
✅ **Server startet** ohne Fehler  
✅ **http://127.0.0.1:8111/health** zeigt `{"status": "ok"}`  
✅ **Frontend lädt** Karte und Touren  
✅ **KI-Summary** wird generiert  
✅ **Kunden-Validierung** zeigt Ergebnisse  

### **Health-Check-Commands:**
```powershell
# API testen:
curl http://127.0.0.1:8111/health
curl http://127.0.0.1:8111/summary

# Ollama testen:
curl http://localhost:11434/api/tags

# Datenbank testen:
python -c "
from backend.db.dao import _connect
con = _connect()
print('Tabellen:', con.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())
"
```

---

## 🔄 **11. Updates & Wartung**

### **System-Update:**
```powershell
# Dependencies aktualisieren:
pip install -r requirements.txt --upgrade

# Ollama-Modelle aktualisieren:
ollama pull qwen2.5:0.5b
```

### **Backup wichtiger Daten:**
```powershell
# Sicherung erstellen:
Copy-Item "data\" "backup\data_$(Get-Date -Format 'yyyyMMdd')\" -Recurse
Copy-Item "ai_models\config.json" "backup\"
```

### **Logs prüfen:**
```powershell
# Server-Logs ansehen:
Get-Content "logs\server.log" -Tail 20

# Oder direkt beim Start:
python start_server.py | Tee-Object -FilePath "logs\server.log"
```

---

## 🎉 **Installation erfolgreich!**

Nach dieser Anleitung sollte FAMO Traffic vollständig funktionieren:

1. **Server läuft** auf Port 8111
2. **KI-Integration** mit Ollama aktiv
3. **Frontend** zeigt Touren und Karten
4. **Neue Features** (Kunden-Validierung) verfügbar

**Bei Problemen:** Prüfe die Troubleshooting-Sektion oder kontaktiere das Entwicklungsteam.

---

*Installations-Guide Version 2.0*  
*FAMO Traffic Optimization System*  
*Stand: $(Get-Date)*
