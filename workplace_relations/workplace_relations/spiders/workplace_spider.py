# workplace_relations/spiders/workplace_spider.py

import scrapy
import datetime
from urllib.parse import urlencode
from workplace_relations.utils import daterange_monthly


class WorkplaceSpider(scrapy.Spider):
    name = "workplace"
    allowed_domains = ["workplacerelations.ie"]
    start_url = "https://www.workplacerelations.ie/en/search/"

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    }

    def __init__(self, start_date=None, end_date=None, bodies=None, **kwargs):
        super().__init__(**kwargs)
        self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        # Parse bodies argument if provided (comma-separated list, case-insensitive)
        if bodies:
            self.selected_bodies = set(
                b.strip().lower() for b in bodies.split(",") if b.strip()
            )
            print(f"[DEBUG] Selected bodies: {self.selected_bodies}")
        else:
            self.selected_bodies = None

    def start_requests(self):
        # Scrape the available bodies from the filter table first
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse_bodies,
        )

    def parse_bodies(self, response):
        # Extract body IDs and names from the filter table on the left
        body_ids = response.xpath("//table[@id='CB2']//tr/td/input/@value").getall()
        body_names = response.xpath("//table[@id='CB2']//tr/td/label/text()").getall()
        bodies = list(zip(body_names, body_ids))
        for body_name, body_id in bodies:
            body_name_clean = body_name.strip().lower()
            # If filtering, skip bodies not in the selected list (case-insensitive)
            if self.selected_bodies and body_name_clean not in self.selected_bodies:
                continue
            print(f"[DEBUG] Crawling body: {body_name} (id: {body_id})")
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

            yield {
                "identifier": identifier.strip() if identifier else None,
                "description": description.strip() if description else None,
                "published_date": published_date.strip() if published_date else None,
                "link_to_doc": response.urljoin(link) if link else None,
                "partition_date": response.meta["partition_date"],
                "body": response.meta.get("body"),
            }

        # Follow pagination
        next_page = response.xpath("//a[@class='next']/@href").get()
        if next_page:
            yield response.follow(
                next_page, callback=self.parse_results, meta=response.meta
            )
