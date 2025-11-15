# KI-CodeChecker: Modell-Konfiguration
**Datum:** 2025-01-10  
**Status:** ✅ KONFIGURIERT

---

## 🤖 Standard-Modell: GPT-4o-mini

Wir verwenden **GPT-4o-mini** als Standard-Modell für alle Code-Verbesserungen.

### Warum GPT-4o-mini?

1. **Kostenoptimiert:**
   - Input: 0.00015€ pro 1000 Tokens
   - Output: 0.0006€ pro 1000 Tokens
   - **~10x günstiger als GPT-4**

2. **Schnell:**
   - Schnellere Antwortzeiten
   - Geringere Latenz

3. **Ausreichend für Code-Verbesserungen:**
   - Gute Code-Analyse-Fähigkeiten
   - Versteht Kontext gut
   - Geeignet für die meisten Code-Verbesserungen

---

## 💰 Kosten-Vergleich

### Beispiel: Code-Verbesserung (1000 Input + 500 Output Tokens)

| Modell | Input-Kosten | Output-Kosten | **Gesamt** |
|--------|--------------|--------------|------------|
| **gpt-4o-mini** | 0.00015€ | 0.0003€ | **0.00045€** |
| gpt-3.5-turbo | 0.0015€ | 0.001€ | 0.0025€ |
| gpt-4o | 0.005€ | 0.0075€ | 0.0125€ |
| gpt-4-turbo | 0.01€ | 0.015€ | 0.025€ |
| gpt-4 | 0.03€ | 0.03€ | 0.06€ |

**Ersparnis:** Mit GPT-4o-mini sparen wir **~99%** im Vergleich zu GPT-4!

---

## 📊 Tages-Limits (mit GPT-4o-mini)

Mit GPT-4o-mini können wir **viel mehr** Verbesserungen pro Tag machen:

### Aktuelle Limits:
- **Kosten-Limit:** 5€ pro Tag
- **API-Aufrufe:** 50 pro Tag
- **Verbesserungen:** 10 pro Tag

### Potenzial mit GPT-4o-mini:
- **~11.000 Verbesserungen** pro Tag möglich (bei 5€ Limit)
- **~333.000 API-Aufrufe** pro Tag möglich (bei 5€ Limit)

**Empfehlung:** Limits können erhöht werden, da GPT-4o-mini so günstig ist!

---

## 🔧 Konfiguration

### Standard-Modell setzen

```python
# backend/services/cost_tracker.py
self.default_model = "gpt-4o-mini"
```

### Modell in Code-Verbesserungen verwenden

```python
from backend.services.cost_tracker import get_cost_tracker

tracker = get_cost_tracker()
model = tracker.default_model  # "gpt-4o-mini"

# API-Aufruf mit GPT-4o-mini
response = openai_client.chat.completions.create(
    model=model,  # gpt-4o-mini
    messages=[...],
    ...
)
```

---

## 📈 Kosten-Tracking

Alle API-Aufrufe werden automatisch getrackt:

```python
# Automatisches Tracking
cost = tracker.track_api_call(
    model="gpt-4o-mini",
    input_tokens=1000,
    output_tokens=500
)
# cost = 0.00045€
```

---

## 🎯 Empfehlungen

### Für einfache Code-Verbesserungen:
- ✅ **GPT-4o-mini** (Standard)

### Für komplexe Code-Verbesserungen:
- ⚠️ Optional: GPT-4o (falls GPT-4o-mini nicht ausreicht)
- ⚠️ Nur bei Bedarf, da teurer

### Für kritische Code-Verbesserungen:
- ⚠️ Optional: GPT-4 (höchste Qualität)
- ⚠️ Nur bei Bedarf, da sehr teuer

---

## 🔄 Modell-Wechsel

Falls ein anderes Modell benötigt wird, kann es in der Konfiguration geändert werden:

```yaml
# config/app.yaml
ki_codechecker:
  model:
    default: "gpt-4o-mini"
    fallback: "gpt-4o"  # Falls GPT-4o-mini nicht ausreicht
```

---

**Status:** ✅ GPT-4o-mini als Standard konfiguriert  
**Kosten:** ~99% Ersparnis im Vergleich zu GPT-4

