"""
Document service for handling document processing business logic.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from ..models import Document
from .storage_service import StorageService
from workplace_relations.config import settings, get_logger
from ..utils import DateUtils

logger = get_logger(__name__)


class DocumentService:
    """
    Service for handling document processing operations.
    Implements business logic for document transformation and processing.
    """

    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage_service = storage_service or StorageService()
        self.storage_config = settings.get_storage_config()

    def handle_duplicates(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Identify and handle duplicate documents based on identifier.

        Args:
            documents: List of documents to check

        Returns:
            Dictionary with:
            - total_duplicates: Count of duplicate identifiers found
            - duplicates: List of duplicate groups
            - action_taken: Description of actions taken
        """
        if not documents:
            return {
                "total_duplicates": 0,
                "duplicates": [],
                "action_taken": "No documents provided",
            }

        # Group documents by identifier
        grouped = {}
        for doc in documents:
            grouped.setdefault(doc.identifier, []).append(doc)

        # Filter only duplicates
        duplicates = {k: v for k, v in grouped.items() if len(v) > 1}

        if not duplicates:
            return {
                "total_duplicates": 0,
                "duplicates": [],
                "action_taken": "No duplicates found",
            }

        # For each duplicate group, keep the most recent one based on published_date
        actions = []
        for identifier, docs in duplicates.items():
            # Sort by published_date (newest first)
            sorted_docs = sorted(
                docs,
                key=lambda x: DateUtils.parse_date(x.published_date) or datetime.min,
                reverse=True,
            )

            # Keep the first one (most recent), mark others as duplicates
            keeper = sorted_docs[0]
            for doc in sorted_docs[1:]:
                self.storage_service.delete_document(doc.file_path)
                actions.append(
                    f"Deleted duplicate {doc.identifier} (keeping {keeper.identifier})"
                )

        return {
            "total_duplicates": len(duplicates),
            "duplicates": list(duplicates.keys()),
            "action_taken": f"Processed {len(duplicates)} duplicate groups",
            "actions": actions,
        }

    def process_document(self, document: Document) -> Optional[Document]:
        """
        Process a document by transforming its content and creating a processed version.

        Args:
            document: Original document to process

        Returns:
            Processed document or None if processing failed
        """
        try:
            if not document.file_path or not self.storage_service.document_exists(
                document.file_path
            ):
                logger.warning(f"Document file not found: {document.file_path}")
                return None

            # Read original content
            original_content = self.storage_service.retrieve_document(
                document.file_path
            )
            if original_content is None:
                return None

            # Process content based on file type
            processed_content = self._process_content(
                original_content, document.file_type
            )
            if processed_content is None:
                return None

            # Create processed document
            processed_doc = self._create_processed_document(document, processed_content)

            # Store processed document
            if not self._store_processed_document(processed_doc, processed_content):
                return None

            return processed_doc

        except Exception as e:
            logger.error(f"Failed to process document {document.identifier}: {e}")
            return None

    def _process_content(
        self, content: bytes, file_type: Optional[str]
    ) -> Optional[bytes]:
        """Process document content based on file type."""
        if not file_type:
            return content

        try:
            if file_type.lower() == "html":
                return self._process_html_content(content)
            else:
                # For PDF/DOC files, return content as-is
                return content
        except Exception as e:
            logger.error(f"Failed to process content: {e}")
            return None

    def _process_html_content(self, content: bytes) -> bytes:
        """Process HTML content by extracting relevant sections."""
        try:
            soup = BeautifulSoup(content.decode("utf-8"), "html.parser")

            # Extract relevant content (adjust selectors as needed)
            content_div = soup.find("div", {"class": "col-sm-9"})
            if not content_div:
                content_div = soup.find("body") or soup

            return str(content_div).encode("utf-8")
        except Exception as e:
            logger.error(f"Failed to process HTML content: {e}")
            return content

    def _create_processed_document(
        self, original_doc: Document, processed_content: bytes
    ) -> Document:
        """Create a processed document from the original."""
        # Calculate new hash
        new_file_hash = original_doc.calculate_file_hash(processed_content)

        # Create new filename
        safe_identifier = self._sanitize_filename(original_doc.identifier)[:100]
        new_filename = f"{safe_identifier}.{original_doc.file_type}"

        # Create new storage path
        new_storage_path = os.path.join(
            self.storage_config["processed_storage_base"],
            self._sanitize_filename(original_doc.body or "unknown"),
            original_doc.partition_date or "unknown",
        )
        new_file_path = os.path.join(new_storage_path, new_filename)

        # Create processed document
        processed_doc = Document(
            identifier=original_doc.identifier,
            description=original_doc.description,
            published_date=original_doc.published_date,
            link_to_doc=original_doc.link_to_doc,
            partition_date=original_doc.partition_date,
            body=original_doc.body,
            file_path=new_file_path,
            file_hash=new_file_hash,
            file_type=original_doc.file_type,
            original_file_path=original_doc.file_path,
            processed_at=datetime.utcnow().isoformat(),
            processing_version=settings.PROCESSING_VERSION,
        )

        return processed_doc

    def _store_processed_document(self, document: Document, content: bytes) -> bool:
        """Store processed document content."""
        try:
            os.makedirs(os.path.dirname(document.file_path), exist_ok=True)
            with open(document.file_path, "wb") as f:
                f.write(content)
            logger.debug(f"Stored processed document: {document.file_path}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to store processed document {document.file_path}: {e}"
            )
            return False

    def _sanitize_filename(self, name: str) -> str:
        """Convert string to safe filename."""
        keepchars = (" ", ".", "_", "-")
        return "".join(c for c in name if c.isalnum() or c in keepchars).rstrip()

    def validate_document(self, document: Document) -> bool:
        """Validate document data."""
        return document.validate()

    def get_document_statistics(self, documents: List[Document]) -> Dict[str, Any]:
        """Get statistics about a collection of documents."""
        if not documents:
            return {
                "total_documents": 0,
                "processed_documents": 0,
                "file_types": {},
                "bodies": {},
                "date_range": None,
            }

        stats = {
            "total_documents": len(documents),
            "processed_documents": sum(1 for doc in documents if doc.is_processed()),
            "file_types": {},
            "bodies": {},
            "date_range": {"earliest": None, "latest": None},
        }

        for doc in documents:
            # Count file types
            file_type = doc.file_type or "unknown"
            stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1

            # Count bodies
            body = doc.body or "unknown"
            stats["bodies"][body] = stats["bodies"].get(body, 0) + 1

            # Track date range
            if doc.published_date:
                try:
                    date_obj = datetime.strptime(
                        doc.published_date, settings.DATE_FORMAT_DISPLAY
                    )
                    if (
                        not stats["date_range"]["earliest"]
                        or date_obj < stats["date_range"]["earliest"]
                    ):
                        stats["date_range"]["earliest"] = date_obj
                    if (
                        not stats["date_range"]["latest"]
                        or date_obj > stats["date_range"]["latest"]
                    ):
                        stats["date_range"]["latest"] = date_obj
                except ValueError:
                    pass

        return stats
