# workplace_spider.py
import scrapy
import datetime
import os
import re
import hashlib
from urllib.parse import urlencode
from workplace_relations.utils import daterange_monthly
from workplace_relations.items import WorkplaceRelationsItem  # Import the Item class


class WorkplaceSpider(scrapy.Spider):
    name = "workplace"
    allowed_domains = ["workplacerelations.ie"]
    start_url = "https://www.workplacerelations.ie/en/search/"

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    }

    def __init__(
        self,
        start_date=None,
        end_date=None,
        bodies=None,
        storage_base="storage",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        self.storage_base = storage_base  # Base directory for storing files

        if bodies:
            self.selected_bodies = set(
                b.strip().lower() for b in bodies.split(",") if b.strip()
            )
        else:
            self.selected_bodies = None

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse_bodies,
        )

    def parse_bodies(self, response):
        body_ids = response.xpath("//table[@id='CB2']//tr/td/input/@value").getall()
        body_names = response.xpath("//table[@id='CB2']//tr/td/label/text()").getall()
        bodies = list(zip(body_names, body_ids))

        for body_name, body_id in bodies:
            body_name_clean = body_name.strip().lower()
            if self.selected_bodies and body_name_clean not in self.selected_bodies:
                continue

            for range_start, range_end in daterange_monthly(
                self.start_date, self.end_date
            ):
                params = {
                    "decisions": 1,
                    "from": range_start.strftime("%d/%m/%Y"),
                    "to": range_end.strftime("%d/%m/%Y"),
                    "Body": body_id,
                }
                url = f"{self.start_url}?{urlencode(params)}"
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_results,
                    meta={
                        "partition_date": range_start.strftime("%Y-%m"),
                        "body": body_name,
                    },
                )

    def parse_results(self, response):
        for item in response.xpath("//div[@class='item-list search-list']//li"):
            identifier = item.xpath(".//h2/@title").get()
            description = item.xpath("./p[@class='description']/@title").get()
            published_date = item.xpath(".//span[@class='date']/text()").get()
            link = item.xpath(".//div[contains(@class, 'link')]/a/@href").get()

            if not link:
                continue

            abs_url = response.urljoin(link)
            meta = {
                "identifier": identifier.strip() if identifier else None,
                "description": description.strip() if description else None,
                "published_date": published_date.strip() if published_date else None,
                "partition_date": response.meta["partition_date"],
                "body": response.meta["body"],
                "link_to_doc": abs_url,
            }

            # Yield request to download document
            yield scrapy.Request(
                url=abs_url,
                callback=self.parse_document,
                meta=meta,
            )

        # Pagination handling remains the same
        next_page = response.xpath("//a[@class='next']/@href").get()
        if next_page:
            yield response.follow(
                next_page, callback=self.parse_results, meta=response.meta
            )

    # workplace_spider.py (update parse_document method only)
    def parse_document(self, response):
        """Handle document download and metadata processing"""
        item = WorkplaceRelationsItem()

        # Only load fields that exist in the item class
        for key, value in response.meta.items():
            if key in item.fields:
                item[key] = value

        # Determine file extension
        content_type = response.headers.get("Content-Type", b"").decode().lower()
        url = response.url.lower()

        if "pdf" in content_type or url.endswith(".pdf"):
            ext = "pdf"
        elif "msword" in content_type or "wordprocessingml" in content_type:
            ext = "docx"
        elif url.endswith(".docx"):
            ext = "docx"
        elif url.endswith(".doc"):
            ext = "doc"
        elif "html" in content_type or url.endswith((".html", ".htm")):
            ext = "html"
        else:
            ext = "bin"  # Fallback extension

        # Create safe filename and directory path
        safe_identifier = re.sub(r"[^\w]", "_", item["identifier"] or "document")[:50]
        safe_body = re.sub(r"[^\w]", "_", item["body"])
        dir_path = os.path.join(self.storage_base, safe_body, item["partition_date"])
        os.makedirs(dir_path, exist_ok=True)

        filename = f"{safe_identifier}.{ext}"
        file_path = os.path.join(dir_path, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(response.body)

        # Calculate file hash
        file_hash = hashlib.md5(response.body).hexdigest()

        # Add file metadata to item
        item["file_path"] = file_path
        item["file_hash"] = file_hash

        yield item
