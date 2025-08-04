from workplace_relations.repository import scrapy_runner_resource

if __name__ == "__main__":
    runner = scrapy_runner_resource(None)
    stats = runner.run_spider(
        spider_name="workplace",
        start_date="2025-01-01",
        end_date="2025-03-01",
        bodies="labour court",
    )
    print("Spider stats:", stats)
