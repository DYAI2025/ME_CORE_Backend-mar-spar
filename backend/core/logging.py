"""
Centralized logging configuration for MarkerEngine.
Provides structured logging with consistent format across all modules.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.thread,
            "process": record.process
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'marker_id'):
            log_data['marker_id'] = record.marker_id
            
        if hasattr(record, 'phase'):
            log_data['phase'] = record.phase
            
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class MarkerEngineLogger:
    """Centralized logger configuration for MarkerEngine."""
    
    def __init__(self, 
                 name: str = "markerengine",
                 level: str = "INFO",
                 log_dir: Optional[Path] = None):
        """
        Initialize logger configuration.
        
        Args:
            name: Logger name
            level: Logging level
            log_dir: Directory for log files
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
    def get_logger(self, module_name: str) -> logging.Logger:
        """
        Get a configured logger for a specific module.
        
        Args:
            module_name: Name of the module requesting the logger
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(f"{self.name}.{module_name}")
        
        if not logger.handlers:
            logger.setLevel(self.level)
            
            # Console handler with structured output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            logger.addHandler(console_handler)
            
            # File handler with rotation
            file_handler = RotatingFileHandler(
                self.log_dir / f"{self.name}.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(StructuredFormatter())
            logger.addHandler(file_handler)
            
            # Error file handler
            error_handler = RotatingFileHandler(
                self.log_dir / f"{self.name}_errors.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter())
            logger.addHandler(error_handler)
        
        return logger
    
    def log_request(self, 
                    logger: logging.Logger,
                    request_id: str,
                    message: str,
                    **kwargs):
        """Log with request context."""
        extra = {"request_id": request_id}
        extra.update(kwargs)
        logger.info(message, extra=extra)
    
    def log_performance(self,
                       logger: logging.Logger,
                       phase: str,
                       duration_ms: float,
                       request_id: Optional[str] = None,
                       **kwargs):
        """Log performance metrics."""
        extra = {
            "phase": phase,
            "duration_ms": duration_ms
        }
        if request_id:
            extra["request_id"] = request_id
        extra.update(kwargs)
        
        logger.info(f"Performance: {phase} completed in {duration_ms:.2f}ms", extra=extra)


# Global logger instance
_logger_config = MarkerEngineLogger()


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Configured logger
    """
    return _logger_config.get_logger(module_name)


def configure_logging(level: str = "INFO", log_dir: Optional[str] = None):
    """
    Configure global logging settings.
    
    Args:
        level: Logging level
        log_dir: Directory for log files
    """
    global _logger_config
    _logger_config = MarkerEngineLogger(
        level=level,
        log_dir=Path(log_dir) if log_dir else None
    )