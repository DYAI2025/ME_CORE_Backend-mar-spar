"""
Centralized exception handling for MarkerEngine.
Provides structured error types and handling strategies.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class MarkerEngineError(Exception):
    """Base exception for all MarkerEngine errors."""
    
    def __init__(self, 
                 message: str,
                 error_code: str,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize MarkerEngine error.
        
        Args:
            message: Error message
            error_code: Unique error code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(MarkerEngineError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class DatabaseError(MarkerEngineError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {"operation": operation} if operation else {}
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )


class MarkerNotFoundError(MarkerEngineError):
    """Raised when a marker is not found."""
    
    def __init__(self, marker_id: str):
        super().__init__(
            message=f"Marker not found: {marker_id}",
            error_code="MARKER_NOT_FOUND",
            details={"marker_id": marker_id}
        )


class NLPProcessingError(MarkerEngineError):
    """Raised when NLP processing fails."""
    
    def __init__(self, message: str, phase: Optional[str] = None):
        details = {"phase": phase} if phase else {}
        super().__init__(
            message=message,
            error_code="NLP_PROCESSING_ERROR",
            details=details
        )


class ConfigurationError(MarkerEngineError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class ExternalServiceError(MarkerEngineError):
    """Raised when external service calls fail."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )


def handle_markerengine_error(error: MarkerEngineError) -> HTTPException:
    """
    Convert MarkerEngine error to HTTP exception.
    
    Args:
        error: MarkerEngine error instance
        
    Returns:
        HTTPException with appropriate status code
    """
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "MARKER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DATABASE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "NLP_PROCESSING_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY
    }
    
    status_code = status_map.get(error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        detail=error.to_dict()
    )


class ErrorHandler:
    """Centralized error handling utilities."""
    
    @staticmethod
    def safe_execute(func, *args, **kwargs):
        """
        Execute function with error handling.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises MarkerEngineError
        """
        try:
            return func(*args, **kwargs)
        except MarkerEngineError:
            raise
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise MarkerEngineError(
                message=f"Unexpected error: {str(e)}",
                error_code="INTERNAL_ERROR",
                details={"original_error": type(e).__name__}
            )