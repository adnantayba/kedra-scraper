"""
Monitoring utilities for tracking scraping performance and metrics.
"""

from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass
import time
import psutil
from workplace_relations.config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Class to track performance metrics."""

    start_time: float
    end_time: float = 0.0
    documents_processed: int = 0
    documents_failed: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


class ScraperMonitor:
    """Monitoring service for scraping operations."""

    def __init__(self):
        self.metrics = PerformanceMetrics(start_time=time.time())
        self.process = psutil.Process()

    def update_metrics(self) -> None:
        """Update current system metrics."""
        self.metrics.memory_usage_mb = self.process.memory_info().rss / (1024 * 1024)
        self.metrics.cpu_usage_percent = self.process.cpu_percent()

    def document_processed(self, success: bool = True) -> None:
        """Record document processing attempt."""
        if success:
            self.metrics.documents_processed += 1
        else:
            self.metrics.documents_failed += 1
        self.update_metrics()

    def finalize(self) -> Dict[str, Any]:
        """Finalize metrics and return results."""
        self.metrics.end_time = time.time()
        self.update_metrics()

        elapsed = self.metrics.end_time - self.metrics.start_time
        docs_per_sec = self.metrics.documents_processed / elapsed if elapsed > 0 else 0

        return {
            "start_time": datetime.fromtimestamp(self.metrics.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.metrics.end_time).isoformat(),
            "duration_seconds": round(elapsed, 2),
            "documents_processed": self.metrics.documents_processed,
            "documents_failed": self.metrics.documents_failed,
            "success_rate": (
                round(
                    self.metrics.documents_processed
                    / (
                        self.metrics.documents_processed + self.metrics.documents_failed
                    ),
                    2,
                )
                if (self.metrics.documents_processed + self.metrics.documents_failed)
                > 0
                else 1.0
            ),
            "documents_per_second": round(docs_per_sec, 2),
            "peak_memory_usage_mb": round(self.metrics.memory_usage_mb, 2),
            "average_cpu_usage_percent": round(self.metrics.cpu_usage_percent, 2),
        }

    def log_metrics(self) -> None:
        """Log the collected metrics."""
        metrics = self.finalize()
        logger.info("Scraping Metrics:")
        for key, value in metrics.items():
            logger.info(f"{key.replace('_', ' ').title()}: {value}")
