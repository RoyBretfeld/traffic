# KI-CodeChecker: Kosten- und Performance-Monitoring
**Datum:** 2025-01-10  
**Status:** 📋 KONZEPT

---

## 🎯 Ziel

Überwachung und Optimierung von:
- **Kosten:** KI-API-Aufrufe, E-Mail-Versand, Ressourcenverbrauch
- **Performance:** Code-Analyse-Zeit, WebSocket-Latenz, Log-Dateigröße

---

## 💰 Kosten-Monitoring

### 1. KI-API-Kosten

#### Tracking
- **Anzahl API-Aufrufe** pro Tag/Woche/Monat
- **Token-Verbrauch** (Input/Output)
- **Kosten pro Aufruf** (basierend auf Modell-Preisen)
- **Kosten pro Datei** (welche Dateien sind am teuersten?)

#### Implementierung
```python
class CostTracker:
    def track_api_call(self, model: str, input_tokens: int, output_tokens: int, cost: float):
        # Speichere in DB oder Log
        pass
    
    def get_daily_costs(self) -> float:
        # Summiere alle Kosten des Tages
        pass
    
    def get_cost_per_file(self, file_path: str) -> float:
        # Kosten für bestimmte Datei
        pass
```

#### Rate-Limiting
- **Max. API-Aufrufe pro Tag:** 50 (konfigurierbar)
- **Max. Kosten pro Tag:** 5€ (konfigurierbar)
- **Max. Verbesserungen pro Tag:** 10 (konfigurierbar)
- **Pause bei Limit erreicht:** Automatisch stoppen

### 2. E-Mail-Kosten

#### Tracking
- Anzahl E-Mails pro Tag
- Kosten pro E-Mail (falls bezahlt)
- E-Mail-Provider-Limits

#### Optimierung
- **Batch-E-Mails:** Tages-Zusammenfassung statt einzelne E-Mails
- **Nur wichtige E-Mails:** Rollback immer, Erfolg optional
- **E-Mail-Deaktivierung:** Optional komplett ausschalten

### 3. Ressourcen-Kosten

#### Tracking
- CPU-Zeit für Code-Analyse
- Speicher-Verbrauch
- Log-Dateigröße
- Datenbank-Größe

---

## ⚡ Performance-Monitoring

### 1. Code-Analyse-Performance

#### Metriken
- **Analyse-Zeit** pro Datei (Ziel: < 5 Sekunden)
- **Token-Generierung-Zeit** (Ziel: < 10 Sekunden)
- **Test-Ausführungs-Zeit** (Ziel: < 30 Sekunden)
- **Gesamt-Zeit** pro Verbesserung (Ziel: < 60 Sekunden)

#### Tracking
```python
class PerformanceTracker:
    def track_analysis(self, file_path: str, duration: float):
        # Speichere Analyse-Zeit
        pass
    
    def track_api_call(self, duration: float):
        # Speichere API-Aufruf-Zeit
        pass
    
    def get_average_analysis_time(self) -> float:
        # Durchschnittliche Analyse-Zeit
        pass
```

### 2. WebSocket-Performance

#### Metriken
- **Latenz** (Zeit bis Update beim Client)
- **Verbindungs-Qualität** (Anzahl Reconnects)
- **Nachrichten pro Sekunde**

#### Optimierung
- **Batching:** Mehrere Updates zusammen senden
- **Throttling:** Max. 1 Update pro Sekunde
- **Heartbeat:** Reduzieren auf alle 10 Sekunden

### 3. Log-Datei-Performance

#### Metriken
- **Log-Dateigröße** pro Tag
- **Lese-Zeit** für Historie
- **Schreib-Zeit** für neue Einträge

#### Optimierung
- **Rotation:** Alte Logs komprimieren/archivieren
- **Retention:** Nur 30 Tage behalten
- **Batch-Schreiben:** Mehrere Einträge zusammen schreiben

---

## 📊 Dashboard-Erweiterung

### Kosten-Tab

```
┌─────────────────────────────────────────────────────────┐
│  Kosten-Übersicht (Heute)                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  💰 Gesamt-Kosten: 2.45€ / 5.00€ (Limit)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ API-Aufrufe │  │ Token       │  │ E-Mails    │     │
│  │   12 / 50   │  │ 45k / 200k  │  │   3 / 100   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                          │
│  📈 Kosten-Trend (7 Tage)                                │
│  [Chart: Kosten pro Tag]                                 │
│                                                          │
│  📁 Teuerste Dateien                                     │
│  1. routes/workflow_api.py - 0.85€                      │
│  2. frontend/index.html - 0.42€                         │
│  3. backend/app.py - 0.38€                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Performance-Tab

```
┌─────────────────────────────────────────────────────────┐
│  Performance-Übersicht                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ⚡ Durchschnittliche Zeiten                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Analyse      │  │ API-Call    │  │ Tests       │   │
│  │   3.2s       │  │   8.5s      │  │  25.3s      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                          │
│  📈 Performance-Trend (7 Tage)                          │
│  [Chart: Durchschnittliche Zeiten]                       │
│                                                          │
│  🐌 Langsamste Dateien                                  │
│  1. routes/workflow_api.py - 12.5s                      │
│  2. frontend/index.html - 8.3s                          │
│  3. backend/app.py - 6.1s                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementierung

