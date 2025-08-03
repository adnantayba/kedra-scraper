# pipelines.py
from itemadapter import ItemAdapter
from pymongo import MongoClient
from workplace_relations.utils.logger import get_logger

logger = get_logger(__name__)


class WorkplaceRelationsPipeline:

    def open_spider(self, spider):
        """Connect to MongoDB when spider opens"""
        try:
            self.client = MongoClient("mongodb://localhost:27017/")
            self.db = self.client["workplace_relations"]
            self.collection = self.db["decisions"]
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def close_spider(self, spider):
        """Close MongoDB connection when spider closes"""
        try:
            self.client.close()
            logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")

    def process_item(self, item, spider):
        """Store item in MongoDB"""
        try:
            item_dict = ItemAdapter(item).asdict()
            result = self.collection.insert_one(item_dict)
            logger.debug(f"Inserted document with ID: {result.inserted_id}")
            return item
        except Exception as e:
            logger.error(f"Failed to insert item into MongoDB: {e}")
            # Re-raise to allow handling by Scrapy
            raise
