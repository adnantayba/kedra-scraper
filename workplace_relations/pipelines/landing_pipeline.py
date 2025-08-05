"""
Landing pipeline for initial document processing and storage.
"""

from typing import Any, Optional
from pymongo import MongoClient
from scrapy import Spider

from .base_pipeline import BasePipeline
from workplace_relations.core import Document, StorageService
from workplace_relations.config import settings, get_logger

logger = get_logger(__name__)


class LandingPipeline(BasePipeline):
    """
    Pipeline for processing documents into the landing zone.
    Handles file download, storage, and metadata persistence.
    """

    def __init__(self):
        super().__init__()
        self.storage_service = StorageService()
        self.mongo_client: Optional[MongoClient] = None
        self.mongo_collection = None
        self.mongo_config = settings.get_mongo_config()

    def _setup_pipeline(self, spider: Spider):
        """Setup MongoDB connection and storage."""
        try:
            self.mongo_client = MongoClient(self.mongo_config["uri"])
            db = self.mongo_client[self.mongo_config["database"]]
            self.mongo_collection = db[self.mongo_config["landing_collection"]]
            self.logger.info("Connected to MongoDB for landing pipeline")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _cleanup_pipeline(self, spider: Spider):
        """Cleanup MongoDB connection."""
        try:
            if self.mongo_client:
                self.mongo_client.close()
                self.logger.info("Closed MongoDB connection")
        except Exception as e:
            self.logger.error(f"Error closing MongoDB connection: {e}")

    def _process_item(self, item: Any, spider: Spider) -> Any:
        """
        Process item through landing pipeline.

        Args:
            item: Scrapy item to process
            spider: Spider instance

        Returns:
            Processed item
        """
        item_dict = self._get_item_dict(item)
        identifier = item_dict.get("identifier", "unknown")

        self.logger.info(f"Processing item: {identifier}")

        try:
            # Convert to Document model
            document = Document.from_dict(item_dict)

            # Validate document
            if not document.validate():
                self.logger.warning(f"Invalid document data for {identifier}")
                return item

            # Download and store file
            file_info = self.storage_service.download_and_store_document(document)
            if file_info:
                # Update document with file information
                document.file_path = file_info["file_path"]
                document.file_hash = file_info["file_hash"]
                document.file_type = file_info["file_type"]

                # Update item with file information
                item_dict.update(file_info)

            # Store in MongoDB
            self._store_in_mongodb(document)

            # Update item with any additional processing
            self._update_item_from_document(item, document)

            return item

        except Exception as e:
            self.logger.error(f"Failed to process item {identifier}: {e}")
            raise

    def _store_in_mongodb(self, document: Document):
        """Store document metadata in MongoDB."""
        try:
            document_dict = document.to_dict()
            result = self.mongo_collection.insert_one(document_dict)
            self.logger.info(
                f"Stored document {document.identifier} (ID: {result.inserted_id})"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to store document {document.identifier} in MongoDB: {e}"
            )
            raise

    def _update_item_from_document(self, item: Any, document: Document):
        """Update Scrapy item with document data."""
        try:
            # Update item fields with document data
            item.file_path = document.file_path
            item.file_hash = document.file_hash
            item.file_type = document.file_type
        except Exception as e:
            self.logger.error(f"Failed to update item from document: {e}")

    def _pre_process_item(self, item: Any, spider: Spider) -> Any:
        """Pre-processing: validate and sanitize item data."""
        item_dict = self._get_item_dict(item)

        # Basic validation
        if not item_dict.get("identifier"):
            self.logger.warning("Item missing identifier")
            return item

        # Sanitize string fields
        for field in ["identifier", "description", "body"]:
            if field in item_dict and item_dict[field]:
                item_dict[field] = item_dict[field].strip()

        return item

    def _post_process_item(self, item: Any, spider: Spider) -> Any:
        """Post-processing: log success and update statistics."""
        item_dict = self._get_item_dict(item)
        identifier = item_dict.get("identifier", "unknown")

        self.logger.info(f"Successfully processed item: {identifier}")

        # Update spider statistics if available
        if hasattr(spider, "document_count"):
            spider.document_count += 1

        return item

    def _handle_error(self, item: Any, spider: Spider, error: Exception) -> Any:
        """Handle processing errors."""
        item_dict = self._get_item_dict(item)
        identifier = item_dict.get("identifier", "unknown")

        self.logger.error(f"Pipeline error for item {identifier}: {error}")

        # You could implement error recovery logic here
        # For now, we'll just return the item as-is
        return item
