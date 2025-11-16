"""
Erweiterte Logging-Utilities für FAMO TrafficApp
Implementiert positives/negatives Logging mit erweitertem Debugging
"""
import logging
import time
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
from pathlib import Path


class EnhancedLogger:
    """
    Erweiterter Logger mit positivem/negativem Logging
    - ✅ POSITIV: Erfolgreiche Operationen
    - ❌ NEGATIV: Fehler und Probleme
    - 🔍 DEBUG: Detaillierte Debug-Informationen
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
        self._operation_stack = []  # Für verschachtelte Operationen
    
    def _format_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Formatiert Log-Nachricht mit Kontext"""
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {context_str}"
        return message
    
    def success(self, message: str, context: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None):
        """
        ✅ POSITIVES LOGGING: Erfolgreiche Operation
        """
        msg = self._format_message(f"✅ {message}", context)
        if duration_ms is not None:
            msg += f" | Dauer: {duration_ms:.2f}ms"
        self.logger.info(msg)
    
    def error(self, message: str, error: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None, 
              trace: bool = True):
        """
        ❌ NEGATIVES LOGGING: Fehler aufgetreten
        """
        msg = self._format_message(f"❌ {message}", context)
        if error:
            msg += f" | Fehler: {type(error).__name__}: {str(error)}"
        self.logger.error(msg)
        
        if trace and error:
            self.logger.debug(f"❌ Traceback:\n{traceback.format_exc()}")
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        ⚠️ WARNUNG: Potenzielle Probleme
        """
        msg = self._format_message(f"⚠️ {message}", context)
        self.logger.warning(msg)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        🔍 DEBUG: Detaillierte Debug-Informationen
        """
        msg = self._format_message(f"🔍 {message}", context)
        self.logger.debug(msg)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        ℹ️ INFO: Allgemeine Information
        """
        msg = self._format_message(f"ℹ️ {message}", context)
        self.logger.info(msg)
    
    def operation_start(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """
        Startet eine Operation (für verschachteltes Logging)
        """
        self._operation_stack.append({
            'name': operation_name,
            'start_time': time.time(),
            'context': context or {}
        })
        self.debug(f"Starte Operation: {operation_name}", context)
    
    def operation_end(self, operation_name: str, success: bool = True, 
                     context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None):
        """
        Beendet eine Operation mit Erfolg/Fehler
        """
        if not self._operation_stack:
            return
        
        op = self._operation_stack.pop()
        duration_ms = (time.time() - op['start_time']) * 1000
        
        if success:
            self.success(f"Operation abgeschlossen: {operation_name}", 
                        context={**(op.get('context', {})), **(context or {})},
                        duration_ms=duration_ms)
        else:
            self.error(f"Operation fehlgeschlagen: {operation_name}", 
                      error=error,
                      context={**(op.get('context', {})), **(context or {})})
    
    def log_api_call(self, method: str, endpoint: str, status_code: int, 
                    duration_ms: float, request_id: Optional[str] = None):
        """
        Loggt API-Aufrufe mit positivem/negativem Logging
        """
        context = {
            'method': method,
            'endpoint': endpoint,
            'status': status_code,
            'duration_ms': f"{duration_ms:.2f}"
        }
        if request_id:
            context['request_id'] = request_id
        
        if 200 <= status_code < 300:
            self.success(f"API {method} {endpoint}", context, duration_ms)
        elif 400 <= status_code < 500:
            self.warning(f"API {method} {endpoint} - Client-Fehler", context)
        else:
            self.error(f"API {method} {endpoint} - Server-Fehler", context=context)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, 
                           error: Optional[Exception] = None, size_bytes: Optional[int] = None):
        """
        Loggt Datei-Operationen
        """
        context = {'file': str(file_path)}
        if size_bytes:
            context['size_bytes'] = size_bytes
        
        if success:
            self.success(f"Datei-Operation: {operation}", context)
        else:
            self.error(f"Datei-Operation fehlgeschlagen: {operation}", error=error, context=context)
    
    def log_database_operation(self, operation: str, table: str, success: bool,
                               rows_affected: Optional[int] = None, error: Optional[Exception] = None):
        """
        Loggt Datenbank-Operationen
        """
        context = {'table': table}
        if rows_affected is not None:
            context['rows'] = rows_affected
        
        if success:
            self.success(f"DB-Operation: {operation}", context)
        else:
            self.error(f"DB-Operation fehlgeschlagen: {operation}", error=error, context=context)


def get_enhanced_logger(name: str) -> EnhancedLogger:
    """Factory-Funktion für EnhancedLogger"""
    return EnhancedLogger(name)


def log_function_call(logger: Optional[EnhancedLogger] = None, log_args: bool = False, 
                     log_result: bool = False):
    """
    Decorator für automatisches Logging von Funktionsaufrufen
    """
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_logger = logger or get_enhanced_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            context = {}
            
            if log_args:
                context['args_count'] = len(args)
                context['kwargs_keys'] = list(kwargs.keys())
            
            func_logger.operation_start(func_name, context)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if log_result:
                    context['result_type'] = type(result).__name__
                    if hasattr(result, '__len__'):
                        context['result_length'] = len(result)
                
                func_logger.operation_end(func_name, success=True, 
                                         context={**context, 'duration_ms': f"{duration_ms:.2f}"})
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                func_logger.operation_end(func_name, success=False, 
                                         context={**context, 'duration_ms': f"{duration_ms:.2f}"},
                                         error=e)
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_logger = logger or get_enhanced_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            context = {}
            
            if log_args:
                context['args_count'] = len(args)
                context['kwargs_keys'] = list(kwargs.keys())
            
            func_logger.operation_start(func_name, context)
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if log_result:
                    context['result_type'] = type(result).__name__
                    if hasattr(result, '__len__'):
                        context['result_length'] = len(result)
                
                func_logger.operation_end(func_name, success=True, 
                                         context={**context, 'duration_ms': f"{duration_ms:.2f}"})
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                func_logger.operation_end(func_name, success=False, 
                                         context={**context, 'duration_ms': f"{duration_ms:.2f}"},
                                         error=e)
                raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_api_endpoint(logger: Optional[EnhancedLogger] = None):
    """
    Decorator für FastAPI-Endpoints mit automatischem Logging
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_logger = logger or get_enhanced_logger(func.__module__)
            endpoint = f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            request_id = None
            
            # Versuche request_id aus kwargs zu extrahieren
            if 'request' in kwargs:
                request = kwargs['request']
                if hasattr(request, 'state') and hasattr(request.state, 'request_id'):
                    request_id = request.state.request_id
            
            func_logger.operation_start(f"API {endpoint}", {'request_id': request_id} if request_id else {})
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Status-Code extrahieren (falls Response-Objekt)
                status_code = 200
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                
                func_logger.log_api_call('POST' if 'post' in func.__name__.lower() else 'GET',
                                        endpoint, status_code, duration_ms, request_id)
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                func_logger.operation_end(f"API {endpoint}", success=False, 
                                         context={'duration_ms': f"{duration_ms:.2f}"},
                                         error=e)
                raise
        
        return wrapper
    return decorator

