# Technische Implementierungsanleitung - LLM-Integration

## Schnellstart

### 1. OpenAI API-Integration

```python
# services/llm_optimizer.py
import openai
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class OptimizationResult:
    optimized_route: List[int]
    confidence_score: float
    reasoning: str
    tokens_used: int

class LLMOptimizer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def optimize_route(self, stops: List[Dict], region: str = "Dresden") -> OptimizationResult:
        prompt = f"""
        Optimiere die Route für {len(stops)} Stopps in {region}.
        Stopps: {[f"{s['name']} - {s['address']}" for s in stops]}
        
        Berücksichtige:
        - Minimale Fahrzeit
        - Logische Reihenfolge
        - Prioritäten der Kunden
        
        Gib die optimale Reihenfolge als Indizes zurück.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return OptimizationResult(
            optimized_route=self._parse_response(response.choices[0].message.content),
            confidence_score=0.8,  # Placeholder
            reasoning=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens
        )
```

### 2. Monitoring-Integration

```python
# services/monitoring.py
import time
import logging
from typing import Dict, Any

class LLMMonitor:
    def __init__(self):
        self.metrics = {}
        self.logger = logging.getLogger(__name__)
    
    def track_llm_call(self, operation: str, start_time: float, 
                      tokens_used: int, success: bool):
        duration = time.time() - start_time
        
        self.metrics[operation] = {
            "duration": duration,
            "tokens_used": tokens_used,
            "success": success,
            "timestamp": time.time()
        }
        
        self.logger.info(f"LLM {operation}: {duration:.2f}s, {tokens_used} tokens")
    
    def get_performance_report(self) -> Dict[str, Any]:
        return {
            "total_calls": len(self.metrics),
            "avg_duration": sum(m["duration"] for m in self.metrics.values()) / len(self.metrics),
            "total_tokens": sum(m["tokens_used"] for m in self.metrics.values()),
            "success_rate": sum(1 for m in self.metrics.values() if m["success"]) / len(self.metrics)
        }
```

### 3. Workflow-Integration

```python
# Erweiterung von routes/workflow_api.py
from services.llm_optimizer import LLMOptimizer
from services.monitoring import LLMMonitor

class EnhancedWorkflowAPI:
    def __init__(self):
        self.llm_optimizer = LLMOptimizer(os.getenv("OPENAI_API_KEY"))
        self.monitor = LLMMonitor()
    
    async def complete_workflow_with_llm(self, filename: str):
        start_time = time.time()
        
        # Bestehender Workflow
        result = await self.complete_workflow(filename)
        
        # LLM-Optimierung für jede Tour
        for tour in result["tours"]:
            if len(tour["stops"]) > 1:
                llm_result = self.llm_optimizer.optimize_route(
                    tour["stops"], 
                    region="Dresden"
                )
                
                # Wende LLM-Optimierung an
                tour["stops"] = self._apply_llm_optimization(
                    tour["stops"], 
                    llm_result.optimized_route
                )
                
                tour["llm_optimized"] = True
                tour["confidence_score"] = llm_result.confidence_score
        
        # Monitoring
        self.monitor.track_llm_call(
            "workflow_optimization",
            start_time,
            sum(tour.get("tokens_used", 0) for tour in result["tours"]),
            True
        )
        
        return result
```

## Konfiguration

### Environment Variables

```bash
# .env
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.3
MONITORING_ENABLED=true
```

### Prompt-Templates

```json
{
  "routing_optimization": {
    "system": "Du bist ein Experte für Routenoptimierung...",
    "user": "Optimiere die Route für {tour_count} Stopps...",
    "parameters": {
      "max_tokens": 500,
      "temperature": 0.3
    }
  }
}
```

## Testing

### Unit Tests

```python
# tests/test_llm_optimizer.py
import pytest
from services.llm_optimizer import LLMOptimizer

def test_route_optimization():
    optimizer = LLMOptimizer("test_key")
    stops = [
        {"name": "Kunde 1", "address": "Straße 1, Dresden"},
        {"name": "Kunde 2", "address": "Straße 2, Dresden"}
    ]
    
    result = optimizer.optimize_route(stops)
    
    assert len(result.optimized_route) == 2
    assert result.confidence_score > 0
    assert result.tokens_used > 0
```

### Integration Tests

```python
# tests/test_workflow_integration.py
import pytest
from routes.workflow_api import EnhancedWorkflowAPI

@pytest.mark.asyncio
async def test_workflow_with_llm():
    api = EnhancedWorkflowAPI()
    result = await api.complete_workflow_with_llm("test_tourplan.csv")
    
    assert result["success"] == True
    assert any(tour.get("llm_optimized") for tour in result["tours"])
```

## Deployment

### Docker-Integration

```dockerfile
# Dockerfile.llm
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

CMD ["python", "backend/app.py"]
```

### CI/CD-Pipeline

```yaml
# .github/workflows/llm-integration.yml
name: LLM Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/test_llm_*.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Monitoring & Alerting

### Metriken-Dashboard

```python
# routes/monitoring_api.py
@router.get("/api/monitoring/llm-metrics")
async def get_llm_metrics():
    monitor = LLMMonitor()
    return {
        "performance": monitor.get_performance_report(),
        "alerts": monitor.check_alerts(),
        "recommendations": monitor.get_recommendations()
    }
```

### Alerting

```python
# services/alerting.py
class LLMAlerting:
    def check_alerts(self, metrics: Dict[str, Any]):
        alerts = []
        
        if metrics["avg_duration"] > 5.0:
            alerts.append("High LLM response time")
        
        if metrics["success_rate"] < 0.95:
            alerts.append("Low LLM success rate")
        
        return alerts
```

## Best Practices

1. **Prompt-Engineering**: Verwende konsistente Templates und teste verschiedene Formulierungen
2. **Error-Handling**: Implementiere Fallback-Mechanismen für API-Ausfälle
3. **Rate-Limiting**: Respektiere API-Limits und implementiere Retry-Logik
4. **Caching**: Cache häufige Anfragen zur Kostenreduktion
5. **Monitoring**: Überwache Token-Usage und Performance kontinuierlich

## Troubleshooting

### Häufige Probleme

1. **API-Key-Fehler**: Prüfe Environment-Variable `OPENAI_API_KEY`
2. **Rate-Limiting**: Implementiere Exponential-Backoff
3. **Token-Limit**: Reduziere Prompt-Länge oder verwende Streaming
4. **Latenz-Probleme**: Implementiere Timeout und Fallback-Routen

### Debugging

```python
# Debug-Modus aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# LLM-Calls loggen
logger = logging.getLogger("llm_optimizer")
logger.debug(f"LLM Request: {prompt}")
logger.debug(f"LLM Response: {response}")
```
