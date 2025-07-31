"""Logging-Konfiguration für die Marker Analysis Engine."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import colorlog


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True,
    colored: bool = True,
    rotation: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Konfiguriert das Logging-System.
    
    Args:
        level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Pfad zur Log-Datei (optional)
        console: Ob auf Konsole geloggt werden soll
        colored: Ob farbige Ausgabe verwendet werden soll
        rotation: Ob Log-Rotation aktiviert werden soll
        max_bytes: Maximale Größe einer Log-Datei
        backup_count: Anzahl der Backup-Dateien
    
    Returns:
        Konfigurierter Root-Logger
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Entferne existierende Handler
    root_logger.handlers.clear()
    
    # Format für Logs
    detailed_format = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
    )
    simple_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Console Handler
    if console:
        if colored and colorlog:
            console_handler = colorlog.StreamHandler(sys.stdout)
            console_format = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(console_format)
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(simple_format))
        
        root_logger.addHandler(console_handler)
    
    # File Handler
    if log_file:
        # Erstelle Log-Verzeichnis falls nötig
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        if rotation:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setFormatter(logging.Formatter(detailed_format))
        root_logger.addHandler(file_handler)
    
    # Spezielle Logger-Konfigurationen
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Gibt einen benannten Logger zurück.
    
    Args:
        name: Name des Loggers (normalerweise __name__)
    
    Returns:
        Logger-Instanz
    """
    return logging.getLogger(name)


class LogContext:
    """Context Manager für temporäre Logging-Level-Änderungen."""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = None
    
    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


def log_function_call(func):
    """Decorator zum Loggen von Funktionsaufrufen."""
    logger = logging.getLogger(func.__module__)
    
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper


# Standard-Setup beim Import
if not logging.getLogger().handlers:
    setup_logging()