"""
Core business logic services for the workplace relations scraper.
"""

from .storage_service import StorageService
from .document_service import DocumentService

__all__ = ['StorageService', 'DocumentService'] 