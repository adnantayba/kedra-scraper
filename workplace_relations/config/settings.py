"""
Centralized settings management for the workplace relations scraper.
"""

import os
from typing import Dict, Any, Optional
from .constants import *


class Settings:
    """
    Centralized settings management class.
    Implements the Singleton pattern for consistent configuration access.
    """

    _instance: Optional["Settings"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._load_settings()
        self._initialized = True

    def _load_settings(self):
        """Load all settings from constants and environment variables."""
        # Scrapy settings
        self.BOT_NAME = BOT_NAME
        self.SPIDER_MODULES = SPIDER_MODULES
        self.NEWSPIDER_MODULE = NEWSPIDER_MODULE

        # Storage settings
        self.STORAGE_BASE = os.environ.get("STORAGE_BASE", STORAGE_BASE)
        self.PROCESSED_STORAGE_BASE = os.environ.get(
            "PROCESSED_STORAGE_BASE", PROCESSED_STORAGE_BASE
        )

        # MongoDB settings
        self.MONGO_URI = os.environ.get("MONGO_URI", MONGO_URI)
        self.MONGO_DATABASE = os.environ.get("MONGO_DATABASE", MONGO_DATABASE)
        self.MONGO_LANDING_COLLECTION = os.environ.get(
            "MONGO_LANDING_COLLECTION", MONGO_LANDING_COLLECTION
        )
        self.MONGO_PROCESSED_COLLECTION = os.environ.get(
            "MONGO_PROCESSED_COLLECTION", MONGO_PROCESSED_COLLECTION
        )

        # Spider settings
        self.MAX_DOCUMENTS = int(os.environ.get("MAX_DOCUMENTS", MAX_DOCUMENTS))
        self.ALLOWED_DOMAINS = ALLOWED_DOMAINS
        self.START_URL = START_URL
        self.USER_AGENT = USER_AGENT

        # Concurrency settings
        self.CONCURRENT_REQUESTS = int(
            os.environ.get("CONCURRENT_REQUESTS", CONCURRENT_REQUESTS)
        )
        self.CONCURRENT_REQUESTS_PER_DOMAIN = int(
            os.environ.get(
                "CONCURRENT_REQUESTS_PER_DOMAIN", CONCURRENT_REQUESTS_PER_DOMAIN
            )
        )
        self.DOWNLOAD_DELAY = float(os.environ.get("DOWNLOAD_DELAY", DOWNLOAD_DELAY))

        # File processing settings
        self.SUPPORTED_FILE_TYPES = SUPPORTED_FILE_TYPES
        self.DATE_FORMAT_INPUT = DATE_FORMAT_INPUT
        self.DATE_FORMAT_DISPLAY = DATE_FORMAT_DISPLAY
        self.DATE_FORMAT_PARTITION = DATE_FORMAT_PARTITION
        self.PROCESSING_VERSION = PROCESSING_VERSION

    def get_scrapy_settings(self) -> Dict[str, Any]:
        """Get Scrapy-specific settings dictionary."""
        return {
            "BOT_NAME": self.BOT_NAME,
            "SPIDER_MODULES": self.SPIDER_MODULES,
            "NEWSPIDER_MODULE": self.NEWSPIDER_MODULE,
            "USER_AGENT": self.USER_AGENT,
            "ROBOTSTXT_OBEY": True,
            "CONCURRENT_REQUESTS": self.CONCURRENT_REQUESTS,
            "CONCURRENT_REQUESTS_PER_DOMAIN": self.CONCURRENT_REQUESTS_PER_DOMAIN,
            "DOWNLOAD_DELAY": self.DOWNLOAD_DELAY,
            "COOKIES_ENABLED": False,
            "TELNETCONSOLE_ENABLED": False,
            "DOWNLOADER_MIDDLEWARES": {
                "workplace_relations.middlewares.WorkplaceRelationsDownloaderMiddleware": 543,
            },
            "ITEM_PIPELINES": {
                "workplace_relations.pipelines.landing_pipeline.LandingPipeline": 300,
            },
            "LOG_LEVEL": "DEBUG",
            "EXTENSIONS": {
                "scrapy.extensions.logstats.LogStats": None,
                "scrapy.extensions.corestats.CoreStats": None,
            },
            "FEED_EXPORT_ENCODING": "utf-8",
        }

    def get_mongo_config(self) -> Dict[str, str]:
        """Get MongoDB configuration."""
        return {
            "uri": self.MONGO_URI,
            "database": self.MONGO_DATABASE,
            "landing_collection": self.MONGO_LANDING_COLLECTION,
            "processed_collection": self.MONGO_PROCESSED_COLLECTION,
        }

    def get_storage_config(self) -> Dict[str, str]:
        """Get storage configuration."""
        return {
            "storage_base": self.STORAGE_BASE,
            "processed_storage_base": self.PROCESSED_STORAGE_BASE,
        }


# Global settings instance
settings = Settings()
