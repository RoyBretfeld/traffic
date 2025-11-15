#!/usr/bin/env python3
"""
LLM UND ROUTEN-ERKENNUNG: STATUS UND NÄCHSTE SCHRITTE
"""
import sys
sys.path.insert(0, '.')

def check_llm_status():
    """Prüfe den aktuellen Status der LLM-Integration."""
    print('🤖 AKTUELLE LLM-KONFIGURATION:')
    print('=' * 50)
    
    try:
        from backend.services.ai_config import ai_config
        
        info = ai_config.get_model_info()
        print(f'Bevorzugtes Modell: {info["preferred"]}')
        print(f'Fallback-Modelle: {info["fallbacks"]}')
        print(f'Modelle-Verzeichnis: {info["models_dir"]}')
        print(f'Ollama läuft: {info["ollama_running"]}')
        print()
        
        print('⚙️ OPTIMIERUNGS-EINSTELLUNGEN:')
        settings = ai_config.optimization_settings
        for key, value in settings.items():
            print(f'   {key}: {value}')
            
    except Exception as e:
        print(f'❌ Fehler beim Laden der AI-Konfiguration: {e}')

def check_routing_status():
    """Prüfe den Status der Routing-Services."""
    print('\n🗺️ ROUTING-SERVICES STATUS:')
    print('=' * 50)
    
    try:
        from backend.services.real_routing import RealRoutingService
        from backend.services.optimization_rules import OptimizationRules
        
        routing_service = RealRoutingService()
        print(f'Mapbox Token gesetzt: {bool(routing_service.mapbox_token)}')
        
        rules = OptimizationRules()
        print(f'Max. Fahrzeit: {rules.max_driving_time_to_last_customer} Min')
        print(f'Servicezeit pro Kunde: {rules.service_time_per_customer_minutes} Min')
        print(f'Max. Stops pro Tour: {rules.max_stops_per_tour}')
        print(f'Depot: {rules.start_location}')
        
    except Exception as e:
        print(f'❌ Fehler beim Laden der Routing-Services: {e}')

def check_ai_optimizer():
    """Prüfe den AI-Optimizer."""
    print('\n🧠 AI-OPTIMIZER STATUS:')
    print('=' * 50)
    
    try:
        from backend.services.ai_optimizer import AIOptimizer
        
        optimizer = AIOptimizer(use_local=True)
        print(f'Lokale Modelle aktiviert: {optimizer.use_local}')
        print(f'Ollama URL: {optimizer.ollama_url}')
        
    except Exception as e:
        print(f'❌ Fehler beim Laden des AI-Optimizers: {e}')

def suggest_next_steps():
    """Schlage nächste Schritte vor."""
    print('\n🚀 NÄCHSTE SCHRITTE:')
    print('=' * 50)
    
    print('1. 🤖 LLM-SETUP PRÜFEN:')
    print('   - Ollama installiert und läuft?')
    print('   - Modelle heruntergeladen?')
    print('   - API-Endpunkte erreichbar?')
    print()
    
    print('2. 🗺️ ROUTING-SETUP PRÜFEN:')
    print('   - Mapbox API-Token konfiguriert?')
    print('   - OpenRouteService als Fallback?')
    print('   - Haversine-Distanz als letzter Fallback?')
    print()
    
    print('3. 🧪 INTEGRATIONSTESTS:')
    print('   - CSV → Geocoding → Clustering → TSP')
    print('   - AI-Optimierung mit echten Daten')
    print('   - Performance-Tests')
    print()
    
    print('4. 📊 MONITORING:')
    print('   - LLM-Response-Zeiten')
    print('   - Routing-API-Quotas')
    print('   - Optimierungsqualität')

if __name__ == '__main__':
    check_llm_status()
    check_routing_status()
    check_ai_optimizer()
    suggest_next_steps()
