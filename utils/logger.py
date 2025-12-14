"""
Logging Configuration

Sets up logging for the hotel training system.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = None, log_level: str = "INFO") -> logging.Logger:
    """
    Set up logger with file and console handlers

    Args:
        name: Logger name (uses __name__ if None)
        log_level: Logging level

    Returns:
        Configured logger
    """
    if name is None:
        name = "hotel_training_system"

    # Create logger
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # File handler - rotating log files
    log_file = log_dir / f"hotel_training_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)

    # Error file handler - separate file for errors
    error_log_file = log_dir / f"hotel_training_errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the standard configuration

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

class ContextFilter(logging.Filter):
    """Add context information to log records"""

    def __init__(self, session_id: str = None):
        super().__init__()
        self.session_id = session_id

    def filter(self, record):
        if self.session_id:
            record.session_id = self.session_id
        else:
            record.session_id = "no-session"
        return True

def add_session_context(logger: logging.Logger, session_id: str):
    """
    Add session context to logger

    Args:
        logger: Logger to add context to
        session_id: Session identifier
    """
    context_filter = ContextFilter(session_id)
    logger.addFilter(context_filter)

    # Update formatter to include session ID
    for handler in logger.handlers:
        if isinstance(handler.formatter, logging.Formatter):
            format_str = handler.formatter._fmt
            if "session_id" not in format_str:
                new_format = format_str.replace(
                    "%(levelname)s",
                    "%(levelname)s - [%(session_id)s]"
                )
                handler.setFormatter(logging.Formatter(new_format))

def log_performance(func):
    """Decorator to log function performance"""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {duration:.3f}s")
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise

    return wrapper