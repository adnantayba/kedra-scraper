# spiders/workplace_spider.py
import scrapy
import datetime
from urllib.parse import urlencode
from workplace_relations.utils import daterange_monthly, get_logger
from workplace_relations.items import WorkplaceRelationsItem


logger = get_logger(__name__)


class WorkplaceSpider(scrapy.Spider):
    name = "workplace"
    allowed_domains = ["workplacerelations.ie"]
    start_url = "https://www.workplacerelations.ie/en/search/"
    MAX_DOCUMENTS = 1000  # Limit to 1000 documents

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
        self.document_count = 0

        try:
            self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            self.storage_base = storage_base
            logger.info(
                f"Initialized spider with start_date={start_date}, end_date={end_date}"
            )

            if bodies:
                self.selected_bodies = set(
                    b.strip().lower() for b in bodies.split(",") if b.strip()
                )
                logger.info(f"Filtering bodies: {', '.join(self.selected_bodies)}")
            else:
                self.selected_bodies = None
                logger.info("No body filter applied")

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid date format: {e}")
            raise scrapy.exceptions.CloseSpider("Invalid date parameters") from e

    def start_requests(self):
        """Start by fetching the list of available bodies"""
        logger.info("Starting requests for body list")
        yield scrapy.Request(
            url=self.start_url, callback=self.parse_bodies, errback=self.handle_error
        )

    def parse_bodies(self, response):
        """Parse the list of decision-making bodies"""
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

            for range_start, range_end in daterange_monthly(
                self.start_date, self.end_date
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

    def parse_results(self, response):
        """Parse search results page and yield items directly"""
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

            # Create item directly from metadata
            yield WorkplaceRelationsItem(
                identifier=identifier.strip() if identifier else None,
                description=item.xpath("./p[@class='description']/@title").get(),
                published_date=item.xpath(".//span[@class='date']/text()").get(),
                partition_date=response.meta["partition_date"],
                body=response.meta["body"],
                link_to_doc=abs_url,
            )

        # Pagination handling
        next_page = response.xpath("//a[@class='next']/@href").get()
        if next_page and self.document_count < self.MAX_DOCUMENTS:
            logger.debug("Following pagination")
            yield response.follow(
                next_page, callback=self.parse_results, meta=response.meta
            )

    def handle_error(self, failure):
        """Handle request errors"""
        logger.error(f"Request failed: {failure.value}")
