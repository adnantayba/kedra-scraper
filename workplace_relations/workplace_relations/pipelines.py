# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class WorkplaceRelationsPipeline:
    def process_item(self, item, spider):
        return item

    def open_spider(self, spider):
        # Connect to MongoDB (default URI, adjust as needed)
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["workplace_relations"]
        self.collection = self.db["decisions"]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.collection.insert_one(ItemAdapter(item).asdict())
        return item
