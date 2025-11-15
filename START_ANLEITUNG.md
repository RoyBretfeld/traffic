# 🚀 Start-Anleitung - FAMO TrafficApp 3.0

## ⚠️ WICHTIG: Start-Prozess

### **Docker = NUR für OSRM!**
### **TrafficApp = LOKAL im Terminal/CMD!**

---

## 📋 Start-Reihenfolge

### **1. OSRM in Docker starten** (falls nicht läuft)

```bash
docker-compose up -d osrm
```

**Prüfen ob OSRM läuft:**
```bash
docker ps | grep osrm
```

**OSRM sollte auf Port 5000 laufen:**
```bash
curl http://127.0.0.1:5000/route/v1/driving/13.388860,52.517037;13.397634,52.529407
```

---

### **2. TrafficApp LOKAL starten**

**WICHTIG:** Vor dem Start ALLE Python-Prozesse stoppen!

```powershell
# Windows PowerShell:
taskkill /F /IM python.exe /T
```

**Dann starten:**
```bash
python start_server.py
```

**ODER in CMD:**
```cmd
python start_server.py
```

---

## ✅ Prüfen ob alles läuft

### **1. Prüfe Python-Prozesse:**
```powershell
Get-Process python | Select-Object Id, StartTime
```
**Sollte nur 2 Prozesse zeigen:** Hauptprozess + Worker (normal)

### **2. Prüfe ob Server antwortet:**
```bash
curl http://127.0.0.1:8111/health
```

### **3. Prüfe OSRM:**
```bash
curl http://127.0.0.1:5000/route/v1/driving/13.388860,52.517037;13.397634,52.529407
```

---

## 🛑 Server stoppen

### **Alle Python-Prozesse stoppen:**
```powershell
taskkill /F /IM python.exe /T
```

### **OSRM stoppen:**
```bash
docker-compose stop osrm
```

---

## ⚠️ Häufige Probleme

### **Problem: "Port 8111 bereits belegt"**
**Lösung:** Es läuft noch ein alter Python-Prozess!
```powershell
taskkill /F /IM python.exe /T
```

### **Problem: "Mehrere Server-Instanzen"**
**Lösung:** Immer ALLE stoppen vor Neustart!
```powershell
Get-Process python | Stop-Process -Force
```

### **Problem: "OSRM nicht erreichbar"**
**Lösung:** OSRM-Container starten:
```bash
docker-compose up -d osrm
```

---

## 📝 Zusammenfassung

| Service | Wo läuft? | Start-Befehl |
|---------|-----------|--------------|
| **OSRM** | Docker | `docker-compose up -d osrm` |
| **TrafficApp** | Lokal (Terminal/CMD) | `python start_server.py` |

**NIEMALS:** `docker-compose up -d app` ❌  
**IMMER:** `python start_server.py` ✅

---

## 🔗 URLs nach Start

- **Hauptseite:** http://127.0.0.1:8111/
- **KI-Improvements:** http://127.0.0.1:8111/admin/ki-improvements
- **KI-Kosten:** http://127.0.0.1:8111/admin/ki-kosten
- **API Docs:** http://127.0.0.1:8111/docs

---

**Stand:** 2025-11-15

