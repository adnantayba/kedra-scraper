"""
Dagster assets for scraping and processing workplace relations documents.
Refactored to use the new architecture and separation of concerns.
"""

import os
from dagster import asset, Output, OpExecutionContext
from datetime import datetime
from workplace_relations.config.settings import settings
from workplace_relations.config.logging_config import get_logger
from workplace_relations.core.models.document import Document
from workplace_relations.core.services.document_service import DocumentService
from workplace_relations.repositories.mongo_repository import MongoRepository

logger = get_logger(__name__)

document_service = DocumentService()
landing_repo = MongoRepository(collection_name=settings.MONGO_LANDING_COLLECTION)
processed_repo = MongoRepository(collection_name=settings.MONGO_PROCESSED_COLLECTION)


@asset(required_resource_keys={"scrapy_runner"})
def scrape_and_store_landing_zone(context: OpExecutionContext):
    config = context.op_config or {}
    result = context.resources.scrapy_runner.run_spider(
        spider_name="workplace",
        start_date=config.get("start_date"),
        end_date=config.get("end_date"),
        bodies=config.get("bodies"),
    )

    # NEW: Get metrics from the spider run
    spider = context.resources.scrapy_runner.get_spider()
    if spider and hasattr(spider, 'monitor'):
        metrics = spider.monitor.finalize()
        context.log.info("Scraping Metrics:")
        for key, value in metrics.items():
            context.log.info(f"{key}: {value}")
            
    # Verify results (optional)
    count = landing_repo.count()

    return Output(
        value={"document_count": count, "status": "completed"},
        metadata={"documents_in_db": count, "storage_path": os.path.abspath(settings.STORAGE_BASE)},
    )


@asset(
    required_resource_keys={"mongo"},
    description="Transforms landing zone documents and stores them in processed location",
)
def transform_landing_zone_documents(context: OpExecutionContext):
    config = context.op_config or {}
    start_date = config.get("start_date")
    end_date = config.get("end_date")

    # Convert dates using DateUtils
    from workplace_relations.core.utils.date_utils import DateUtils
    query_start = DateUtils.parse_date(start_date)
    query_end = DateUtils.parse_date(end_date)

    context.log.info(f"Looking for documents between {query_start} and {query_end}")

    # Fetch documents from landing zone
    documents = landing_repo.find_by_date_range(query_start, query_end)
    context.log.info(f"Found {len(documents)} documents to process")
    
    # NEW: Handle duplicates before processing
    duplicate_report = document_service.handle_duplicates(documents)
    context.log.info(f"Duplicate handling result: {duplicate_report}")
    
    # Filter out duplicates (those marked with metadata)
    documents = [doc for doc in documents if not doc.metadata.get('duplicate_of')]
    context.log.info(f"Proceeding with {len(documents)} after duplicate removal")

    processed_docs = []

    for doc in documents:
        try:
            # Process document using DocumentService
            processed_doc = document_service.process_document(doc)
            if processed_doc:
                # Store processed document metadata in processed collection
                processed_repo.create(processed_doc)
                processed_docs.append(processed_doc)
            else:
                context.log.warning(f"Failed to process document: {doc.identifier}")
        except Exception as e:
            context.log.error(f"Failed to process document {getattr(doc, 'identifier', None)}: {str(e)}")
            continue

    return Output(
        value={
            "processed_count": len(processed_docs),
            "start_date": start_date,
            "end_date": end_date,
        },
        metadata={
            "processed_documents": len(processed_docs),
            "processed_storage_path": os.path.abspath(settings.PROCESSED_STORAGE_BASE),
            "mongo_collection": settings.MONGO_PROCESSED_COLLECTION,
        },
    )
