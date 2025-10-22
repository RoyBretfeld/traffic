# MIGRATION VON OLLAMA ZU OPENAI API

## 🎯 ZIEL
Ersetze lokale Ollama-Modelle durch OpenAI API für bessere Proxmox-Kompatibilität.

## 📋 SCHRITTE

### 1. OpenAI API-Key besorgen
```bash
# Gehe zu: https://platform.openai.com/api-keys
# Erstelle neuen API-Key
# Kopiere den Key
```

### 2. Umgebungsvariable setzen
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your_key_here"

# Linux/Mac
export OPENAI_API_KEY="your_key_here"

# Oder in .env Datei
echo "OPENAI_API_KEY=your_key_here" > .env
```

### 3. Konfiguration aktualisieren
```bash
python migrate_to_openai.py
```

### 4. Testen
```bash
python openai_integration.py
```

## ✅ VORTEILE

- **Netzwerkunabhängig:** Keine lokalen Modelle nötig
- **Keine Updates:** API bleibt stabil
- **Weniger Ressourcen:** Kein lokaler Speicher/CPU-Verbrauch
- **Zuverlässiger:** Professionelle Infrastruktur
- **Einfacher:** Keine Modell-Verwaltung

## 🔧 KOSTEN

- **gpt-4o-mini:** ~$0.15 pro 1M Input-Tokens, ~$0.60 pro 1M Output-Tokens
- **Typische Tourenplanung:** ~$0.001-0.01 pro Optimierung
- **Monatliche Kosten:** Geschätzt $5-20 je nach Nutzung

## 🚀 NÄCHSTE SCHRITTE

1. API-Key konfigurieren
2. Integration testen
3. Performance messen
4. Produktiv einsetzen
