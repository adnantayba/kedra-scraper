"""
Scrapy Item definition for compatibility.
For business logic, use workplace_relations.core.models.document.Document.
"""

import scrapy
import hashlib


class WorkplaceRelationsItem(scrapy.Item):
    identifier = scrapy.Field()
    description = scrapy.Field()
    published_date = scrapy.Field()
    link_to_doc = scrapy.Field()  # This is now the primary field
    partition_date = scrapy.Field()
    body = scrapy.Field()
    file_path = scrapy.Field()  # Path to stored file
    file_hash = scrapy.Field()  # Hash of the file content
    file_type = scrapy.Field()  # File extension (pdf, doc, html, etc.)

    # Internal fields (keep for Scrapy compatibility)
    depth = scrapy.Field()
    download_timeout = scrapy.Field()
    download_slot = scrapy.Field()
    download_latency = scrapy.Field()
