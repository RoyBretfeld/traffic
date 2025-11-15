#!/usr/bin/env python3
"""
MIGRATION VON OLLAMA ZU OPENAI API
Ersetzt lokale Ollama-Modelle durch OpenAI API für Proxmox-Umgebung
"""
import os
import json
from pathlib import Path

def create_openai_config():
    """Erstellt OpenAI-Konfiguration"""
    
    config = {
        "use_openai_api": True,
        "openai_model": "gpt-4o-mini",
        "fallback_model": "gpt-3.5-turbo",
        "api_timeout": 30,
        "max_tokens": 1000,
        "temperature": 0.1,
        "optimization_settings": {
            "temperature": 0.1,
            "max_tokens": 1000,
            "response_format": "json_object"
        }
    }
    
    # Speichere neue Konfiguration
    config_path = Path('ai_models/config_openai.json')
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f'✅ OpenAI-Konfiguration erstellt: {config_path}')
    return config_path

def update_ai_config():
    """Aktualisiert die bestehende AI-Konfiguration"""
    
    config_path = Path('ai_models/config.json')
    
    if not config_path.exists():
        print('❌ Bestehende Konfiguration nicht gefunden')
        return False
    
    # Lade bestehende Konfiguration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Aktualisiere für OpenAI
    config.update({
        "use_local_models": False,
        "use_openai_api": True,
        "openai_model": "gpt-4o-mini",
        "fallback_model": "gpt-3.5-turbo",
        "api_timeout": 30,
        "max_tokens": 1000,
        "temperature": 0.1,
        "optimization_settings": {
            "temperature": 0.1,
            "max_tokens": 1000,
            "response_format": "json_object"
        }
    })
    
    # Speichere aktualisierte Konfiguration
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f'✅ AI-Konfiguration aktualisiert: {config_path}')
    return True

def create_env_example():
    """Erstellt .env.example für OpenAI API-Key"""
    
    env_content = """# FAMO TrafficApp - Umgebungsvariablen

# OpenAI API (für LLM-Integration)
OPENAI_API_KEY=your_openai_api_key_here

# Mapbox API (für Routing - optional)
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here

# Datenbank
DATABASE_URL=sqlite:///data/traffic.db

# Server
HOST=0.0.0.0
PORT=8000
"""
    
    env_path = Path('.env.example')
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f'✅ .env.example erstellt: {env_path}')

def create_migration_guide():
    """Erstellt Migrations-Anleitung"""
    
    guide = """# MIGRATION VON OLLAMA ZU OPENAI API

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
"""
    
    guide_path = Path('MIGRATION_TO_OPENAI.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f'✅ Migrations-Anleitung erstellt: {guide_path}')

def main():
    """Hauptfunktion für Migration"""
    
    print('🚀 MIGRATION VON OLLAMA ZU OPENAI API')
    print('=' * 50)
    
    # 1. Erstelle OpenAI-Konfiguration
    create_openai_config()
    
    # 2. Aktualisiere bestehende Konfiguration
    update_ai_config()
    
    # 3. Erstelle .env.example
    create_env_example()
    
    # 4. Erstelle Migrations-Anleitung
    create_migration_guide()
    
    print()
    print('✅ MIGRATION VORBEREITET!')
    print()
    print('📋 NÄCHSTE SCHRITTE:')
    print('1. OpenAI API-Key besorgen: https://platform.openai.com/api-keys')
    print('2. Umgebungsvariable setzen: OPENAI_API_KEY=your_key')
    print('3. Integration testen: python openai_integration.py')
    print('4. Produktiv einsetzen')

if __name__ == '__main__':
    main()
