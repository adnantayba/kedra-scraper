"""
Scrapy spider for workplace relations document crawling.
Uses centralized config, logging, and utility modules.
"""

import scrapy
from urllib.parse import urlencode, urlparse
from typing import Optional
from workplace_relations.core.models.spider_config import SpiderConfig
from workplace_relations.core.utils.date_utils import DateUtils
from workplace_relations.core.utils.file_utils import FileUtils
from workplace_relations.items import WorkplaceRelationsItem
from workplace_relations.config.settings import settings
from workplace_relations.config.logging_config import get_logger
from workplace_relations.core.utils.monitoring import ScraperMonitor

logger = get_logger(__name__)

class WorkplaceSpider(scrapy.Spider):
    """
    Spider for crawling workplace relations documents.
    """
    name = "workplace"
    allowed_domains = settings.ALLOWED_DOMAINS
    start_url = settings.START_URL
    MAX_DOCUMENTS = settings.MAX_DOCUMENTS

    custom_settings = {
        "USER_AGENT": settings.USER_AGENT,
    }

    def __init__(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        bodies: Optional[str] = None,
        storage_base: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.document_count = 0
        self.monitor = ScraperMonitor()
        try:
            self.config = SpiderConfig(
                start_date=DateUtils.parse_date(start_date),
                end_date=DateUtils.parse_date(end_date),
                bodies=bodies.split(",") if bodies else None,
                storage_base=storage_base or settings.STORAGE_BASE
            )
            logger.info(
                f"Initialized spider with start_date={start_date}, end_date={end_date}"
            )
            self.selected_bodies = self.config.get_body_filter()
            if self.selected_bodies:
                logger.info(f"Filtering bodies: {', '.join(self.selected_bodies)}")
            else:
                logger.info("No body filter applied")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid date format: {e}")
            raise scrapy.exceptions.CloseSpider("Invalid date parameters") from e

    def start_requests(self):
        """Start by fetching the list of available bodies."""
        logger.info("Starting requests for body list")
        yield scrapy.Request(
            url=self.start_url, callback=self.parse_bodies, errback=self.handle_error
        )

    def parse_bodies(self, response: scrapy.http.Response):
        """Parse the list of decision-making bodies."""
        if response.status != 200:
            logger.error(f"Failed to fetch body list: HTTP {response.status}")
            return

        body_ids = response.xpath("//table[@id='CB2']//tr/td/input/@value").getall()
        body_names = response.xpath("//table[@id='CB2']//tr/td/label/text()").getall()
        bodies = list(zip(body_names, body_ids))

        logger.info(f"Found {len(bodies)} bodies for processing")

        for body_name, body_id in bodies:
            body_name_clean = body_name.strip().lower()
            if self.selected_bodies and body_name_clean not in self.selected_bodies:
                continue

            logger.debug(f"Processing body: {body_name} (ID: {body_id})")

            for range_start, range_end in DateUtils.get_monthly_ranges(
                self.config.start_date, self.config.end_date
            ):
                if self.document_count >= self.MAX_DOCUMENTS:
                    logger.info(
                        f"Reached document limit of {self.MAX_DOCUMENTS}, stopping"
                    )
                    return

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
                    errback=self.handle_error,
                )

    def parse_results(self, response: scrapy.http.Response):
        """Parse search results page and yield items directly."""
        self.monitor.update_metrics()
        if response.status != 200:
            logger.warning(f"Failed search results page: HTTP {response.status}")
            return

        items = response.xpath("//div[@class='item-list search-list']//li")
        logger.debug(f"Found {len(items)} items on page {response.url}")

        for item in items:
            if self.document_count >= self.MAX_DOCUMENTS:
                logger.info(f"Reached document limit of {self.MAX_DOCUMENTS}, stopping")
                return

            identifier = item.xpath(".//h2/@title").get()
            link = item.xpath(".//div[contains(@class, 'link')]/a/@href").get()

            if not link:
                logger.debug("Skipping item without link")
                continue

            abs_url = response.urljoin(link)
            self.document_count += 1

            # Determine file type from URL
            parsed_url = urlparse(abs_url)
            path = parsed_url.path.lower()
            if path.endswith(".pdf"):
                file_type = "pdf"
            elif path.endswith(".doc") or path.endswith(".docx"):
                file_type = "docx" if path.endswith(".docx") else "doc"
            else:
                file_type = "html"

            # Yield Scrapy Item (for pipeline compatibility)
            yield WorkplaceRelationsItem(
                identifier=identifier.strip() if identifier else None,
                description=item.xpath("./p[@class='description']/@title").get(),
                published_date=item.xpath(".//span[@class='date']/text()").get(),
                partition_date=response.meta["partition_date"],
                body=response.meta["body"],
                link_to_doc=abs_url,
                file_type=file_type,
            )

        # Pagination
        next_page = response.xpath("//a[@class='next']/@href").get()
        if next_page and self.document_count < self.MAX_DOCUMENTS:
            logger.debug("Following pagination")
            yield response.follow(
                next_page, callback=self.parse_results, meta=response.meta
            )

    def closed(self, reason):
        """Called when the spider closes."""
        metrics = self.monitor.finalize()
        logger.info(f"Spider closed. Reason: {reason}")
        logger.info(f"Final metrics: {metrics}")


    def handle_error(self, failure):
        """Handle request errors."""
        logger.error(f"Request failed: {failure.value}")
