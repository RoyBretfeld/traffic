"""
HT-04: Einheitlicher Error-Contract für alle Endpoints.
Standardisiertes Format: code/message/trace_id
"""
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse
import uuid
import logging

logger = logging.getLogger(__name__)


class ErrorCode:
    """Standardisierte Error-Codes für TrafficApp 3.0"""
    
    # Validation Errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Authentication Errors (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    
    # Authorization Errors (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Not Found Errors (404)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    
    # Conflict Errors (409)
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    
    # Rate Limit Errors (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server Errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Import/Processing Errors
    IMPORT_SIZE_LIMIT = "IMPORT_SIZE_LIMIT"
    IMPORT_PARSE_ERROR = "IMPORT_PARSE_ERROR"
    GEOCODING_FAILED = "GEOCODING_FAILED"
    ROUTING_FAILED = "ROUTING_FAILED"


def create_error_response(
    code: str,
    message: str,
    status_code: int = 500,
    trace_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Erstellt standardisierte Error-Response (HT-04).
    
    Args:
        code: Error-Code (aus ErrorCode)
        message: Benutzerfreundliche Fehlermeldung
        status_code: HTTP-Status-Code
        trace_id: Optional, wird generiert falls nicht vorhanden
        details: Zusätzliche Details (z.B. für Validation-Errors)
    
    Returns:
        JSONResponse mit standardisiertem Error-Format
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    error_data = {
        "error": {
            "code": code,
            "message": message,
            "trace_id": trace_id
        }
    }
    
    if details:
        error_data["error"]["details"] = details
    
    # Log error (PII-reduziert)
    logger.error(
        f"Error {code}: {message}",
        extra={
            "error_code": code,
            "trace_id": trace_id,
            "status_code": status_code
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


def create_validation_error(
    message: str,
    fields: Optional[Dict[str, str]] = None,
    trace_id: Optional[str] = None
) -> JSONResponse:
    """
    Erstellt Validation-Error-Response.
    
    Args:
        message: Fehlermeldung
        fields: Dict mit Feldname → Fehlermeldung
        trace_id: Optional
    
    Returns:
        JSONResponse mit Validation-Error
    """
    details = {"fields": fields} if fields else None
    return create_error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        status_code=400,
        trace_id=trace_id,
        details=details
    )


def create_not_found_error(
    resource: str,
    resource_id: Optional[str] = None,
    trace_id: Optional[str] = None
) -> JSONResponse:
    """
    Erstellt Not-Found-Error-Response.
    
    Args:
        resource: Ressourcen-Typ (z.B. "Tour", "Customer")
        resource_id: Optional ID
        trace_id: Optional
    
    Returns:
        JSONResponse mit Not-Found-Error
    """
    message = f"{resource} not found"
    if resource_id:
        message += f" (ID: {resource_id})"
    
    return create_error_response(
        code=ErrorCode.NOT_FOUND,
        message=message,
        status_code=404,
        trace_id=trace_id
    )

