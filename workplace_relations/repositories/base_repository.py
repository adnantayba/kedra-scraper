"""
Abstract base repository for data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository implementing the Repository pattern.
    Provides common data access operations.
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Find entity by ID."""
        pass

    @abstractmethod
    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Find all entities with optional filters."""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        pass

    def find_by_field(self, field: str, value: Any) -> Optional[T]:
        """Find entity by field value."""
        filters = {field: value}
        results = self.find_all(filters)
        return results[0] if results else None

    def find_by_fields(self, filters: Dict[str, Any]) -> List[T]:
        """Find entities by multiple field values."""
        return self.find_all(filters)

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        return len(self.find_all(filters))

    def find_by_date_range(
        self, date_field: str, start_date: datetime, end_date: datetime
    ) -> List[T]:
        """Find entities within a date range."""
        filters = {date_field: {"$gte": start_date, "$lte": end_date}}
        return self.find_all(filters)

    def find_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Find entities with pagination."""
        all_results = self.find_all(filters)
        total_count = len(all_results)

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_results = all_results[start_index:end_index]

        return {
            "data": paginated_results,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
        }
