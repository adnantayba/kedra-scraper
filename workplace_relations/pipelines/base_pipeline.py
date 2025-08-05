"""
Abstract base pipeline for Scrapy item processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from itemadapter import ItemAdapter
from scrapy import Spider

from workplace_relations.config import get_logger

logger = get_logger(__name__)


class BasePipeline(ABC):
    """
    Abstract base class for Scrapy pipelines.
    Implements the Template Method pattern.
    """

    def __init__(self):
        self.logger = logger

    def open_spider(self, spider: Spider):
        """Called when spider opens. Template method hook."""
        self.logger.info(f"Opening pipeline for spider: {spider.name}")
        self._setup_pipeline(spider)

    def close_spider(self, spider: Spider):
        """Called when spider closes. Template method hook."""
        self.logger.info(f"Closing pipeline for spider: {spider.name}")
        self._cleanup_pipeline(spider)

    def process_item(self, item: Any, spider: Spider) -> Any:
        """
        Process item through the pipeline. Template method.

        Args:
            item: Item to process
            spider: Spider instance

        Returns:
            Processed item
        """
        try:
            # Pre-processing hook
            item = self._pre_process_item(item, spider)

            # Main processing
            item = self._process_item(item, spider)

            # Post-processing hook
            item = self._post_process_item(item, spider)

            return item

        except Exception as e:
            self.logger.error(
                f"Error processing item in {self.__class__.__name__}: {e}"
            )
            return self._handle_error(item, spider, e)

    @abstractmethod
    def _process_item(self, item: Any, spider: Spider) -> Any:
        """
        Main item processing logic. Must be implemented by subclasses.

        Args:
            item: Item to process
            spider: Spider instance

        Returns:
            Processed item
        """
        pass

    def _setup_pipeline(self, spider: Spider):
        """Setup pipeline resources. Override if needed."""
        pass

    def _cleanup_pipeline(self, spider: Spider):
        """Cleanup pipeline resources. Override if needed."""
        pass

    def _pre_process_item(self, item: Any, spider: Spider) -> Any:
        """Pre-processing hook. Override if needed."""
        return item

    def _post_process_item(self, item: Any, spider: Spider) -> Any:
        """Post-processing hook. Override if needed."""
        return item

    def _handle_error(self, item: Any, spider: Spider, error: Exception) -> Any:
        """Handle processing errors. Override if needed."""
        self.logger.error(f"Pipeline error for item: {error}")
        return item

    def _get_item_dict(self, item: Any) -> Dict[str, Any]:
        """Convert item to dictionary."""
        return ItemAdapter(item).asdict()

    def _log_item_processing(self, item: Any, spider: Spider, stage: str):
        """Log item processing stage."""
        item_dict = self._get_item_dict(item)
        identifier = item_dict.get("identifier", "unknown")
        self.logger.debug(
            f"Processing item {identifier} in {self.__class__.__name__} - {stage}"
        )
