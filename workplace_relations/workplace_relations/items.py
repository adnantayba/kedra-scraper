# items.py
import scrapy


class WorkplaceRelationsItem(scrapy.Item):
    identifier = scrapy.Field()
    description = scrapy.Field()
    published_date = scrapy.Field()
    link_to_doc = scrapy.Field()
    partition_date = scrapy.Field()
    body = scrapy.Field()
    file_path = scrapy.Field()
    file_hash = scrapy.Field()

    # Add Scrapy's internal fields to prevent errors
    depth = scrapy.Field()
    download_timeout = scrapy.Field()
    download_slot = scrapy.Field()
    download_latency = scrapy.Field()
