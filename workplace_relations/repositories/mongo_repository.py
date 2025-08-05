"""
MongoDB implementation of the document repository.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, time, date
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from workplace_relations.core import Document
from .document_repository import DocumentRepository
from workplace_relations.config.settings import settings
from workplace_relations.config.logging_config import get_logger

logger = get_logger(__name__)


class MongoRepository(DocumentRepository):
    """
    MongoDB implementation of the document repository.
    Implements the Repository pattern for MongoDB.
    """
    
    def __init__(self, collection_name: str = 'landing_zone'):
        self.mongo_config = settings.get_mongo_config()
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self.collection_name = collection_name
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_config['uri'])
            self.database = self.client[self.mongo_config['database']]
            self.collection = self.database[self.collection_name]
            logger.info(f"Connected to MongoDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _disconnect(self):
        """Close MongoDB connection."""
        try:
            if self.client:
                self.client.close()
                logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    def create(self, entity: Document) -> Document:
        """Create a new document."""
        try:
            document_dict = entity.to_dict()
            result = self.collection.insert_one(document_dict)
            logger.info(f"Created document {entity.identifier} with ID: {result.inserted_id}")
            return entity
        except Exception as e:
            logger.error(f"Failed to create document {entity.identifier}: {e}")
            raise
    
    def find_by_id(self, entity_id: str) -> Optional[Document]:
        """Find document by identifier."""
        try:
            document_dict = self.collection.find_one({'identifier': entity_id})
            if document_dict:
                return Document.from_dict(document_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to find document by ID {entity_id}: {e}")
            return None
    
    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Find all documents with optional filters."""
        try:
            query = filters or {}
            cursor = self.collection.find(query)
            documents = []
            for document_dict in cursor:
                document_dict.pop('_id', None)  # Remove MongoDB's _id field
                documents.append(Document.from_dict(document_dict))
            return documents
        except Exception as e:
            logger.error(f"Failed to find documents: {e}")
            return []
    
    def update(self, entity: Document) -> Document:
        """Update an existing document."""
        try:
            document_dict = entity.to_dict()
            result = self.collection.replace_one(
                {'identifier': entity.identifier},
                document_dict
            )
            if result.modified_count > 0:
                logger.info(f"Updated document {entity.identifier}")
            else:
                logger.warning(f"No document found to update: {entity.identifier}")
            return entity
        except Exception as e:
            logger.error(f"Failed to update document {entity.identifier}: {e}")
            raise
    
    def delete(self, entity_id: str) -> bool:
        """Delete document by identifier."""
        try:
            result = self.collection.delete_one({'identifier': entity_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted document {entity_id}")
                return True
            else:
                logger.warning(f"No document found to delete: {entity_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete document {entity_id}: {e}")
            return False
    
    def exists(self, entity_id: str) -> bool:
        """Check if document exists."""
        try:
            count = self.collection.count_documents({'identifier': entity_id})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check existence of document {entity_id}: {e}")
            return False
    

    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Document]:
        """Find documents within a date range using MongoDB aggregation."""
        start_dt = self._to_datetime(start_date)
        end_dt = self._to_datetime(end_date)
        try:
            pipeline = [
                {
                    '$addFields': {
                        'parsed_date': {
                            '$dateFromString': {
                                'dateString': '$published_date',
                                'format': '%d/%m/%Y'
                            }
                        }
                    }
                },
                {
                    '$match': {
                        'parsed_date': {
                            '$gte': start_dt,
                            '$lte': end_dt
                        }
                    }
                },
                {
                    '$project': {
                        'parsed_date': 0  # Exclude the parsed_date field from results
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            documents = []
            for document_dict in cursor:
                document_dict.pop('_id', None)  # Remove MongoDB's _id field
                document_dict.pop('parsed_date', None)  # Also remove parsed_date if it exists
                documents.append(Document.from_dict(document_dict))
            
            return documents
        except Exception as e:
            logger.error(f"Failed to find documents by date range: {e}")
            return []
    
    def find_duplicates(self, field: str = 'identifier') -> List[Dict[str, Any]]:
        """Find documents with duplicate field values (default: identifier).
        
        Args:
            field: Field name to check for duplicates
            
        Returns:
            List of dictionaries containing:
            - field_value: The duplicate value
            - count: Number of duplicates
            - documents: List of duplicate documents
        """
        try:
            pipeline = [
                {
                    '$group': {
                        '_id': f'${field}',
                        'count': {'$sum': 1},
                        'documents': {'$push': '$$ROOT'}
                    }
                },
                {
                    '$match': {
                        'count': {'$gt': 1}
                    }
                }
            ]
            
            duplicates = []
            cursor = self.collection.aggregate(pipeline)
            
            for group in cursor:
                # Convert MongoDB documents to our Document model
                doc_list = []
                for doc in group['documents']:
                    doc.pop('_id', None)
                    doc_list.append(Document.from_dict(doc))
                
                duplicates.append({
                    'field_value': group['_id'],
                    'count': group['count'],
                    'documents': doc_list
                })
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to find duplicates by {field}: {e}")
            return []
    
    def __del__(self):
        """Cleanup on object destruction."""
        self._disconnect() 

    def _to_datetime(self, dt):
        if isinstance(dt, datetime):
            return dt
        if isinstance(dt, date):
            return datetime.combine(dt, time.min)
        return dt