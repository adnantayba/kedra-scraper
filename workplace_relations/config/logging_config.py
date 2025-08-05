"""
Logging configuration for the workplace relations scraper.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggingConfig:
    """Configuration class for logging setup."""
    
    def __init__(self):
        self.enabled = os.environ.get("LOGGING_ENABLED", "true").lower() == "true"
        self.level = os.environ.get("LOG_LEVEL", "INFO").upper()
        self.log_dir = os.environ.get("LOG_DIR", "logs")
        self.log_file = os.path.join(self.log_dir, "workplace_relations.log")
        self.max_bytes = 5 * 1024 * 1024  # 5 MB
        self.backup_count = 5
        self.log_format = "%(asctime)s | %(levelname)s | %(name)s | %(module)s:%(lineno)d | %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"
        
        # Create logs directory if logging is enabled
        if self.enabled and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger instance."""
        logger = logging.getLogger(f"workplace_relations.{name}")
        
        if not self.enabled:
            logger.addHandler(logging.NullHandler())
            return logger
        
        if not logger.handlers:  # Avoid duplicate handlers
            logger.setLevel(self.level)
            formatter = logging.Formatter(self.log_format, datefmt=self.date_format)
            
            # File handler with rotation
            file_handler = RotatingFileHandler(
                self.log_file, 
                maxBytes=self.max_bytes, 
                backupCount=self.backup_count, 
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger


# Global logging configuration instance
_logging_config = LoggingConfig()


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance for the workplace relations scraper.
    
    Args:
        name: The name for the logger (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return _logging_config.get_logger(name) 