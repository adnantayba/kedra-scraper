"""
Data access layer repositories for the workplace relations scraper.
"""

from .base_repository import BaseRepository
from .document_repository import DocumentRepository
from .mongo_repository import MongoRepository

__all__ = ['BaseRepository', 'DocumentRepository', 'MongoRepository'] 