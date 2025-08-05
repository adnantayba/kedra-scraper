"""
Document repository interface for document data access operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from workplace_relations.core import Document
from .base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """
    Repository interface for document data access operations.
    Extends BaseRepository with document-specific operations.
    """
    
    def find_by_body(self, body: str) -> List[Document]:
        """Find documents by decision-making body."""
        return self.find_by_field('body', body)
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Document]:
        """Find documents within a date range."""
        return self.find_by_date_range('published_date', start_date, end_date)
    
    def find_by_file_type(self, file_type: str) -> List[Document]:
        """Find documents by file type."""
        return self.find_by_field('file_type', file_type)
    
    def find_processed_documents(self) -> List[Document]:
        """Find all processed documents."""
        return self.find_by_field('original_file_path', {'$exists': True, '$ne': None})
    
    def find_unprocessed_documents(self) -> List[Document]:
        """Find all unprocessed documents."""
        return self.find_by_field('original_file_path', None)
    
    def find_by_partition_date(self, partition_date: str) -> List[Document]:
        """Find documents by partition date."""
        return self.find_by_field('partition_date', partition_date)
    
    def find_by_hash(self, file_hash: str) -> Optional[Document]:
        """Find document by file hash."""
        return self.find_by_field('file_hash', file_hash)
    
    def find_duplicates(self) -> List[Document]:
        """Find documents with duplicate file hashes."""
        # This would need to be implemented in the concrete repository
        # as it requires aggregation or grouping operations
        raise NotImplementedError("find_duplicates must be implemented in concrete repository")
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics."""
        all_documents = self.find_all()
        
        stats = {
            'total_documents': len(all_documents),
            'processed_documents': len(self.find_processed_documents()),
            'unprocessed_documents': len(self.find_unprocessed_documents()),
            'file_types': {},
            'bodies': {},
            'date_range': {
                'earliest': None,
                'latest': None
            }
        }
        
        for doc in all_documents:
            # Count file types
            file_type = doc.file_type or 'unknown'
            stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1
            
            # Count bodies
            body = doc.body or 'unknown'
            stats['bodies'][body] = stats['bodies'].get(body, 0) + 1
            
            # Track date range
            if doc.published_date:
                try:
                    date_obj = datetime.strptime(doc.published_date, "%d/%m/%Y")
                    if not stats['date_range']['earliest'] or date_obj < stats['date_range']['earliest']:
                        stats['date_range']['earliest'] = date_obj
                    if not stats['date_range']['latest'] or date_obj > stats['date_range']['latest']:
                        stats['date_range']['latest'] = date_obj
                except ValueError:
                    pass
        
        return stats
    
    def find_by_processing_version(self, version: str) -> List[Document]:
        """Find documents by processing version."""
        return self.find_by_field('processing_version', version)
    
    def find_recent_documents(self, days: int = 30) -> List[Document]:
        """Find documents from the last N days."""
        end_date = datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        return self.find_by_date_range(start_date, end_date) 