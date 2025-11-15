# 🚀 FAMO TrafficApp

**Intelligente Tourenplanungs- und Routenoptimierungsanwendung mit KI-Integration**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Status](https://img.shields.io/badge/Status-Produktionsbereit-brightgreen.svg)](https://github.com/famo/trafficapp)

## 🎯 **Übersicht**

Die FAMO TrafficApp ist eine modulare, KI-gestützte Anwendung zur Tourenplanung. Grundlage ist ein 8-Schritte-Workflow (siehe `docs/Neu/Neue Prompts.md`), der CSV-Tourpläne einliest, normalisiert, geokodiert, clustert, optimiert und im Frontend mit KI-Kommentaren darstellt.

### ✨ **Hauptfeatures (Stand 30.09.2025)**

- 🧱 **8-Schritte-Pipeline**: Parser ➝ Geokodierung ➝ Zeitmatrix ➝ Clustering ➝ TSP ➝ KI-Kommentare ➝ Frontend ➝ Logging.
- 📄 **Neuer CSV-Parser** (`backend/parsers/tour_plan_parser.py`) mit BAR-Zuordnung & Duplikatfilter.
- 🧮 **Workflow-Orchestrator** (`backend/services/workflow_orchestrator.py`) für komplette Verarbeitung.
- 🗺️ **Frontend-Akkordeon** (unter Karte) für Tourübersicht inkl. Filter & BAR-Markierung.
- 🤖 **KI-Optimierung & Erklärungen** via `ai_optimizer.py` (Ollama/Qwen); RAG/Vectorstore-Integration (FAQ, historische Antworten) als nächster Ausbauschritt vorgesehen.
- 📚 **Clustering-Logik dokumentiert** (`docs/Neu/Neue Prompts.md`): Sweep-Heuristik, 60-Minuten-Budget, BAR-Kunden-Regeln.
- 📚 **Aktualisierte Doku** (`docs/Api_Docs.md`, `docs/FAMO_TrafficApp_MasterDoku.md`, `docs/Architecture.md`).

## 🚀 **Schnellstart**

### **Voraussetzungen**

- Python 3.10+ (empfohlen: 3.13.1)
- Ollama (für lokale KI-Modelle)
- Git

### **Installation**

```bash
# Repository klonen
git clone <repository-url>
cd TrafficApp

# Virtuelle Umgebung erstellen
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Dependencies installieren
pip install -r requirements.txt

# Ollama-Modelle installieren
ollama pull qwen2.5:0.5b
ollama pull llama3.2:1b
```

### **Server starten**

```bash
# Einfach
python start_server.py

# Oder direkt
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

### **Anwendung öffnen**

Öffne deinen Browser und gehe zu: **http://127.0.0.1:8000** (FastAPI UI) oder **http://127.0.0.1:8111/ui/** (Workflow-Frontend via `start_server.py`).

## 📁 **Projektstruktur**

```
TrafficApp/
├── backend/                 # FastAPI Backend
│   ├── app.py              # Hauptanwendung
│   ├── services/           # Business Logic
│   │   ├── workflow_orchestrator.py # Orchestriert Schritte 1–6
│   │   ├── multi_tour_generator.py  # Sweep-Heuristik + KI
│   │   ├── ai_optimizer.py          # KI-Optimierung/Kommentare
│   │   └── geocode.py               # Geokodierung + Fallbacks
│   └── parsers/
│       ├── tour_plan_parser.py      # Neuer CSV-Tourplan-Parser
│       └── excel_parser.py          # (Legacy) Excel-Support
├── frontend/               # Web-Interface
│   └── index.html         # 🎨 Hauptseite
├── ai_models/             # KI-Modelle & Konfiguration
│   ├── config.json        # 🤖 KI-Einstellungen
│   └── setup_ollama.ps1   # 🚀 Ollama-Setup
├── tourplaene/            # 📁 CSV-Tourenpläne
├── docs/                  # 📚 Dokumentation & Toolbox
│   ├── toolbox.html       # 🛠️ Web-Toolbox
│   └── csv_bulk_processor.py
└── requirements.txt       # 📦 Python-Dependencies
```

## 🎮 **Verwendung**

1. **CSV hochladen (Schritt 1):** `/api/parse-csv-tourplan` oder UI-Link „Nur parsen“.
2. **Kompletten Workflow ausführen:** `/api/process-csv-modular` oder UI-Button „Workflow starten“.
3. **Tourübersicht** (Frontend `/ui/`): Karte + Akkordeon mit Tourdaten, BAR-Kennzeichnung, Statistiken.
4. **Filter & Kommentare**: Tourtyp-, BAR-, Datumsfilter; Workflow-Anzeige im Sidebar.
5. **Legacy-Bulk** (`/api/csv-bulk-process`) bleibt vorerst verfügbar, wird jedoch durch neue Pipeline ersetzt.

## 🤖 **KI-Integration**

Primär local (Ollama/Qwen). LLM liefert Optimierungsvorschläge und Kommentare (Schritt 5/6). Fallbacks (OpenAI) können in `ai_models/config.json` hinterlegt werden.

## 📊 **Unterstützte Formate**

Empfohlen: Semikolon-separierte CSV im TEHA-Layout, Encoding `latin1`/`cp1252`. Excel-Import bleibt (Legacy) möglich, wird aber nicht mehr aktiv weiterentwickelt.

## 🔧 **Konfiguration**

### **Umgebungsvariablen** (Auszug)
```bash
# KI-API-Keys (optional)
OPENAI_API_KEY=your_openai_key

# Ollama-Konfiguration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODELS=C:\Workflow\TrafficApp\ai_models
```

Siehe `ai_models/config.json` und `backend/services/optimization_rules.py`.

## 📚 **Dokumentation**

- **[Vollständige Projektdokumentation](PROJEKT_DOKUMENTATION_FINAL.md)**
- **[Detailliertes Changelog](CHANGELOG_FINAL.md)**
- **[API-Dokumentation](http://127.0.0.1:8000/docs)** (nach Server-Start)
- **[Code-Kommentare](backend/)** für Entwickler

## 🧪 **Testing**

```bash
# Parser Golden-Test (alle Tourenpläne)
python scripts/test_csv_parser.py

# API Smoke-Tests (pytest)
pytest tests/test_api_health.py
```

## 🐛 **Fehlerbehebung**

### **Häufige Probleme**

#### **Ollama läuft nicht**
```bash
# Ollama starten
ollama serve

# Modell installieren
ollama pull qwen2.5:0.5b
```

#### **CSV-Parsing-Fehler**
- Prüfe Encoding (latin1/cp1252) und Semikolon als Trennzeichen.
- Sicherstellen, dass Datei dem TEHA-Layout folgt (Tourkopf + Kundenzeilen).

#### **Workflow-Fehler**
- Siehe `/api/workflow-info` oder Log-Einträge in `logs/csv_import_debug.log`.
- Workflow-UI zeigt Status pro Schritt.
## 🔮 **Roadmap**

Siehe `docs/FORTSCHRITT_22_09_2025.md` und `docs/ToDo.md` für den aktuellen Plan.

## 🤝 **Beitragen**

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Erstelle einen Pull Request

## 📄 **Lizenz**

Dieses Projekt ist proprietär und gehört FAMO.

## 📞 **Support**

- **Dokumentation**: Siehe oben verlinkte Dokumentationsdateien
- **API-Docs**: http://127.0.0.1:8000/docs (nach Server-Start)
- **Issues**: GitHub Issues für Bug-Reports

## 🎉 **Fazit**

Aktueller Stand (09/2025): Parser + Workflow neu, Frontend prototypisch, Routing/DB-Integration in Modernisierung. Hinweise & Details in `docs/Api_Docs.md`, `docs/FAMO_TrafficApp_MasterDoku.md`, `docs/Architecture.md`.
