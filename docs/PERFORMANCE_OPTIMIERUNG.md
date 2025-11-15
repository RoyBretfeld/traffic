# Performance-Optimierung: Allow-Liste & API-Konfiguration

**Datum:** 2025-01-09  
**Status:** ✅ Implementiert

---

## Übersicht

Die **Allow-Liste** dient als **Performance-Boost**: Nur Touren in der Allow-Liste werden verarbeitet, alle anderen werden übersprungen. Das beschleunigt die Verarbeitung erheblich.

**Wichtig:** Das System verwendet **OpenAI API** (Cloud-basiert), **keine lokalen Modelle**. Dadurch:
- ✅ Funktioniert auf jedem Rechner (Laptop, Desktop, Server)
- ✅ Keine GPU erforderlich
- ✅ Nur Internet-Verbindung nötig
- ✅ Skalierbar und schnell

---

## Allow-Liste als Speed-Boost

### Konzept

**Datei:** `config/tour_ignore_list.json`

```json
{
  "allow_tours": ["CB", "T", "BZ"]
}
```

**Effekt:**
- Nur CB, T, BZ Touren werden verarbeitet
- Alle anderen Touren (W, PIR, FG, etc.) werden übersprungen
- **Resultat:** Deutlich weniger Touren = viel schneller!

### Performance-Gewinn

**Beispiel-Szenario:**
- **Vorher:** 20 Touren verarbeiten (alle)
- **Nachher:** 5 Touren verarbeiten (nur CB, T, BZ)
- **Gewinn:** ~75% weniger Verarbeitung = 4x schneller

**Für Single-Tour-Routen (FG, etc.):**
- Diese können in Allow-Liste **nicht** stehen
- Werden automatisch übersprungen
- System konzentriert sich nur auf relevante Touren

---

## API-Konfiguration (Keine lokalen Modelle!)

### Aktuelles System

**Haupt-LLM:** `services/llm_optimizer.py`
- ✅ Verwendet **nur OpenAI API**
- ✅ Model: `gpt-4o-mini` (schnell, kostengünstig)
- ✅ Keine lokalen Modelle
- ✅ Keine GPU erforderlich

**Konfiguration:**
```python
self.client = openai.OpenAI(api_key=self.api_key)
self.model = "gpt-4o-mini"  # Cloud-basiert, keine GPU nötig
```

### Alternative: `backend/services/ai_optimizer.py`

**⚠️ WARNUNG:** Diese Klasse hat `use_local` Parameter!

**Um sicherzustellen dass nur API verwendet wird:**

**Option 1:** Code prüfen wo `AIOptimizer` initialisiert wird:
```python
# ❌ FALSCH (verwendet lokale Modelle):
optimizer = AIOptimizer(use_local=True)

# ✅ RICHTIG (verwendet nur API):
optimizer = AIOptimizer(use_local=False, api_key=os.getenv("OPENAI_API_KEY"))
```

**Option 2:** Nur `LLMOptimizer` verwenden (bereits API-only):
```python
from services.llm_optimizer import LLMOptimizer
optimizer = LLMOptimizer()  # ✅ Automatisch API-only
```

---

## Performance-Tipps

### 1. Allow-Liste gezielt einsetzen

**Für schnelle Verarbeitung:**
```json
{
  "allow_tours": ["CB", "T", "BZ"]  // Nur direkte Routen
}
```

**Für alle Touren:**
```json
{
  "allow_tours": []  // Leer = alle erlauben
}
```

### 2. Ignore-Liste für Pickups/Nachtlieferungen

```json
{
  "ignore_tours": ["DBD", "DPD", "DVD"]  // Überspringen, nicht relevant
}
```

### 3. API-Key sicher konfigurieren

**.env Datei:**
```env
OPENAI_API_KEY=sk-proj-...
LLM_MODEL=gpt-4o-mini  # Schnell & günstig
```

**Verifizierung:**
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️ WARNUNG: OPENAI_API_KEY nicht gesetzt!")
```

### 4. Keine lokalen Modelle laden

**Entfernen/Fertigstellen wenn vorhanden:**
- `ai_models/` Ordner (falls vorhanden)
- `backend/services/ai_optimizer.py` → `use_local=False` setzen
- Ollama-Integration deaktivieren

---

## Geschwindigkeits-Vergleich

### Mit Allow-Liste (CB, T, BZ)
```
✅ 5 Touren verarbeiten
⏱️ ~30 Sekunden
💻 Funktioniert auf jedem Rechner (API-only)
```

### Ohne Allow-Liste (alle Touren)
```
⚠️ 20 Touren verarbeiten
⏱️ ~2 Minuten
💻 Funktioniert auf jedem Rechner (API-only)
```

**Gewinn:** ~4x schneller mit Allow-Liste!

---

## Laptop-Performance

### Warum ist es auf Laptop langsam?

**Mögliche Ursachen:**
1. ⚠️ Lokale Modelle werden verwendet (brauchen GPU)
2. ⚠️ Allow-Liste ist nicht aktiviert (alle Touren werden verarbeitet)
3. ⚠️ Langsame Internet-Verbindung (API-Calls dauern lange)

### Lösung

1. **Verifiziere API-Only:**
   ```python
   # In workflow_api.py prüfen:
   llm_optimizer = LLMOptimizer()
   print(f"LLM enabled: {llm_optimizer.enabled}")  # Sollte True sein
   print(f"API Key vorhanden: {bool(llm_optimizer.api_key)}")  # Sollte True sein
   ```

2. **Aktiviere Allow-Liste:**
   ```json
   {
     "allow_tours": ["CB", "T", "BZ"]  // Nur diese verarbeiten
   }
   ```

3. **Internet-Verbindung prüfen:**
   ```bash
   curl https://api.openai.com/v1/models
   ```

---

## Checkliste für optimale Performance

- [ ] Allow-Liste aktiviert (`allow_tours` nicht leer, nur relevante Touren)
- [ ] Ignore-Liste konfiguriert (DBD, DPD, DVD)
- [ ] OpenAI API-Key gesetzt (`OPENAI_API_KEY` in `.env`)
- [ ] Nur `LLMOptimizer` verwendet (API-only, keine lokalen Modelle)
- [ ] `use_local=False` bei `AIOptimizer` (falls verwendet)
- [ ] Internet-Verbindung stabil
- [ ] Model: `gpt-4o-mini` (schnell & günstig)

---

## Debugging

### Prüfe welche LLM verwendet wird

**Im Server-Log suchen:**
```
[INFO] LLM-Optimizer initialized successfully
[INFO] Model: gpt-4o-mini
```

**Wenn lokale Modelle verwendet werden:**
```
[WARN] Using local model: qwen2.5:0.5b
[WARN] Ollama URL: http://localhost:11434
```
→ **Das sollte NICHT vorkommen!**

### Prüfe Allow-Liste

**Im Server-Log:**
```
[WORKFLOW] Tour-Filter geladen - Ignore: ['DBD', 'DPD', 'DVD'], Allow: ['CB', 'T', 'BZ']
[WORKFLOW] Tour 'CB-08.00 Tour' verarbeitet
[WORKFLOW] Tour 'W-07.00 Uhr Tour' übersprungen (Nicht in Allow-Liste: ['CB', 'T', 'BZ'])
```

---

**Letzte Aktualisierung:** 2025-01-09  
**Status:** ✅ Produktiv, Performance-optimiert

