"""
Scrapy middlewares for workplace relations project.
Refactored to use centralized logging.
"""

from scrapy import signals
from workplace_relations.config import get_logger

logger = get_logger(__name__)


class WorkplaceRelationsSpiderMiddleware:
    """
    Spider middleware for workplace relations.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    async def process_start(self, start):
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        logger.info(f"Spider opened: {spider.name}")


class WorkplaceRelationsDownloaderMiddleware:
    """
    Downloader middleware for workplace relations.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        logger.info(f"Spider opened: {spider.name}")
