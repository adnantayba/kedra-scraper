"""
Dagster resources for Scrapy and MongoDB.
"""

from dagster import resource
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient
from workplace_relations.config.settings import settings

@resource
def scrapy_runner_resource(init_context):
    """Dagster resource for running Scrapy spiders."""
    class ScrapyRunner:
        def run_spider(self, spider_name, **kwargs):
            process = CrawlerProcess(get_project_settings())
            process.crawl(spider_name, **kwargs)
            process.start()
            return {"status": "completed", "spider": spider_name}
    return ScrapyRunner()

    
@resource
def mongo_resource(init_context):
    """Dagster resource for MongoDB client using centralized config."""
    return MongoClient(settings.MONGO_URI)
