# jobs.py
from dagster import job
from workplace_relations.resources import scrapy_runner_resource
from workplace_relations.dagster_assets import (
    scrape_and_store_landing_zone,
    process_documents_from_landing_zone,
)


@job(resource_defs={"scrapy_runner": scrapy_runner_resource})
def process_documents_job():
    process_documents_from_landing_zone(scrape_and_store_landing_zone())
