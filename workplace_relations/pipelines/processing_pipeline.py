"""
Processing pipeline for document transformation and enrichment.
"""

from typing import Any, Optional
from pymongo import MongoClient
from scrapy import Spider

from .base_pipeline import BasePipeline
from workplace_relations.core import Document, DocumentService
from workplace_relations.config import settings, get_logger

logger = get_logger(__name__)


class ProcessingPipeline(BasePipeline):
    """
    Pipeline for processing and transforming documents.
    Handles document content processing and metadata enrichment.
    """

    def __init__(self):
        super().__init__()
        self.document_service = DocumentService()
        self.mongo_client: Optional[MongoClient] = None
        self.mongo_collection = None
        self.mongo_config = settings.get_mongo_config()

    def _setup_pipeline(self, spider: Spider):
        """Setup MongoDB connection for processed documents."""
        try:
            self.mongo_client = MongoClient(self.mongo_config["uri"])
            db = self.mongo_client[self.mongo_config["database"]]
            self.mongo_collection = db[self.mongo_config["processed_collection"]]
            self.logger.info("Connected to MongoDB for processing pipeline")
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
        Process item through processing pipeline.

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

            # Check if document is already processed
            if document.is_processed():
                self.logger.info(f"Document {identifier} already processed, skipping")
                return item

            # Process document
            processed_document = self.document_service.process_document(document)
            if processed_document:
                # Store processed document metadata
                self._store_processed_document(processed_document)

                # Update item with processed information
                self._update_item_from_processed_document(item, processed_document)

                self.logger.info(f"Successfully processed document: {identifier}")
            else:
                self.logger.warning(f"Failed to process document: {identifier}")

            return item

        except Exception as e:
            self.logger.error(f"Failed to process item {identifier}: {e}")
            raise

    def _store_processed_document(self, document: Document):
        """Store processed document metadata in MongoDB."""
        try:
            document_dict = document.to_dict()
            result = self.mongo_collection.insert_one(document_dict)
            self.logger.info(
                f"Stored processed document {document.identifier} (ID: {result.inserted_id})"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to store processed document {document.identifier} in MongoDB: {e}"
            )
            raise

    def _update_item_from_processed_document(self, item: Any, document: Document):
        """Update Scrapy item with processed document data."""
        try:
            # Update item fields with processed document data
            item.file_path = document.file_path
            item.file_hash = document.file_hash
            item.original_file_path = document.original_file_path
            item.processed_at = document.processed_at
            item.processing_version = document.processing_version
        except Exception as e:
            self.logger.error(f"Failed to update item from processed document: {e}")

    def _pre_process_item(self, item: Any, spider: Spider) -> Any:
        """Pre-processing: validate document for processing."""
        item_dict = self._get_item_dict(item)

        # Check if document has required fields for processing
        if not item_dict.get("file_path"):
            self.logger.warning("Item missing file_path, skipping processing")
            return None

        if not item_dict.get("identifier"):
            self.logger.warning("Item missing identifier")
            return item

        return item

    def _post_process_item(self, item: Any, spider: Spider) -> Any:
        """Post-processing: log success and update statistics."""
        if item is None:
            return item

        item_dict = self._get_item_dict(item)
        identifier = item_dict.get("identifier", "unknown")

        self.logger.info(f"Successfully completed processing for item: {identifier}")

        # Update spider statistics if available
        if hasattr(spider, "processed_count"):
            spider.processed_count += 1

        return item

    def _handle_error(self, item: Any, spider: Spider, error: Exception) -> Any:
        """Handle processing errors."""
        item_dict = self._get_item_dict(item)
        identifier = item_dict.get("identifier", "unknown")

        self.logger.error(f"Processing pipeline error for item {identifier}: {error}")

        # You could implement error recovery logic here
        # For now, we'll just return the item as-is
        return item
