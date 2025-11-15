# FAMO TrafficApp - AI Models

Lokale AI-Modelle für Routenoptimierung

## Empfohlene Modelle:

### Qwen 2.5 (Empfehlung)
- **qwen2.5:0.5b** - Ultraschnell, 300MB
- **qwen2.5:1.5b** - Guter Kompromiss, 900MB
- **qwen2.5:3b** - Beste Qualität, 1.7GB

### Llama 3.2
- **llama3.2:1b** - Schnell, 700MB
- **llama3.2:3b** - Ausgewogen, 2GB

## Installation:
```bash
# Qwen (empfohlen)
ollama pull qwen2.5:0.5b

# Llama Alternative
ollama pull llama3.2:1b
```

## Ollama Konfiguration:
```bash
# Modelle-Pfad setzen (optional)
set OLLAMA_MODELS=C:\Users\Bretfeld\Meine Ablage\_________FAMO\Traffic\ai_models

# Ollama starten
ollama serve
```

## Test:
```bash
curl http://localhost:11434/api/tags
```
