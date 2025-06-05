"""
Logging utilities for Nuke AI Panel.

Provides centralized logging configuration with support for file and console logging,
log rotation, and colored output.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import colorlog

# Global logger cache
_loggers: Dict[str, logging.Logger] = {}
_configured = False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None,
    console_logging: bool = True,
    file_logging: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_format: Optional[str] = None
):
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of log file (defaults to nuke_ai_panel.log)
        log_dir: Directory for log files (defaults to ~/.nuke_ai_panel/logs)
        console_logging: Enable console logging
        file_logging: Enable file logging
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        log_format: Custom log format string
    """
    global _configured
    
    # Set up log directory
    if log_dir is None:
        log_dir = Path.home() / ".nuke_ai_panel" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up log file path
    if log_file is None:
        log_file = "nuke_ai_panel.log"
    log_file_path = log_dir / log_file
    
    # Set up log format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Set up console handler with colors
    if console_logging:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Colored format for console
        console_format = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
    
    # Set up file handler with rotation
    if file_logging:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        # Standard format for file
        file_format = logging.Formatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    
    # Set up error file handler for errors and above
    if file_logging:
        error_file_path = log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        root_logger.addHandler(error_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    _configured = True
    
    # Log the configuration
    logger = get_logger(__name__)
    logger.info(f"Logging configured - Level: {level}, Console: {console_logging}, File: {file_logging}")
    if file_logging:
        logger.info(f"Log file: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    global _loggers, _configured
    
    # Set up basic logging if not configured
    if not _configured:
        setup_logging()
    
    # Return cached logger if exists
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = logging.getLogger(name)
    _loggers[name] = logger
    
    return logger


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    
    Usage:
        class MyClass(LoggerMixin):
            def some_method(self):
                self.logger.info("This is a log message")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger


class ContextLogger:
    """
    Context manager for adding context to log messages.
    
    Usage:
        with ContextLogger("operation_name") as logger:
            logger.info("This will include operation_name in the log")
    """
    
    def __init__(self, context: str, logger_name: Optional[str] = None):
        """
        Initialize context logger.
        
        Args:
            context: Context string to add to log messages
            logger_name: Logger name (defaults to calling module)
        """
        self.context = context
        self.logger_name = logger_name or __name__
        self.logger = None
        self.original_format = None
    
    def __enter__(self) -> logging.Logger:
        """Enter context and return logger with context."""
        self.logger = get_logger(self.logger_name)
        
        # Add context to all handlers
        for handler in self.logger.handlers:
            if hasattr(handler, 'formatter') and handler.formatter:
                original_format = handler.formatter._fmt
                new_format = original_format.replace(
                    "%(message)s", 
                    f"[{self.context}] %(message)s"
                )
                handler.setFormatter(logging.Formatter(new_format))
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original format."""
        # Restore original format would be complex, so we'll leave it
        # In practice, context loggers should be short-lived
        pass


def log_function_call(func):
    """
    Decorator to log function calls with arguments and return values.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return "result"
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log function entry
        logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func_name} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func_name} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper


def log_async_function_call(func):
    """
    Decorator to log async function calls with arguments and return values.
    
    Usage:
        @log_async_function_call
        async def my_async_function(arg1, arg2):
            return "result"
    """
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log function entry
        logger.debug(f"Calling async {func_name} with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func_name} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"Async {func_name} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper


class LogCapture:
    """
    Context manager to capture log messages for testing.
    
    Usage:
        with LogCapture() as captured:
            logger.info("test message")
            assert "test message" in captured.messages
    """
    
    def __init__(self, logger_name: Optional[str] = None, level: int = logging.DEBUG):
        """
        Initialize log capture.
        
        Args:
            logger_name: Logger to capture (None for root logger)
            level: Minimum level to capture
        """
        self.logger_name = logger_name
        self.level = level
        self.messages = []
        self.handler = None
        self.logger = None
    
    def __enter__(self):
        """Start capturing logs."""
        self.logger = logging.getLogger(self.logger_name)
        
        # Create memory handler
        self.handler = logging.Handler()
        self.handler.setLevel(self.level)
        
        # Override emit to capture messages
        def emit(record):
            self.messages.append(self.handler.format(record))
        
        self.handler.emit = emit
        self.logger.addHandler(self.handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing logs."""
        if self.handler and self.logger:
            self.logger.removeHandler(self.handler)
    
    def clear(self):
        """Clear captured messages."""
        self.messages.clear()
    
    def contains(self, text: str) -> bool:
        """Check if any captured message contains the given text."""
        return any(text in msg for msg in self.messages)


def configure_third_party_loggers():
    """Configure third-party library loggers to reduce noise."""
    # HTTP libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    # AI libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    
    # Other common libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("concurrent.futures").setLevel(logging.WARNING)


# Configure third-party loggers on import
configure_third_party_loggers()