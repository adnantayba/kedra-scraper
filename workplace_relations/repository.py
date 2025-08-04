from dagster import Definitions
from workplace_relations.dagster_assets import (
    scrape_and_store_landing_zone,
    process_documents_from_landing_zone,
)
from workplace_relations.jobs import process_documents_job
from workplace_relations.resources import scrapy_runner_resource

defs = Definitions(
    assets=[scrape_and_store_landing_zone, process_documents_from_landing_zone],
    jobs=[process_documents_job],
    resources={"scrapy_runner": scrapy_runner_resource},
)