### 1. CostTracker Service

```python
# backend/services/cost_tracker.py
class CostTracker:
    def __init__(self):
        self.db_path = "data/code_fixes_cost.db"
        self._init_db()
    
    def track_api_call(self, model: str, input_tokens: int, output_tokens: int):
        # Berechne Kosten basierend auf Modell-Preisen
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Speichere in DB
        self._save_cost_entry({
            "timestamp": datetime.now(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })
        
        return cost
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        # OpenAI Preise (Stand: 2025)
        prices = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-4-turbo": {"input": 0.01 / 1000, "output": 0.03 / 1000},
            "gpt-3.5-turbo": {"input": 0.0015 / 1000, "output": 0.002 / 1000}
        }
        
        model_price = prices.get(model, prices["gpt-3.5-turbo"])
        return (input_tokens * model_price["input"]) + (output_tokens * model_price["output"])
    
    def get_daily_costs(self) -> float:
        # Summiere alle Kosten des Tages
        pass
    
    def check_daily_limit(self, limit: float = 5.0) -> bool:
        # Prüfe ob Tages-Limit erreicht
        return self.get_daily_costs() < limit
```

### 2. PerformanceTracker Service

```python
# backend/services/performance_tracker.py
import time
from contextlib import contextmanager

class PerformanceTracker:
    def __init__(self):
        self.db_path = "data/code_fixes_performance.db"
        self._init_db()
    
    @contextmanager
    def track_operation(self, operation_name: str, file_path: str = None):
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._save_performance_entry({
                "timestamp": datetime.now(),
                "operation": operation_name,
                "file_path": file_path,
                "duration": duration
            })
    
    def get_average_time(self, operation_name: str) -> float:
        # Berechne Durchschnitts-Zeit für Operation
        pass
```

### 3. Rate-Limiter

```python
# backend/services/rate_limiter.py
class RateLimiter:
    def __init__(self):
        self.daily_improvements = 0
        self.daily_api_calls = 0
        self.daily_costs = 0.0
        
        # Limits (konfigurierbar)
        self.max_improvements_per_day = 10
        self.max_api_calls_per_day = 50
        self.max_costs_per_day = 5.0
    
    def can_improve_code(self) -> tuple[bool, str]:
        """Prüft ob Code-Verbesserung erlaubt ist."""
        if self.daily_improvements >= self.max_improvements_per_day:
            return False, f"Tages-Limit erreicht: {self.max_improvements_per_day} Verbesserungen"
        
        if self.daily_api_calls >= self.max_api_calls_per_day:
            return False, f"API-Limit erreicht: {self.max_api_calls_per_day} Aufrufe"
        
        if self.daily_costs >= self.max_costs_per_day:
            return False, f"Kosten-Limit erreicht: {self.max_costs_per_day}€"
        
        return True, "OK"
    
    def record_improvement(self, api_calls: int, cost: float):
        """Zeichnet Verbesserung auf."""
        self.daily_improvements += 1
        self.daily_api_calls += api_calls
        self.daily_costs += cost
```

---

## 📋 Konfiguration

### config/app.yaml

```yaml
ki_codechecker:
  costs:
    daily_limit_eur: 5.0
    daily_api_calls_limit: 50
    daily_improvements_limit: 10
    track_costs: true
    
  performance:
    track_performance: true
    log_slow_operations: true
    slow_operation_threshold_seconds: 10
    
  notifications:
    email:
      batch_mode: true  # Tages-Zusammenfassung statt einzelne E-Mails
      only_important: true  # Nur Rollback, nicht Erfolg
      
  websocket:
    throttle_seconds: 1  # Max. 1 Update pro Sekunde
    heartbeat_interval: 10  # Heartbeat alle 10 Sekunden
    
  logs:
    retention_days: 30
    compress_old_logs: true
```

---

## 🎯 Optimierungen

### 1. Kosten-Optimierung
- ✅ **Batch-E-Mails:** Tages-Zusammenfassung
- ✅ **Rate-Limiting:** Max. X Verbesserungen/Tag
- ✅ **Kosten-Limit:** Automatisch stoppen bei Limit
- ✅ **Günstigere Modelle:** gpt-3.5-turbo für einfache Fixes
- ✅ **Caching:** Ähnliche Probleme nicht erneut analysieren

### 2. Performance-Optimierung
- ✅ **Parallele Analyse:** Mehrere Dateien gleichzeitig
- ✅ **Inkrementelle Analyse:** Nur geänderte Dateien
- ✅ **Caching:** Analyse-Ergebnisse cachen
- ✅ **Throttling:** WebSocket-Updates batching
- ✅ **Log-Rotation:** Alte Logs komprimieren

---

## 📊 Metriken-Export

### API-Endpoints

```python
@router.get("/api/ki-improvements/costs")
async def get_costs(period: str = "today"):
    """Gibt Kosten-Übersicht zurück."""
    pass

@router.get("/api/ki-improvements/performance")
async def get_performance(period: str = "today"):
    """Gibt Performance-Übersicht zurück."""
    pass

@router.get("/api/ki-improvements/limits")
async def get_limits():
    """Gibt aktuelle Limits und Status zurück."""
    pass
```

---

**Status:** 📋 KONZEPT  
**Nächster Schritt:** Implementierung von CostTracker und PerformanceTracker

