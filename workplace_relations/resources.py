# resources.py (updated)
from dagster import resource
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient


@resource
def scrapy_runner_resource(init_context):
    class ScrapyRunner:
        def run_spider(self, spider_name, **kwargs):
            process = CrawlerProcess(get_project_settings())
            process.crawl(spider_name, **kwargs)
            process.start()
            return {"status": "completed", "spider": spider_name}

    return ScrapyRunner()


@resource
def mongo_resource(init_context):
    return MongoClient("mongodb://localhost:27017")
