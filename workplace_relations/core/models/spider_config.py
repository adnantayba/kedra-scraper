"""
Spider configuration model for workplace relations scraper.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Set


@dataclass
class SpiderConfig:
    """
    Configuration model for spider execution.
    
    Attributes:
        start_date: Start date for scraping
        end_date: End date for scraping
        bodies: List of bodies to scrape (None for all)
        max_documents: Maximum number of documents to scrape
        storage_base: Base directory for storage
        user_agent: User agent string
        download_delay: Delay between requests
        concurrent_requests: Number of concurrent requests
    """
    
    start_date: date
    end_date: date
    bodies: Optional[List[str]] = None
    max_documents: int = 1000
    storage_base: str = "storage"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    download_delay: float = 1.5
    concurrent_requests: int = 16
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
        
        if self.max_documents <= 0:
            raise ValueError("Max documents must be positive")
        
        if self.download_delay < 0:
            raise ValueError("Download delay must be non-negative")
        
        if self.concurrent_requests <= 0:
            raise ValueError("Concurrent requests must be positive")
    
    def get_body_filter(self) -> Optional[Set[str]]:
        """Get set of body names to filter by."""
        if self.bodies is None:
            return None
        return {body.strip().lower() for body in self.bodies if body.strip()}
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'bodies': self.bodies,
            'max_documents': self.max_documents,
            'storage_base': self.storage_base,
            'user_agent': self.user_agent,
            'download_delay': self.download_delay,
            'concurrent_requests': self.concurrent_requests,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SpiderConfig':
        """Create configuration from dictionary."""
        start_date = date.fromisoformat(data['start_date'])
        end_date = date.fromisoformat(data['end_date'])
        
        return cls(
            start_date=start_date,
            end_date=end_date,
            bodies=data.get('bodies'),
            max_documents=data.get('max_documents', 1000),
            storage_base=data.get('storage_base', 'storage'),
            user_agent=data.get('user_agent'),
            download_delay=data.get('download_delay', 1.5),
            concurrent_requests=data.get('concurrent_requests', 16),
        ) 