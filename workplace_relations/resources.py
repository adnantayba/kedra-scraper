from dagster import resource
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from workplace_relations.spiders.workplace_spider import WorkplaceSpider
from scrapy import signals


from datetime import datetime
import json


@resource
def scrapy_runner_resource(init_context):
    class ScrapyRunner:
        def run_spider(self, spider_name, **kwargs):
            # Ensure Scrapy uses all pipelines
            process = CrawlerProcess(get_project_settings())
            process.crawl(spider_name, **kwargs)
            process.start()  # This will run all pipelines

            # Return simple success status
            return {"status": "completed", "spider": spider_name}

    return ScrapyRunner()
