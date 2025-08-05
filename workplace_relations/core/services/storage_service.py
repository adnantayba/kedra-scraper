"""
Storage service for managing file storage operations.
Implements the Strategy pattern for different storage backends.
"""

import os
import hashlib
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from workplace_relations.core import Document
from workplace_relations.config.settings import settings
from workplace_relations.config.logging_config import get_logger

logger = get_logger(__name__)


class StorageStrategy(ABC):
    """Abstract base class for storage strategies."""
    
    @abstractmethod
    def store_file(self, content: bytes, file_path: str) -> bool:
        """Store file content at the specified path."""
        pass
    
    @abstractmethod
    def retrieve_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content from the specified path."""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists at the specified path."""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete file at the specified path."""
        pass


class LocalFileStorageStrategy(StorageStrategy):
    """Local filesystem storage strategy."""
    
    def store_file(self, content: bytes, file_path: str) -> bool:
        """Store file content to local filesystem."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.debug(f"Stored file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store file {file_path}: {e}")
            return False
    
    def retrieve_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content from local filesystem."""
        try:
            if not self.file_exists(file_path):
                return None
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to retrieve file {file_path}: {e}")
            return None
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local filesystem."""
        return os.path.exists(file_path)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from local filesystem."""
        try:
            if self.file_exists(file_path):
                os.remove(file_path)
                logger.debug(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False


class StorageService:
    """
    Storage service that manages file operations using different storage strategies.
    Implements the Strategy pattern and Factory pattern.
    """
    
    def __init__(self, strategy: Optional[StorageStrategy] = None):
        self.strategy = strategy or LocalFileStorageStrategy()
        self.storage_config = settings.get_storage_config()
    
    def download_and_store_document(self, document: Document) -> Optional[Dict[str, Any]]:
        """
        Download document from URL and store it using the storage strategy.
        
        Args:
            document: Document object containing URL and metadata
            
        Returns:
            Dictionary with file information or None if failed
        """
        if not document.link_to_doc:
            logger.warning(f"No link provided for document {document.identifier}")
            return None
        
        try:
            # Download file content
            content, file_type = self._download_file_content(document.link_to_doc)
            if content is None:
                return None
            
            # Calculate file hash
            file_hash = document.calculate_file_hash(content)
            
            # Determine file extension
            file_ext = self._get_file_extension(document.link_to_doc, file_type)
            
            # Create storage path
            storage_path = self._create_storage_path(document, file_ext)
            
            # Store file
            if not self.strategy.store_file(content, storage_path):
                return None
            
            return {
                'file_path': storage_path,
                'file_hash': file_hash,
                'file_type': file_ext,
            }
            
        except Exception as e:
            logger.error(f"Failed to download and store document {document.identifier}: {e}")
            return None
    
    def _download_file_content(self, url: str) -> tuple[Optional[bytes], Optional[str]]:
        """Download file content from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get('content-type', '').lower()
            
            if 'pdf' in content_type:
                return response.content, 'pdf'
            elif 'msword' in content_type or 'docx' in content_type:
                return response.content, 'docx' if 'docx' in content_type else 'doc'
            else:
                # Assume HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                return str(soup).encode('utf-8'), 'html'
                
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            return None, None
    
    def _get_file_extension(self, url: str, content_type: Optional[str]) -> str:
        """Determine file extension from URL and content type."""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        if path.endswith('.pdf'):
            return 'pdf'
        elif path.endswith('.docx'):
            return 'docx'
        elif path.endswith('.doc'):
            return 'doc'
        elif content_type:
            if 'pdf' in content_type:
                return 'pdf'
            elif 'docx' in content_type:
                return 'docx'
            elif 'msword' in content_type:
                return 'doc'
        
        return 'html'
    
    def _create_storage_path(self, document: Document, file_ext: str) -> str:
        """Create storage path for the document."""
        # Sanitize filename
        safe_identifier = self._sanitize_filename(document.identifier)[:100]
        filename = f"{safe_identifier}_{document.calculate_file_hash(b'')[:8]}.{file_ext}"
        
        # Create organized storage path
        storage_path = os.path.join(
            self.storage_config['storage_base'],
            self._sanitize_filename(document.body),
            document.partition_date or 'unknown'
        )
        
        return os.path.join(storage_path, filename)
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert string to safe filename."""
        keepchars = (' ', '.', '_', '-')
        return ''.join(c for c in name if c.isalnum() or c in keepchars).rstrip()
    
    def retrieve_document(self, file_path: str) -> Optional[bytes]:
        """Retrieve document content from storage."""
        return self.strategy.retrieve_file(file_path)
    
    def document_exists(self, file_path: str) -> bool:
        """Check if document exists in storage."""
        return self.strategy.file_exists(file_path)
    
    def delete_document(self, file_path: str) -> bool:
        """Delete document from storage."""
        return self.strategy.delete_file(file_path) 