"""
Document model for workplace relations data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib


@dataclass
class Document:
    """
    Document model representing a workplace relations document.
    
    Attributes:
        identifier: Unique identifier for the document
        description: Document description
        published_date: Publication date
        link_to_doc: URL to the original document
        partition_date: Date used for partitioning
        body: Decision-making body
        file_path: Path to stored file
        file_hash: Hash of file content
        file_type: File extension
        original_file_path: Original file path (for processed documents)
        processed_at: Processing timestamp
        processing_version: Version of processing applied
        metadata: Additional metadata
    """
    
    identifier: str
    description: Optional[str] = None
    published_date: Optional[str] = None
    link_to_doc: Optional[str] = None
    partition_date: Optional[str] = None
    body: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_type: Optional[str] = None
    original_file_path: Optional[str] = None
    processed_at: Optional[str] = None
    processing_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Internal Scrapy fields (for compatibility)
    depth: Optional[int] = None
    download_timeout: Optional[float] = None
    download_slot: Optional[str] = None
    download_latency: Optional[float] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.processed_at is None:
            self.processed_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            'identifier': self.identifier,
            'description': self.description,
            'published_date': self.published_date,
            'link_to_doc': self.link_to_doc,
            'partition_date': self.partition_date,
            'body': self.body,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'file_type': self.file_type,
            'original_file_path': self.original_file_path,
            'processed_at': self.processed_at,
            'processing_version': self.processing_version,
            'metadata': self.metadata,
            'depth': self.depth,
            'download_timeout': self.download_timeout,
            'download_slot': self.download_slot,
            'download_latency': self.download_latency,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary."""
        return cls(**data)
    
    def calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def is_processed(self) -> bool:
        """Check if document has been processed."""
        return self.original_file_path is not None
    
    def get_storage_key(self) -> str:
        """Get storage key for the document."""
        return f"{self.body}/{self.partition_date}/{self.identifier}"
    
    def validate(self) -> bool:
        """Validate document data."""
        return (
            self.identifier is not None and
            self.body is not None and
            self.partition_date is not None
        ) 