import logging
import os
from logging.handlers import RotatingFileHandler
from config import settings

LOGGING_ENABLED = settings.konfiga_logging_enabled
LOG_LEVEL = settings.konfiga_log_level
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "konfiga_framework.log")
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
        root_logger = logging.getLogger()

        if not LOGGING_ENABLED:
            # If logging is disabled, set up a null handler
            root_logger.addHandler(logging.NullHandler())
            cls._configured = True
            return

        root_logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(LOG_LEVEL)
        root_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(LOG_LEVEL)
        root_logger.addHandler(console_handler)

        cls._configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with production-level configuration.
    The logging can be enabled/disabled using the KONFIGA_LOGGING_ENABLED environment variable.

    Environment variables:
        KONFIGA_LOGGING_ENABLED: Set to "false" to disable logging (default: "true")
        KONFIGA_LOG_LEVEL: Set the logging level (default: "INFO")
        KONFIGA_LOG_DIR: Set the directory for log files (default: "logs")

    Usage:
        from utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("message")  # Will only log if KONFIGA_LOGGING_ENABLED is "true"
    """
    _LoggerSingleton.configure()
    return logging.getLogger(name)
