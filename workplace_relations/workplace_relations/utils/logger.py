# utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

# Environment variables for logging configuration
LOGGING_ENABLED = os.environ.get("LOGGING_ENABLED", "true").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "workplace_relations.log")
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5

# Create logs directory only if logging is enabled
if LOGGING_ENABLED and not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(module)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class _LoggerSingleton:
    _configured = False

    @classmethod
    def configure(cls):
        if cls._configured:
            return
        logger = logging.getLogger("workplace_relations")

        if not LOGGING_ENABLED:
            logger.addHandler(logging.NullHandler())
            cls._configured = True
            return

        logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        # Avoid duplicate handlers
        if not logger.handlers:
            # File handler with rotation
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        cls._configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance for the workplace relations scraper

    Usage:
        from workplace_relations.utils.logger import get_logger
        logger = get_logger(__name__)
    """
    _LoggerSingleton.configure()
    return logging.getLogger(f"workplace_relations.{name}")
