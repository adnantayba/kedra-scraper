"""
Configuration management package for workplace relations scraper.
"""

from .settings import settings
from .constants import *
from .logging_config import get_logger

__all__ = ["settings", "get_logger"]
