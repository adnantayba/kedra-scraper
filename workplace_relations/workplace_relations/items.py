import scrapy


class WorkplaceRelationsItem(scrapy.Item):
    identifier = scrapy.Field()
    description = scrapy.Field()
    published_date = scrapy.Field()
    link_to_doc = scrapy.Field()  # This is now the primary field
    partition_date = scrapy.Field()
    body = scrapy.Field()

    # Internal fields (keep for Scrapy compatibility)
    depth = scrapy.Field()
    download_timeout = scrapy.Field()
    download_slot = scrapy.Field()
    download_latency = scrapy.Field()
