# repository.py (updated)
from dagster import Definitions
from workplace_relations.dagster_assets import (
    scrape_and_store_landing_zone,
    transform_landing_zone_documents,
)
from workplace_relations.resources import scrapy_runner_resource, mongo_resource

defs = Definitions(
    assets=[scrape_and_store_landing_zone, transform_landing_zone_documents],
    resources={
        "scrapy_runner": scrapy_runner_resource,
        "mongo": mongo_resource,
    },
)
